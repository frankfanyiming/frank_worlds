import * as THREE from 'three';

export type SignalColor='green'|'amber'|'red';
export function signalPhase(time:number):{EW:SignalColor;NS:SignalColor}{
 const t=((time%38)+38)%38;
 if(t<16)return{EW:'green',NS:'red'};
 if(t<19)return{EW:'amber',NS:'red'};
 if(t<21)return{EW:'red',NS:'red'};
 if(t<33)return{EW:'red',NS:'green'};
 if(t<36)return{EW:'red',NS:'amber'};
 return{EW:'red',NS:'red'};
}
type Car={root:THREE.Group;wheels:THREE.Object3D[];direction:number;lane:number;speed:number;length:number;width:number;wheelRadius:number;distance:number;waiting:string;parked:boolean};

export class TownTraffic {
 cars:Car[]=[];time=0;signals:{material:THREE.MeshStandardMaterial;axis:'EW'|'NS';color:SignalColor}[]=[];
 constructor(public world:THREE.Group){
  const seen=new Set<THREE.Material>();world.traverse(o=>{if(o instanceof THREE.Mesh){for(const m of Array.isArray(o.material)?o.material:[o.material]){
   const match=m.name.match(/^Signal_(EW|NS)_(red|amber|green)/);if(match&&m instanceof THREE.MeshStandardMaterial&&!seen.has(m)){seen.add(m);this.signals.push({material:m,axis:match[1] as 'EW'|'NS',color:match[2] as SignalColor});}
  }}});
 }
 addAsset(source:THREE.Group,type:'car'|'truck'){
  const add=(x:number,y:number,direction:number,parked:boolean)=>{
   const root=new THREE.Group();root.name=(parked?'parked_':'moving_')+type;
   const asset=source.clone(true);root.add(asset);this.world.add(root);
   // The body is an obliquely rotated merged mesh. Transforming its local AABB
   // includes empty space below the tyres; measure the actual vertices instead.
   const bounds=new THREE.Box3().setFromObject(asset,true),size=bounds.getSize(new THREE.Vector3());
   // Authored in metres, front +Z after Blender glTF conversion.
   asset.position.y-=bounds.min.y;root.position.set(x,parked?.054:.133,-y);root.rotation.y=direction*Math.PI/2;
   const wheels:THREE.Object3D[]=[];asset.traverse(o=>{if(/^Wheel_/.test(o.name)&&!/^Wheel_/.test(o.parent?.name??''))wheels.push(o);});
   this.cars.push({root,wheels,direction,lane:y,speed:0,length:size.z,width:size.x,wheelRadius:.26,distance:0,waiting:'',parked});
  };
  if(type==='car'){add(-36,-6.86,1,false);add(-36.0,-23.8,-1,true);}
  else{add(35,-9.14,-1,false);add(-32.0,-3.65,1,true);}
 }
 update(dt:number,player:THREE.Vector3,residents:THREE.Vector3[]=[]){
  this.time+=dt;const phase=signalPhase(this.time);
  for(const s of this.signals)s.material.emissiveIntensity=phase[s.axis]===s.color?3.2:.015;
  const pedestrians=[player,...residents];
  for(const car of this.cars){
   if(car.parked)continue;
   const d=car.direction,x=car.root.position.x,front=x+d*car.length/2;
   let clearance=Infinity;car.waiting='';
   const stop=d>0?-5.8:7.8,toLine=(stop-front)*d;
   if(phase.EW!=='green'&&toLine>=-.10){clearance=Math.max(0,toLine-.22);car.waiting='signal';}
   for(const p of pedestrians){
    const ahead=(p.x-front)*d;
    if(Math.abs(p.y-.133)<1.6&&Math.abs(-p.z-car.lane)<car.width/2+.45&&ahead>-car.length-.4&&ahead<clearance+.75){clearance=Math.max(0,ahead-.75);car.waiting='pedestrian';}
   }
   const cruise=car.root.name.includes('truck')?1.85:2.3;
   const target=Math.min(cruise,Math.sqrt(2*1.8*Math.max(0,clearance-.12)));
   const acceleration=target>car.speed?.65:2.4;
   car.speed+=THREE.MathUtils.clamp(target-car.speed,-acceleration*dt,acceleration*dt);
   const step=Math.min(car.speed*dt,clearance);car.root.position.x+=step*d;car.distance+=step;
   if(step<car.speed*dt)car.speed=0;
   for(const wheel of car.wheels)wheel.rotation.x+=step/car.wheelRadius;
   if(Math.abs(car.root.position.x)>47){car.root.position.x=-d*47;car.speed=0;}
   car.root.visible=Math.abs(car.root.position.x)<43;
  }
 }
 collides(x:number,y:number,z:number,radius=.19){return z<1.7&&this.cars.some(c=>c.root.visible&&Math.abs(x-c.root.position.x)<c.length/2+radius&&Math.abs(y+c.root.position.z)<c.width/2+radius);}
 snapshot(){return{leftHandTraffic:true,phase:signalPhase(this.time),signalHeads:4,signalMaterials:this.signals.length,cars:this.cars.map(c=>({name:c.root.name,parked:c.parked,visible:c.root.visible,position:{x:c.root.position.x,y:-c.root.position.z,height:c.root.position.y},dimensions:{length:c.length,width:c.width},speed:c.speed,distanceTravelled:c.distance,waiting:c.waiting,wheelPivots:c.wheels.length}))};}
}
