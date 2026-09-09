import {assetPath} from './asset-path';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { PLACES, ACTORS, TOWN_BOUNDS, inTown, setExpansionTerrain, type Heightfield, type WalkMesh, collides, groundHeight, insideHouse, HOUSE, type Collider, type GroundSurface, type ViewMode, type PlaceId, type Actor } from './world';
import {TownAtmosphere} from './atmosphere';
import {TownEcosystem} from './ecosystem';
import {TownSky} from './sky';
import {TownTraffic} from './traffic';
import {TownWater} from './water';
import {TownAdventure} from './adventure';
import {TownWeather} from './weather';
import {TownSound} from './sound';
import {TownInteriorLight} from './lighting';
type CharacterMotion={mixer:THREE.AnimationMixer;actions:Map<string,THREE.AnimationAction>;current:string;oneShotUntil:number};
export type TownState={adventure?:ReturnType<TownAdventure['snapshot']>;weather?:ReturnType<TownWeather['snapshot']>;audio?:ReturnType<TownSound['snapshot']>;ready:boolean;progress:number;mode:ViewMode;inside:boolean;floor:number;cutaway:boolean;place:PlaceId;position:{x:number;y:number};near:string;actor:Actor|null;sunset:boolean;error:string|null};
const START:TownState={ready:false,progress:0,mode:'orbit',inside:false,floor:0,cutaway:false,place:'home',position:{x:-9.6,y:-6.3},near:'',actor:null,sunset:false,error:null};
export class TownEngine {
 water=new TownWater(); atmosphere=new TownAtmosphere(); sky:TownSky; traffic?:TownTraffic; ecosystem?:TownEcosystem; shaderErrors:string[]=[];
 interiorLight:TownInteriorLight;adventure:TownAdventure;weather:TownWeather;sound=new TownSound();
 state={...START}; scene=new THREE.Scene(); camera=new THREE.PerspectiveCamera(38,1,.08,260);
 renderer:THREE.WebGLRenderer; composer:EffectComposer; ao:SSAOPass; sun:THREE.DirectionalLight; environmentTarget:THREE.WebGLRenderTarget;
 world?:THREE.Group; player=new THREE.Group(); playerPosition=new THREE.Vector3(-9.6,.23,6.3);
 target=new THREE.Vector3(-8,1,-2); targetGoal=this.target.clone(); azimuth=.63; distance=41; yaw=0; pitch=0;
 groundSurfaces:GroundSurface[]=[]; assetRevision=0; colliders:Collider[]=[]; keys=new Set<string>(); pointer={down:false,x:0,y:0,moved:0}; paused=false; touch={x:0,y:0};
 clock=new THREE.Clock();frameSeconds=1/60;shadowTimer=0; raf=0; elapsed=0; sendAt=0; cameraTarget=new THREE.Vector3(); walkTarget:THREE.Vector3|null=null;
 ring:THREE.Mesh; resizeObserver:ResizeObserver; quality=true; disposers:(()=>void)[]=[]; dead=false; dialogueIndex=0; motions=new Map<string,CharacterMotion>();
 constructor(public host:HTMLDivElement,public publish:(s:TownState)=>void){
  this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance',preserveDrawingBuffer:true});
  const r=this.renderer;r.info.autoReset=false;r.setPixelRatio(Math.min(window.devicePixelRatio,1.65));r.shadowMap.enabled=true;r.shadowMap.type=THREE.PCFSoftShadowMap;r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=1.05;r.outputColorSpace=THREE.SRGBColorSpace;
  r.debug.onShaderError=(gl,program,vertex,fragment)=>{this.shaderErrors.push([gl.getProgramInfoLog(program),gl.getShaderInfoLog(vertex),gl.getShaderInfoLog(fragment)].filter(Boolean).join('\n'));};
  r.domElement.tabIndex=0;r.domElement.setAttribute('aria-label','可探索的三维哆啦A梦小镇。WASD 移动，V 切换视角，E 互动。');host.appendChild(r.domElement);
  this.scene.background=new THREE.Color('#b9d5d6');this.scene.fog=new THREE.FogExp2('#c3d9d6',.0035);this.sky=new TownSky(this.scene);
  const hemi=new THREE.HemisphereLight('#d9eeff','#a59775',1.4);this.scene.add(hemi);
  const pmrem=new THREE.PMREMGenerator(r),environment=new RoomEnvironment();this.environmentTarget=pmrem.fromScene(environment,.06);this.scene.environment=this.environmentTarget.texture;this.scene.environmentIntensity=.35;environment.dispose();pmrem.dispose();
  this.sun=new THREE.DirectionalLight('#ffe5b6',3.0);this.sun.position.set(-28,48,35);this.sun.castShadow=true;
  this.sun.shadow.mapSize.set(4096,4096);Object.assign(this.sun.shadow.camera,{left:-22,right:22,top:22,bottom:-22,near:1,far:130});this.sun.shadow.bias=-.00008;this.sun.shadow.normalBias=.009;this.sun.shadow.radius=2;this.sun.shadow.autoUpdate=false;this.sun.shadow.needsUpdate=true;this.scene.add(this.sun,this.sun.target);
  this.interiorLight=new TownInteriorLight(this.scene);
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(1200,1200),new THREE.MeshStandardMaterial({color:'#bfd0bd',roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.y=-1.60;ground.receiveShadow=true;this.scene.add(ground);
  this.composer=new EffectComposer(r);this.composer.addPass(new RenderPass(this.scene,this.camera));this.ao=new SSAOPass(this.scene,this.camera,host.clientWidth,host.clientHeight);this.ao.kernelRadius=.72;this.ao.minDistance=.003;this.ao.maxDistance=.11;this.composer.addPass(this.ao);this.composer.addPass(new OutputPass());
  this.ring=new THREE.Mesh(new THREE.RingGeometry(.30,.38,40),new THREE.MeshBasicMaterial({color:'#fce7aa',transparent:true,opacity:.85,side:THREE.DoubleSide,depthWrite:false}));this.ring.rotation.x=-Math.PI/2;this.scene.add(this.ring);
  this.scene.add(this.player);this.player.position.copy(this.playerPosition);
  this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(host);this.resize();
  this.weather=new TownWeather(this.scene,this.sky,this.sun,hemi,this.atmosphere);this.adventure=new TownAdventure(this);this.bind();void this.load();this.animate();
 }
 on(target:EventTarget,event:string,fn:EventListener,opts?:AddEventListenerOptions){target.addEventListener(event,fn,opts);this.disposers.push(()=>target.removeEventListener(event,fn,opts));}
 emit(){if(!this.dead)this.publish({...this.state,adventure:this.adventure?.snapshot(),weather:this.weather?.snapshot(),audio:this.sound.snapshot(),position:{x:this.playerPosition.x,y:-this.playerPosition.z}});}
 async load(){try{
  const draco=new DRACOLoader();draco.setDecoderPath(assetPath('/draco/'));draco.setWorkerLimit(2);this.disposers.push(()=>draco.dispose());const loader=new GLTFLoader().setDRACOLoader(draco);
  const parts=['world-v3','interiors-v3','vegetation-v3','terrain-v6','furniture-ground-v10','furniture-upper-v10','streets-v7','surface-v7','details/house-v10','details/connector-v9','details/stairs-support-v10','details/life-v10',...['west','east','walls'].map(id=>'nature/natural-grass-'+id),...['terrain','river-bridge','trees-west','trees-east','groundcover'].map(id=>'expansion/expansion-'+id),...['nobita','doraemon','shizuka','gian','suneo','tamako','nobisuke'].map(id=>'actors/'+id),'fauna/cat','fauna/sparrow','fauna/sparrow_ash','vehicles/kei_hatchback','vehicles/kei_truck','gadgets/bamboo','gadgets/door','gadgets/drawer','gadgets/time-machine','gadgets/season-extras'];const progress=parts.map(()=>0);const [gltfs,data]=await Promise.all([Promise.all(parts.map((part,i)=>loader.loadAsync(assetPath('/models/'+part+'.glb?v=20260907-video10-final'),e=>{progress[i]=e.total?e.loaded/e.total:Math.min(.9,progress[i]+.03);this.state.progress=Math.round(progress.reduce((a,b)=>a+b,0)/parts.length*94);this.emit();}))),fetch(assetPath('/models/world.json?v=10')).then(r=>{if(!r.ok)throw new Error('world data');return r.json();})]);
  if(this.dead)return;this.assetRevision=(data as {revision:number}).revision;this.colliders=(data as {colliders:Collider[]}).colliders;this.groundSurfaces=(data as {walkableSurfaces?:GroundSurface[]}).walkableSurfaces??[];const landscape=data as {heightfield?:Heightfield;walkableOverlays?:WalkMesh[]};if(landscape.heightfield)setExpansionTerrain(landscape.heightfield,landscape.walkableOverlays);this.playerPosition.y=groundHeight(this.playerPosition.x,-this.playerPosition.z,.23,this.groundSurfaces);this.player.position.copy(this.playerPosition);this.world=new THREE.Group();this.ecosystem=new TownEcosystem(this.colliders,this.groundSurfaces,(id,clip)=>{const m=this.motions.get(id);if(m&&m.oneShotUntil<=this.elapsed)this.playClip(id,clip);});for(let i=0;i<gltfs.length;i++){
   const gltf=gltfs[i];if(parts[i].startsWith('vehicles/')||parts[i].startsWith('gadgets/'))continue;if(parts[i].startsWith('fauna/')){this.ecosystem.addFauna(gltf,parts[i]==='fauna/cat'?'cat':'bird',this.world,parts[i].endsWith('_ash')?1:0);continue;}this.world.add(gltf.scene);
   if(parts[i].startsWith('actors/')){const id=parts[i].split('/')[1];const root=gltf.scene.getObjectByName('actor_'+id);if(!root)throw new Error('Missing actor '+id);
    if(id!=='nobita'){const origin=(data as {actors:Record<string,[number,number,number]>}).actors['actor_'+id];if(origin)root.position.set(origin[0],origin[2],-origin[1]);}
    const mixer=new THREE.AnimationMixer(root);const actions=new Map(gltf.animations.map(clip=>[clip.name,mixer.clipAction(clip)]));
    this.motions.set(id,{mixer,actions,current:'',oneShotUntil:0});this.playClip(id,'Idle');mixer.update(i*.31);
    mixer.addEventListener('finished',()=>{this.playClip(id,'Idle');});
   }
  }this.scene.add(this.world);this.ecosystem.addResidents(this.world);this.traffic=new TownTraffic(this.world);for(let i=0;i<parts.length;i++)if(parts[i].startsWith('vehicles/'))this.traffic.addAsset(gltfs[i].scene,parts[i].endsWith('kei_truck')?'truck':'car');
  const unique=new Set<THREE.Material>();
  this.world.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true;if(o instanceof THREE.SkinnedMesh)o.frustumCulled=false;const ms=Array.isArray(o.material)?o.material:[o.material];o.castShadow=!ms.every(m=>/Decal|LotTransition/.test(m.name));ms.forEach(m=>{if(unique.has(m))return;unique.add(m);if(m instanceof THREE.MeshStandardMaterial){for(const texture of [m.map,m.normalMap,m.roughnessMap])if(texture)texture.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());if(m.map){m.map.wrapS=m.map.wrapT=THREE.RepeatWrapping;if(!m.normalMap&&/warm oak|walnut|honey floor|woven rush|plaster|Oak|Walnut|Timber|Tatami|Curtain|Seat/.test(m.name)){m.bumpMap=m.map;m.bumpScale=/Tatami|Curtain|Seat/.test(m.name)?.0003:.0006;}}
    if(!/^V10_|Glass|Chrome|Bell|Brass|Steel/.test(m.name))m.roughness=Math.max(m.roughness,.42);if(/^Glass/.test(m.name)){m.transparent=true;m.opacity=.12;m.depthWrite=false;}if(/BotanicalLeaf|Hydrangea|GrassBlade/.test(m.name))m.side=THREE.DoubleSide;if(m.name==='soft blue window glass')m.roughness=.32;if(/Decal|LotTransition/.test(m.name)){m.transparent=true;m.depthWrite=false;m.polygonOffset=true;m.polygonOffsetFactor=-1;m.polygonOffsetUnits=-1;}}});this.atmosphere.install(o);this.water.install(o);}});
  const avatar=this.world.getObjectByName('actor_nobita');if(avatar){avatar.removeFromParent();avatar.position.set(0,0,0);this.player.add(avatar);}
  // Preserve imported mesh axes; yaw belongs to the enclosing player group.
  this.weather.install(this.world);for(let i=0;i<parts.length;i++)if(parts[i].startsWith('gadgets/')){const id=parts[i].split('/')[1];if(id==='season-extras'){gltfs[i].scene.updateMatrixWorld(true);this.weather.addAsset(gltfs[i].scene);for(const kind of ['baseball','bat']){const o=gltfs[i].scene.getObjectByName(kind==='baseball'?'Prop_Baseball':'Prop_Bat');if(o){const g=new THREE.Group();g.add(o.clone(true));this.adventure.addAsset(kind,g);}}}else this.adventure.addAsset(id,gltfs[i].scene);}
  this.state.ready=true;this.state.progress=100;this.layers();this.emit();
 }catch(e){if(!this.dead){console.error('Town load:',e);this.state.error='小镇没有完整载入，请刷新后再试。';this.emit();}}}
 playClip(id:string,name:string,restart=false){
  const motion=this.motions.get(id);if(!motion||(!restart&&motion.current===name))return;const next=motion.actions.get(name);if(!next)return;
  const old=motion.actions.get(motion.current);next.reset().setEffectiveWeight(1);const walkRate:Record<string,number>={doraemon:.28/.212,shizuka:.52/.60,gian:.57/(.60*1.57/1.4),suneo:.51/(.60*1.35/1.4)};next.setEffectiveTimeScale(name==='Walk'?(walkRate[id]??1):1);
  next.setLoop(name==='Wave'?THREE.LoopOnce:THREE.LoopRepeat,name==='Wave'?1:Infinity);next.clampWhenFinished=false;next.play();if(old&&old!==next)old.crossFadeTo(next,.18,false);
  motion.current=name;motion.oneShotUntil=name==='Wave'?this.elapsed+next.getClip().duration:0;
 }
 wave(id='nobita'){if(!this.state.ready)return;this.playClip(id,'Wave',true);}
 idlePlayer(){const m=this.motions.get('nobita');if(m&&m.oneShotUntil<=this.elapsed)this.playClip('nobita','Idle');}
 resize(){const w=this.host.clientWidth,h=this.host.clientHeight;if(!w||!h)return;this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h);this.composer.setSize(w,h);}
 bind(){const canvas=this.renderer.domElement;
  this.on(window,'keydown',((e:KeyboardEvent)=>{if((e.target as HTMLElement)?.closest('input,textarea,[role="dialog"]'))return;if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();this.keys.add(e.code);if(e.repeat)return;if(e.code==='KeyV')this.setMode(this.state.mode==='orbit'?'first':'orbit');if(e.code==='KeyE')this.interact();if(e.code==='KeyR')this.toggleCutaway();if(e.code==='KeyH')this.wave();if(e.code==='Space'&&(this.adventure.state.flying||this.adventure.state.activity==='baseball'||this.adventure.state.activity==='dodge')){e.preventDefault();this.adventure.action();}if(e.code==='KeyC')this.adventure.land();if(e.code==='Escape'){this.state.actor=null;this.emit();}}) as EventListener);
  this.on(window,'keyup',((e:KeyboardEvent)=>{this.keys.delete(e.code);}) as EventListener);this.on(window,'blur',()=>{this.keys.clear();this.touch={x:0,y:0};this.pointer.down=false;});
  this.on(document,'visibilitychange',()=>{if(document.hidden){this.keys.clear();this.touch={x:0,y:0};}});
  this.on(canvas,'pointerdown',((e:PointerEvent)=>{if(!this.state.ready)return;canvas.focus({preventScroll:true});this.pointer={down:true,x:e.clientX,y:e.clientY,moved:0};canvas.setPointerCapture(e.pointerId);}) as EventListener);
  this.on(canvas,'pointermove',((e:PointerEvent)=>{if(!this.pointer.down&&document.pointerLockElement!==canvas)return;const dx=document.pointerLockElement?e.movementX:e.clientX-this.pointer.x,dy=document.pointerLockElement?e.movementY:e.clientY-this.pointer.y;this.pointer.x=e.clientX;this.pointer.y=e.clientY;this.pointer.moved+=Math.abs(dx)+Math.abs(dy);if(this.state.mode==='first'){this.yaw-=dx*.004;this.pitch=THREE.MathUtils.clamp(this.pitch-dy*.003,-1.35,1.35);}else{this.azimuth-=dx*.005;}}) as EventListener);
  this.on(canvas,'pointerup',((e:PointerEvent)=>{this.pointer.down=false;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);if(this.pointer.moved<6&&this.state.mode==='orbit')this.pointTo(e.clientX,e.clientY);}) as EventListener);
  this.on(canvas,'pointercancel',()=>{this.pointer.down=false;});
  this.on(canvas,'wheel',((e:WheelEvent)=>{e.preventDefault();if(this.state.mode==='orbit')this.distance=THREE.MathUtils.clamp(this.distance*Math.exp(e.deltaY*.001),this.state.inside?5:9,175);}) as EventListener,{passive:false});
  this.on(canvas,'contextmenu',e=>e.preventDefault());
  this.on(canvas,'webglcontextlost',e=>{e.preventDefault();this.state.error='图形画面已暂停，请刷新恢复。';this.emit();});
 }
 setMode(mode:ViewMode){this.state.mode=mode;this.walkTarget=null;if(mode==='first'){this.yaw=this.state.floor?Math.PI:0;this.pitch=0;}else{document.exitPointerLock?.();this.distance=this.state.inside?(this.state.floor?7.2:11):35;this.target.copy(this.playerPosition).add(new THREE.Vector3(0,1,0));}this.layers();this.emit();}
 setPaused(value:boolean){this.paused=value;this.keys.clear();this.touch={x:0,y:0};}
 setTouch(x:number,y:number){this.touch={x,y};}
 setQuality(value:boolean){this.quality=value;this.ao.enabled=value;this.renderer.setPixelRatio(value?Math.min(devicePixelRatio,1.65):1);this.resize();}
 toggleCutaway(){this.state.cutaway=!this.state.cutaway;if(this.state.cutaway){this.targetGoal.set(-13,3,-5);this.target.copy(this.targetGoal);this.distance=28;}this.layers();this.emit();}
 setSunset(){this.state.sunset=!this.state.sunset;this.weather.setHour(this.state.sunset?17.5:15.5);this.emit();}
 teleport(id:PlaceId){this.adventure.onTeleport();const p=PLACES.find(p=>p.id===id);if(!p)return;this.playerPosition.set(p.x,p.floor?HOUSE.upper:groundHeight(p.x,p.y,.23,this.groundSurfaces),-p.y);this.state.place=id;this.state.floor=p.floor;this.state.inside=p.floor===1;this.state.actor=null;this.walkTarget=null;this.state.cutaway=p.floor===1;this.targetGoal.copy(this.playerPosition).add(new THREE.Vector3(0,1,0));this.target.copy(this.targetGoal);this.distance=p.floor?7.2:30;this.player.position.copy(this.playerPosition);this.yaw=id==='bedroom'?Math.PI:0;this.pitch=0;this.layers();this.emit();}
 enterHome(){this.adventure.onTeleport();this.playerPosition.set(-11.50,HOUSE.lower,-1.1);this.player.position.copy(this.playerPosition);this.state.inside=true;this.state.floor=0;this.walkTarget=null;this.distance=13;this.targetGoal.copy(this.playerPosition).add(new THREE.Vector3(0,1,0));this.target.copy(this.targetGoal);this.layers();this.emit();}
 showTown(){if(this.adventure.state.activity==='time')this.adventure.onTeleport();this.state.mode='orbit';this.state.cutaway=false;this.targetGoal.set(0,1,27);this.target.copy(this.targetGoal);this.distance=158;this.layers();this.emit();}
 setFloor(floor:number){if(floor){this.teleport('bedroom');}else{this.enterHome();this.state.cutaway=true;this.layers();this.emit();}}
 layers(){if(!this.world)return;const indoor=this.state.inside;const doll=this.state.mode==='orbit'&&(indoor||this.state.cutaway);const lower=doll&&this.state.floor===0;this.player.visible=this.state.mode==='orbit';
  const set=(name:string,v:boolean)=>{const o=this.world!.getObjectByName(name);if(o)o.visible=v;};
  set('facade_roof',!doll);set('facade_upper',!doll&&!lower);set('facade_ground',!doll);set('home_roof',!doll);set('home_ceiling',!doll);set('home_eaves',!doll);
  set('home_upper',!lower);set('furniture_upper',!lower);set('actor_closet_toy',!lower);
  set('home_front_upper',!doll);set('home_front_ground',!doll);
  set('hero_floor',!lower);set('hero_props',!lower);set('hero_closet',!lower);set('hero_shell',!doll&&!lower);set('hero_front',!doll&&!lower);set('hero_ceiling',!doll&&!lower);
  for(const [name,visible] of [['v9_hero_front_window',!doll&&!lower],['v9_hero_shell_window',!doll&&!lower],['v9_home_front_ground_window',!doll],['v9_home_front_upper_window',!doll],['v9_home_upper_window',!lower],['v9_furniture_upper',!lower]] as const)set(name,visible);
  // First-person keeps complete walls and ceiling. Dollhouse removes the camera-facing wall and roof.
 }
 nearInteraction(){const p=this.playerPosition;const x=p.x,y=-p.z,z=p.y;let near='';let actor:Actor|undefined;
  for(const a of ACTORS){const pos=this.ecosystem?.actorPosition(a.id);const ax=pos?.x??a.x,ay=pos?-pos.z:a.y,az=pos?.y??a.z;if(Math.hypot(x-ax,y-ay)<2.7&&Math.abs(z-az)<1.3){near='和'+a.name+'聊聊';actor=a;break;}}
  if(x>-13.5&&x<-12.55&&y>.45&&y<1.5&&z<2)near='上楼 · 大雄的房间';
  if(this.state.inside&&z>2.8&&x<-12.55&&x>-13.5&&y>4.85)near='下楼 · 客厅';
  if(!this.state.inside&&Math.hypot(x+11.5,y-0.35)<2.8)near='推门 · 回家';
  if(this.state.inside&&Math.hypot(x+11.5,y-1.25)<1.35&&z<2)near='出门 · 街道';
  if(z>3&&Math.hypot(x+11.4,y-5.5)<1.0)near='看看哆啦A梦的壁橱';
  if(z>3&&Math.hypot(x+10.59,y-1.15)<1.45)near=this.adventure.state.drawer?'进入抽屉里的时光机':'拉开书桌抽屉';
  return{near,actor};
 }
 interact(){if(!this.state.ready)return;const {near,actor}=this.nearInteraction();
  if(near.startsWith('拉开')){this.adventure.openDrawer();return;}if(near.startsWith('进入抽屉')){this.adventure.enterTime();return;}
  if(near.startsWith('上楼')){this.teleport('bedroom');return;}if(near.startsWith('下楼')){this.enterHome();return;}if(near.startsWith('推门')){this.enterHome();return;}if(near.startsWith('出门')){this.teleport('home');return;}
  if(near.includes('壁橱')){this.state.actor={id:'closet',name:'哆啦A梦的壁橱',x:0,y:0,z:0,color:'#008ac3',lines:['叠好的被褥和小枕头。原来，哆啦A梦每天就睡在这里。']};this.emit();return;}
  if(actor){this.state.actor=actor;this.wave(actor.id);this.wave();this.emit();}
 }
 meetActor(id:string){const actor=ACTORS.find(a=>a.id===id);if(!actor||!this.state.ready)return false;this.adventure.onTeleport();const target=this.ecosystem?.actorPosition(id)??new THREE.Vector3(actor.x,actor.z,-actor.y);let candidate:THREE.Vector3|undefined;for(let i=0;i<12;i++){const a=i*Math.PI/6,x=target.x+Math.cos(a)*1.2,z=target.z+Math.sin(a)*1.2,h=groundHeight(x,-z,target.y,this.groundSurfaces);if(Math.abs(h-target.y)<.5&&!collides(x,-z,h,this.colliders)){candidate=new THREE.Vector3(x,h,z);break;}}if(!candidate)return false;this.playerPosition.copy(candidate);this.player.position.copy(candidate);this.state.inside=insideHouse(candidate.x,-candidate.z);this.state.floor=candidate.y>2.75?1:0;this.state.actor=actor;this.targetGoal.copy(target).add(new THREE.Vector3(0,.9,0));this.target.copy(this.targetGoal);this.distance=this.state.inside?8:15;this.yaw=Math.atan2(candidate.x-target.x,candidate.z-target.z);this.wave(id);this.wave();this.layers();this.emit();return true;}
 closeDialogue(){this.state.actor=null;this.emit();}
 pointTo(x:number,y:number){const rect=this.renderer.domElement.getBoundingClientRect();const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((x-rect.left)/rect.width*2-1,-(y-rect.top)/rect.height*2+1),this.camera);
  const visible=(o:THREE.Object3D|null):boolean=>!o||(o.visible&&visible(o.parent));
  const hits=(this.world?ray.intersectObject(this.world,true):[]).filter(h=>visible(h.object));const hit=hits[0];
  let actorHit:THREE.Object3D|null=hit?.object??null;while(actorHit&&!actorHit.name.startsWith('actor_'))actorHit=actorHit.parent;
  if(actorHit){const a=ACTORS.find(a=>'actor_'+a.id===actorHit.name);if(a){this.state.actor=a;this.wave(a.id);this.wave();this.emit();return;}}
  const walkHit=hits.find(h=>inTown(h.point.x,-h.point.z)&&Math.abs(h.point.y-groundHeight(h.point.x,-h.point.z,this.playerPosition.y,this.groundSurfaces))<.23);
  if(walkHit){const point=walkHit.point.clone(),height=groundHeight(point.x,-point.z,this.playerPosition.y,this.groundSurfaces);if(collides(point.x,-point.z,height,this.colliders))return;point.y=height;this.walkTarget=point;}
 }
 move(dt:number){if(!this.state.ready||this.paused||this.state.actor||this.adventure.state.activity==='time'){this.idlePlayer();return;}if(this.adventure.flightMove(dt))return;const k=this.keys;let f=(k.has('KeyW')||k.has('ArrowUp')?1:0)-(k.has('KeyS')||k.has('ArrowDown')?1:0)-this.touch.y;let r=(k.has('KeyD')||k.has('ArrowRight')?1:0)-(k.has('KeyA')||k.has('ArrowLeft')?1:0)+this.touch.x;
  const direction=new THREE.Vector3();const angle=this.state.mode==='first'?this.yaw:this.azimuth;
  if(f||r){this.walkTarget=null;direction.set(-Math.sin(angle)*f+Math.cos(angle)*r,0,-Math.cos(angle)*f-Math.sin(angle)*r);}
  else if(this.walkTarget){direction.subVectors(this.walkTarget,this.playerPosition);direction.y=0;if(direction.length()<.18){this.walkTarget=null;direction.set(0,0,0);}}
  const moving=direction.lengthSq()>.005;const beforeMove=this.playerPosition.clone();if(moving){direction.normalize();const speed=(k.has('ShiftLeft')||k.has('ShiftRight')?1.95:1.05)*dt;const old=this.playerPosition.clone();const x=THREE.MathUtils.clamp(old.x+direction.x*speed,TOWN_BOUNDS.x0,TOWN_BOUNDS.x1),sy=-old.z;const z=groundHeight(x,sy,old.y,this.groundSurfaces);
   if(!collides(x,sy,z,this.colliders)&&!this.traffic?.collides(x,sy,z))this.playerPosition.x=x;
   const nz=THREE.MathUtils.clamp(old.z+direction.z*speed,-TOWN_BOUNDS.y1,-TOWN_BOUNDS.y0),nzY=groundHeight(this.playerPosition.x,-nz,old.y,this.groundSurfaces);if(!collides(this.playerPosition.x,-nz,nzY,this.colliders)&&!this.traffic?.collides(this.playerPosition.x,-nz,nzY))this.playerPosition.z=nz;
   this.playerPosition.y=groundHeight(this.playerPosition.x,-this.playerPosition.z,old.y,this.groundSurfaces);
   if(this.playerPosition.distanceToSquared(old)<.0000001&&this.walkTarget)this.walkTarget=null;
   const yaw=Math.atan2(direction.x,direction.z);this.player.quaternion.slerp(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),yaw),Math.min(1,dt*13));
   this.targetGoal.copy(this.playerPosition).add(new THREE.Vector3(0,1.05,0));
  }
  this.player.position.copy(this.playerPosition);if(this.playerPosition.distanceToSquared(beforeMove)>1e-8)this.playClip('nobita',k.has('ShiftLeft')||k.has('ShiftRight')?'Run':'Walk');else this.idlePlayer();
  const px=this.playerPosition.x,py=-this.playerPosition.z;const inside=insideHouse(px,py);const floor=inside&&this.playerPosition.y>2.8?1:0;
  if(inside!==this.state.inside||floor!==this.state.floor){this.state.inside=inside;this.state.floor=floor;if(inside&&this.state.mode==='orbit'){this.distance=floor?7.2:11;}this.layers();this.emit();}
 }
 animate=()=>{if(this.dead)return;this.raf=requestAnimationFrame(this.animate);const raw=this.clock.getDelta();this.frameSeconds=THREE.MathUtils.lerp(this.frameSeconds,Math.min(raw,1),.04);const dt=Math.min(raw,.1);this.elapsed+=dt;this.move(dt);this.atmosphere.update(this.elapsed);this.water.update(this.elapsed);this.weather.update(this.paused?0:dt,this.playerPosition,this.state.inside||this.adventure.state.activity==='time');this.interiorLight.update(this.weather.state.hour,this.weather.state.season);this.sound.update(dt,this.weather.state.season,this.weather.state.hour,this.state.inside,this.adventure.state.flying,this.weather.state.night);if(this.state.ready&&!this.paused)this.adventure.update(dt);if(this.state.ready&&!this.paused)this.ecosystem?.update(dt,this.elapsed,this.playerPosition,this.state.actor?.id??null);if(this.state.ready&&!this.paused)this.traffic?.update(dt,this.playerPosition,ACTORS.map(a=>this.ecosystem?.actorPosition(a.id)).filter((p):p is THREE.Vector3=>!!p));for(const m of this.motions.values())m.mixer.update(dt);
  if(this.state.mode==='first'){this.camera.position.copy(this.playerPosition).add(new THREE.Vector3(0,1.20,0));this.camera.rotation.set(this.pitch,this.yaw,0,'YXZ');if(this.camera.fov!==67){this.camera.fov=67;this.camera.updateProjectionMatrix();}}
  else{if(this.camera.fov!==38){this.camera.fov=38;this.camera.updateProjectionMatrix();}this.target.lerp(this.targetGoal,Math.min(1,dt*4));const off=new THREE.Vector3(Math.sin(this.azimuth)*this.distance*.7071,this.distance*.7071,Math.cos(this.azimuth)*this.distance*.7071);this.cameraTarget.copy(this.target).add(off);this.camera.position.lerp(this.cameraTarget,Math.min(1,dt*6));this.camera.lookAt(this.target);}
  if(this.adventure.state.activity==='time')this.adventure.timeCamera();this.sky.update(this.elapsed,this.camera);this.ring.position.copy(this.playerPosition);this.ring.position.y+=.02;this.ring.visible=this.state.mode==='orbit'&&this.adventure.state.activity!=='time'&&!this.adventure.state.flying;this.ring.scale.setScalar(1+Math.sin(this.elapsed*3)*.06);
  if(this.elapsed-this.sendAt>.25){this.sendAt=this.elapsed;this.state.near=this.nearInteraction().near;let closest=PLACES[0],dist=Infinity;for(const p of PLACES){if(p.id==='bedroom')continue;const d=Math.hypot(p.x-this.playerPosition.x,p.y+this.playerPosition.z);if(d<dist){dist=d;closest=p;}}this.state.place=this.state.inside&&this.state.floor?'bedroom':closest.id;this.emit();}
  const shadowFocus=this.state.mode==='first'?this.playerPosition:this.target,extent=this.state.mode==='first'?12:this.distance>60?48:22;
  this.sun.target.position.copy(shadowFocus);this.sun.position.copy(shadowFocus).add(this.weather.sunOffset);const shadowCamera=this.sun.shadow.camera;
  if(shadowCamera.right!==extent){Object.assign(shadowCamera,{left:-extent,right:extent,top:extent,bottom:-extent});shadowCamera.updateProjectionMatrix();}
  if(!document.hidden){this.sun.shadow.needsUpdate=true;this.renderer.info.reset();if(this.quality)this.composer.render();else this.renderer.render(this.scene,this.camera);}
 };
 destroy(){this.dead=true;this.sound.dispose();this.ecosystem?.dispose();for(const m of this.motions.values()){m.mixer.stopAllAction();m.mixer.uncacheRoot(m.mixer.getRoot());}this.motions.clear();cancelAnimationFrame(this.raf);this.resizeObserver.disconnect();this.disposers.forEach(f=>f());this.composer.dispose();this.ao.dispose();this.scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>{if(m instanceof THREE.MeshStandardMaterial)m.map?.dispose();m.dispose();});}});this.environmentTarget.dispose();this.renderer.dispose();this.renderer.domElement.remove();}
}
