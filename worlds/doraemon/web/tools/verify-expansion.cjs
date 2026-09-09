const fs=require('node:fs'),assert=require('node:assert/strict'),ts=require('typescript'),THREE=require('three');
require.extensions['.ts']=(module,file)=>module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,file);
global.document={exitPointerLock(){}};global.localStorage={getItem(){return null},setItem(){}};
const W=require('../lib/town/world.ts'),{TownEngine}=require('../lib/town/engine.ts'),{TownAdventure}=require('../lib/town/adventure.ts');
const data=JSON.parse(fs.readFileSync('public/models/world.json'));assert(data.revision>=9);W.setExpansionTerrain(data.heightfield,data.walkableOverlays);
const e=Object.create(TownEngine.prototype);Object.assign(e,{scene:new THREE.Scene(),world:new THREE.Group(),player:new THREE.Group(),playerPosition:new THREE.Vector3(1,.133,28),ring:new THREE.Group(),target:new THREE.Vector3(),targetGoal:new THREE.Vector3(),camera:new THREE.PerspectiveCamera(),state:{ready:true,mode:'first',floor:0,inside:false,cutaway:false,actor:null},colliders:data.colliders,groundSurfaces:data.walkableSurfaces,sound:{effect(){},stop(){}},motions:new Map(),emit(){},wave(){},keys:new Set(),touch:{x:0,y:0},yaw:Math.PI,azimuth:0,elapsed:0,paused:false});e.adventure=new TownAdventure(e);
const route=[[1,-28],[1,-41],[1,-48],[1,-55],[1,-56],...data.expansion.trail.route.map(p=>p.slice(0,2))];
let steps=0,maxRise=0,prev=e.playerPosition.y;
for(const [x,y] of route){e.walkTarget=new THREE.Vector3(x,0,-y);let frames=0;while(Math.hypot(e.playerPosition.x-x,-e.playerPosition.z-y)>.19&&frames++<1500){e.move(1/30);maxRise=Math.max(maxRise,Math.abs(e.playerPosition.y-prev));prev=e.playerPosition.y;steps++;}
 assert(Math.hypot(e.playerPosition.x-x,-e.playerPosition.z-y)<.20,`Walk blocked heading ${x},${y}, stopped at ${e.playerPosition.toArray()}`);
 assert(!e.state.inside&&e.state.floor===0,'A hill must not be classified as the bedroom');
}
assert(Math.abs(e.playerPosition.y-7.008)<.025,'Player must stand on summit');assert(maxRise<.10,'No large height steps along the route');
const summit=e.playerPosition.clone();
for(const place of W.PLACES){e.teleport(place.id);assert(!W.collides(e.playerPosition.x,-e.playerPosition.z,e.playerPosition.y,data.colliders),`Destination ${place.id} is obstructed`);}
// River banks block walking. The bridge crosses the same band without blockage.
let blockedWater=0;for(let y=-44.25;y<-43.999;y+=.2)for(const x of [-7,8]){const h=W.groundHeight(x,y,.053,data.walkableSurfaces);assert(W.collides(x,y,h,data.colliders));blockedWater++;}
for(let y=-55;y<=-41;y+=.10){const h=W.groundHeight(1,y,.053,data.walkableSurfaces);assert(!W.collides(1,y,h,data.colliders),'Bridge center blocked');assert(h>=.05&&h<.24);}
e.teleport('hill');e.adventure.state.inventory=['bamboo','door'];assert(e.adventure.fly());for(let i=0;i<60;i++)e.adventure.flightMove(1/30);assert(e.playerPosition.y>8.5);assert(e.adventure.land());assert(e.playerPosition.y>7);assert(e.adventure.openPortal('bridge'));assert(e.adventure.enterPortal());assert(Math.abs(e.playerPosition.y-.22)<.005);
// Match arbitrary native triangle barycentric samples (not just mesh corners).
let largestOverlayError=0;for(const mesh of data.walkableOverlays){if(!/Hill_/.test(mesh.name))continue;for(let i=0;i<mesh.triangles.length;i+=17){const t=mesh.triangles[i].map(k=>mesh.vertices[k]);const p=[0,1,2].map(a=>t[0][a]*.2+t[1][a]*.3+t[2][a]*.5);const h=W.overlayHeight(p[0],p[1]);largestOverlayError=Math.max(largestOverlayError,Math.abs(h-p[2]));}}
assert(largestOverlayError<.0001);
const report={revision:data.revision,places:W.PLACES.length,continuousSchoolBridgeHillWalk:true,walkFrames:steps,maximumFrameHeightStep:maxRise,summit:summit.toArray(),allMapDestinationsClear:true,riverFootBarrier:true,bridgeContinuous:true,hillNeverClassifiedAsBedroom:true,flightAndDoorInExpansion:true,largestOverlayError};
fs.writeFileSync('../街景升级/第九版探索验证.json',JSON.stringify(report,null,2));console.log(report);
