import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
import * as THREE from 'three';
import {createRequire} from 'node:module';
let code=ts.transpileModule(fs.readFileSync('lib/town/traffic.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
code=code.replaceAll("'three'",JSON.stringify(pathToFileURL(process.cwd()+'/node_modules/three/build/three.module.js').href));
const {TownTraffic,signalPhase}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
for(let time=0;time<76;time+=.1){const p=signalPhase(time);assert(!(p.EW!=='red'&&p.NS!=='red'),'Conflicting signals');}
function source(length){const g=new THREE.Group();g.add(new THREE.Mesh(new THREE.BoxGeometry(1.76,1.37,length)));for(const n of ['FL','FR','RL','RR']){const w=new THREE.Group();w.name='Wheel_'+n;g.add(w);}return g;}
const traffic=new TownTraffic(new THREE.Group());traffic.addAsset(source(3.332),'car');traffic.addAsset(source(3.541),'truck');
const player=new THREE.Vector3(100,0,100);let stopped=0,crossings=0;
for(let i=0;i<5400;i++){
 const before=traffic.cars.map(c=>({front:c.root.position.x+c.direction*c.length/2,x:c.root.position.x}));
 traffic.update(1/30,player);
 traffic.cars.forEach((c,k)=>{
  if(c.parked)return;const stop=c.direction>0?-5.8:7.8,prior=(stop-before[k].front)*c.direction,after=(stop-(c.root.position.x+c.direction*c.length/2))*c.direction;
  if(prior>0&&after<0&&Math.abs(before[k].x-c.root.position.x)<1){assert.equal(signalPhase(traffic.time).EW,'green','Vehicle crossed stop line against signal');crossings++;}
  if(c.speed<.03&&c.waiting==='signal')stopped++;
 });
}
assert(stopped>20&&crossings>2,'Traffic must actually stop and resume');
for(const car of traffic.cars.filter(c=>!c.parked)){assert(car.distance>120);assert.equal(car.wheels.length,4);assert(car.wheels.every(w=>Math.abs(w.rotation.x)>1));}
// Hold a pedestrian in the lane, verify braking clearance and body collision.
const t=new TownTraffic(new THREE.Group());t.addAsset(source(3.332),'car');const p=new THREE.Vector3(-20,.133,6.86);
for(let i=0;i<1200;i++)t.update(1/30,p);
const c=t.cars[0];assert(c.root.position.x+c.length/2<=p.x-.70);assert(c.speed<.03);assert.equal(c.waiting,'pedestrian');assert(t.collides(c.root.position.x,-c.root.position.z,.133));
// A resident entering laterally beside the car body must also stop it.
const lateral=new TownTraffic(new THREE.Group());lateral.addAsset(source(3.332),'car');const lateralCar=lateral.cars[0];lateralCar.root.position.x=0;lateralCar.speed=1.5;
lateral.update(1/60,player,[new THREE.Vector3(0,.133,6.86)]);assert.equal(lateralCar.root.position.x,0);assert.equal(lateralCar.speed,0);assert.equal(lateralCar.waiting,'pedestrian');
const report={lateralPedestrianStop:true,duration:180,noConflictingSignals:true,redStops:stopped,greenCrossings:crossings,pedestrianClearance:p.x-(c.root.position.x+c.length/2),rollingWheels:8,vehicles:traffic.snapshot()};
// Regress the actual exported car, including its mesh transforms. A synthetic
// axis-aligned box did not expose the old 1.3376-metre false grounding offset.
const require=createRequire(import.meta.url),{load}=require('../../../work/vehicle-v9/mesh_diag.cjs');
const real=new TownTraffic(new THREE.Group());
real.addAsset(load('public/models/vehicles/kei_hatchback.glb').scene,'car');
real.addAsset(load('public/models/vehicles/kei_truck.glb').scene,'truck');
let maximumContactGap=0;
for(let phase=0;phase<64;phase++){
 for(const car of real.cars){
  car.wheels.forEach(w=>w.rotation.x=phase*Math.PI/32);car.root.updateMatrixWorld(true);
  const expected=car.parked?.054:.133,min=new THREE.Box3().setFromObject(car.root,true).min.y;
  maximumContactGap=Math.max(maximumContactGap,Math.abs(min-expected));
  assert(Math.abs(min-expected)<.001,'Real vehicle must remain grounded through wheel rotation');
  assert(car.length>3.3&&car.length<3.6&&car.width<1.8,'Actual vehicle dimensions were inflated by transforms');
 }
}
report.actualExport={allFourCarsGrounded:true,wheelPhases:64,maximumContactGapMetres:maximumContactGap};
fs.writeFileSync('../街景升级/车辆通行验证.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
