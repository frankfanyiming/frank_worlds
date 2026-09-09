import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
const modules={};
for(const name of ['world','life','ecosystem']){
 let code=ts.transpileModule(fs.readFileSync(`lib/town/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
 for(const key in modules)code=code.replaceAll(`'./${key}'`,JSON.stringify(modules[key]));
 code=code.replaceAll("'three'",JSON.stringify(pathToFileURL(process.cwd()+'/node_modules/three/build/three.module.js').href));
 code=code.replaceAll("'three/addons/utils/SkeletonUtils.js'",JSON.stringify(pathToFileURL(process.cwd()+'/node_modules/three/examples/jsm/utils/SkeletonUtils.js').href));
 modules[name]='data:text/javascript;base64,'+Buffer.from(code).toString('base64');
}
const {collides,groundHeight,HOUSE}=await import(modules.world),{ROUTINES,findRoute}=await import(modules.life),{TownEcosystem}=await import(modules.ecosystem);
const THREE=await import('three');
const data=JSON.parse(fs.readFileSync('public/models/world.json','utf8')),scene=new THREE.Group(),clips=new Map();
for(const r of ROUTINES){const root=new THREE.Group();root.name='actor_'+r.id;const p=data.actors[root.name];root.position.set(p[0],p[2],-p[1]);scene.add(root);}
const life=new TownEcosystem(data.colliders,data.walkableSurfaces,(id,clip)=>clips.set(id,clip));life.addResidents(scene);
const player=new THREE.Vector3(-9.6,.133,6.3);
for(let step=0;step<7200;step++){
 life.update(1/30,step/30,player,null);
 for(const r of life.residents)assert(!collides(r.root.position.x,-r.root.position.z,r.root.position.y,data.colliders,.18),`Resident intersects wall or furniture: ${r.routine.id}`);
}
for(const r of life.residents)assert(r.travel>1,`${r.routine.id} never gets a walkable route (${r.travel}m)`);
const mother=life.residents.find(r=>r.routine.id==='tamako'),old=mother.root.position.clone();life.update(.1,241,player,'tamako');assert(mother.root.position.equals(old),'Speaking resident must stop');
for(let y=HOUSE.stairY0;y<=HOUSE.stairY1;y+=.02){const z=groundHeight(HOUSE.stairX,y,.48,data.walkableSurfaces);assert(!collides(HOUSE.stairX,y,z,data.colliders),'New stair route is obstructed');}
// A companion must follow the real collision-aware route, not just set a flag.
const companion=life.residents.find(r=>r.routine.id==='shizuka');companion.root.position.set(-9,.053,24);companion.path=[];companion.wait=0;life.companion='shizuka';life.companionRepath=0;player.set(-6.8,.053,24);const companionStart=companion.root.position.clone();
for(let i=0;i<90;i++){player.x+=.035;life.update(.1,242+i*.1,player,null);assert(!collides(companion.root.position.x,-companion.root.position.z,companion.root.position.y,data.colliders,.18));}
assert(companion.root.position.distanceTo(companionStart)>2,'Invited companion must actually walk');assert(companion.root.position.distanceTo(player)<2.2,'Companion should catch up with a walking player');
const report={companionFollow:true,durationSeconds:240,residents:life.snapshot().residents,dialogueStopsResident:true,stairContinuity:true};
fs.writeFileSync('../七项修订/人物活动验证.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
