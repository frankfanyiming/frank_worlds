import * as THREE from 'three';
import {clone} from 'three/addons/utils/SkeletonUtils.js';
import type {GLTF} from 'three/addons/loaders/GLTFLoader.js';
import {ROUTINES,findRoute,type Point,type Routine} from './life';
import {groundHeight,type Collider,type GroundSurface} from './world';
type Resident={routine:Routine;root:THREE.Object3D;stop:number;wait:number;path:Point[];blocked:number;travel:number};
type Animal={id:string;root:THREE.Object3D;home:Point;target:Point;start:Point;phase:number;wait:number;flight:boolean;kind:'cat'|'bird';mixer:THREE.AnimationMixer;actions:Map<string,THREE.AnimationAction>;current:string;route:Point[]};
const UP=new THREE.Vector3(0,1,0);
export class TownEcosystem {
 obstacle:(x:number,y:number,z:number,radius:number)=>boolean=()=>false;
 residents:Resident[]=[];animals:Animal[]=[];held=new Set<string>();companion:string|null=null;companionRepath=0;
 constructor(public colliders:Collider[],public surfaces:GroundSurface[],public play:(id:string,clip:string)=>void){}
 addResidents(world:THREE.Group){
  this.residents=ROUTINES.flatMap((routine,i)=>{const root=world.getObjectByName('actor_'+routine.id);if(!root)return [];return[{routine,root,stop:0,wait:1.1+i*.73,path:[],blocked:0,travel:0}];});
 }
 addFauna(gltf:GLTF,kind:'cat'|'bird',world:THREE.Group,variant=0){
  const positions=kind==='cat'?[{x:-18.2,y:-3.1}]:variant?[{x:20.5,y:4.8},{x:-16.8,y:-7.6},{x:-7.8,y:32.0}]:[{x:18.5,y:3.8},{x:21,y:.8},{x:-14.5,y:-7.3}];
  for(const [i,home] of positions.entries()){
   const root=clone(gltf.scene);root.name=`fauna_${kind}_${variant}_${i}`;root.position.set(home.x,groundHeight(home.x,home.y,.1,this.surfaces),-home.y);world.add(root);
   root.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true;if(o instanceof THREE.SkinnedMesh)o.frustumCulled=false;}});
   const mixer=new THREE.AnimationMixer(root),actions=new Map(gltf.animations.map(clip=>[clip.name,mixer.clipAction(clip)]));
   const a:Animal={id:root.name,root,home,target:{...home},start:{...home},phase:0,wait:2+i*2.3+variant*1.4,flight:false,kind,mixer,actions,current:'',route:[]};this.animals.push(a);this.animalClip(a,'Idle');mixer.update(i*.25);
  }
 }
 animalClip(a:Animal,name:string){if(a.current===name)return;const next=a.actions.get(name);if(!next)return;const old=a.actions.get(a.current);next.reset().play();next.timeScale=name==='Fly'?1.5:1;if(old)old.crossFadeTo(next,.16,false);a.current=name;}
 face(root:THREE.Object3D,dx:number,dy:number,dt:number){if(Math.hypot(dx,dy)<.0001)return;const q=new THREE.Quaternion().setFromAxisAngle(UP,Math.atan2(dx,-dy));root.quaternion.slerp(q,Math.min(1,dt*6));}
 actorPosition(id:string){return this.residents.find(r=>r.routine.id===id)?.root.position;}
 update(dt:number,time:number,player:THREE.Vector3,dialogue:string|null){
  this.companionRepath-=dt;
  for(const r of this.residents){
   if(this.held.has(r.routine.id))continue;
   const here={x:r.root.position.x,y:-r.root.position.z},distance=Math.hypot(player.x-here.x,player.z+here.y);
   if(this.companion===r.routine.id){
    if(distance<1.35){this.play(r.routine.id,'Idle');this.face(r.root,player.x-here.x,-player.z-here.y,dt);continue;}
    if(this.companionRepath<=0){this.companionRepath=.8;r.path=findRoute(here,{x:player.x,y:-player.z},r.routine,this.colliders,this.surfaces);r.wait=0;}
    if(!r.path.length){this.play(r.routine.id,'Idle');continue;}
   }
   if(dialogue===r.routine.id){this.face(r.root,player.x-here.x,-player.z-here.y,dt);r.wait=Math.max(r.wait,2);continue;}
   if(r.wait>0){r.wait-=dt;this.play(r.routine.id,'Idle');if(distance<2.7&&Math.abs(player.y-r.root.position.y)<.7)this.face(r.root,player.x-here.x,-player.z-here.y,dt*.5);continue;}
   if(!r.path.length){r.stop=(r.stop+1)%r.routine.stops.length;r.path=findRoute(here,r.routine.stops[r.stop],r.routine,this.colliders,this.surfaces);if(!r.path.length){r.wait=1.2;continue;}}
   const target=r.path[0],dx=target.x-here.x,dy=target.y-here.y,dist=Math.hypot(dx,dy),step=Math.min(dist,(this.companion===r.routine.id?1.15:r.routine.speed)*dt);
   if(dist<.06){r.path.shift();if(!r.path.length){r.wait=r.routine.wait+2*(.5+.5*Math.sin(time+here.x));this.play(r.routine.id,'Idle');}continue;}
   const nx=here.x+dx/dist*step,ny=here.y+dy/dist*step;
   const occupied=this.obstacle(nx,ny,r.root.position.y,r.routine.id==='doraemon'?.55:.32)||(Math.abs(player.y-r.root.position.y)<.65&&Math.hypot(nx-player.x,ny+player.z)<.65)||this.residents.some(o=>o!==r&&Math.abs(o.root.position.y-r.root.position.y)<.6&&Math.hypot(nx-o.root.position.x,ny+o.root.position.z)<.48);
   if(occupied){this.play(r.routine.id,'Idle');r.blocked+=dt;if(r.blocked>3){r.path=[];r.wait=1.5;r.blocked=0;}continue;}
   r.blocked=0;r.root.position.set(nx,groundHeight(nx,ny,.48,this.surfaces),-ny);this.face(r.root,dx,dy,dt);this.play(r.routine.id,'Walk');r.travel+=step;
  }
  for(const a of this.animals){
   const here={x:a.root.position.x,y:-a.root.position.z};
   if(a.kind==='cat'){
    if(a.wait>0){a.wait-=dt;this.animalClip(a,'Idle');}
    else{
     if(!a.route.length){const catRoutine:Routine={id:'cat',speed:.30,wait:5,zone:'outside',stops:[]};a.target={x:-18.2+Math.sin(time*.1)*.25,y:-2.8+(.5+.5*Math.sin(time*.15))*6};a.route=findRoute(here,a.target,catRoutine,this.colliders,this.surfaces);if(!a.route.length)a.wait=3;}
     const p=a.route[0];if(p){const dx=p.x-here.x,dy=p.y-here.y,d=Math.hypot(dx,dy),step=Math.min(d,.30*dt);
      if(Math.hypot(player.x-here.x,player.z+here.y)<.7){a.wait=2;this.animalClip(a,'Idle');}
      else if(d<.04){a.route.shift();if(!a.route.length)a.wait=6;}
      else{a.root.position.set(here.x+dx/d*step,groundHeight(here.x,here.y,.1,this.surfaces),-here.y-dy/d*step);this.face(a.root,dx,dy,dt);this.animalClip(a,'Walk');}
     }
    }
   }else{
    const startled=!a.flight&&Math.hypot(player.x-here.x,player.z+here.y)<1.45&&Math.abs(player.y-a.root.position.y)<1;
    if(startled||(a.wait<=0&&a.phase===0)){
     a.flight=startled||Math.sin(time+a.home.x)>.1;a.start=here;
     const angle=time*.43+a.home.x,length=a.flight?2.8:.22;
     a.target={x:a.home.x+Math.cos(angle)*length,y:a.home.y+Math.sin(angle)*length};a.phase=.001;this.animalClip(a,a.flight?'Fly':'Hop');
    }
    if(a.phase>0){
     const duration=a.flight?2.4:.52;a.phase=Math.min(1,a.phase+dt/duration);const t=a.phase,e=t*t*(3-2*t),x=THREE.MathUtils.lerp(a.start.x,a.target.x,e),y=THREE.MathUtils.lerp(a.start.y,a.target.y,e),base=groundHeight(x,y,.1,this.surfaces);
     const startHeight=groundHeight(a.start.x,a.start.y,.1,this.surfaces),endHeight=groundHeight(a.target.x,a.target.y,.1,this.surfaces);
     a.root.position.set(x,a.flight?THREE.MathUtils.lerp(startHeight,endHeight,e)+Math.sin(t*Math.PI)*2.0:base,-y);this.face(a.root,a.target.x-a.start.x,a.target.y-a.start.y,dt);
     if(t===1){a.phase=0;a.wait=3+(Math.sin(time)*.5+.5)*8;a.flight=false;this.animalClip(a,'Idle');}
    }else a.wait-=dt;
   }
   a.mixer.update(dt);
  }
 }
 snapshot(){return {residents:this.residents.map(r=>({id:r.routine.id,x:+r.root.position.x.toFixed(3),y:+(-r.root.position.z).toFixed(3),moving:r.path.length>0&&r.wait<=0,distanceWalked:+r.travel.toFixed(2)})),animals:this.animals.map(a=>({id:a.id,action:a.current,x:+a.root.position.x.toFixed(2),y:+(-a.root.position.z).toFixed(2)}))};}
 dispose(){for(const a of this.animals){a.mixer.stopAllAction();a.mixer.uncacheRoot(a.root);}}
}
