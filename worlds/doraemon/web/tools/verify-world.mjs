import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
const code=ts.transpileModule(fs.readFileSync('lib/town/world.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {PLACES,collides,groundHeight}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const data=JSON.parse(fs.readFileSync('public/models/world.json','utf8'));
for(const p of PLACES)assert(!collides(p.x,p.y,p.floor?3.15:.23,data.colliders),`Destination blocked: ${p.id}`);
assert(collides(-17.15,4,.48,data.colliders),'House wall must block player');
// The current neighborhood opens this interior; its perimeter wall still blocks movement.
assert(!collides(-34,5,.23,data.colliders),'Neighbor interior must remain explorable');
assert(collides(-39.25,5,.23,data.colliders),'Neighbor perimeter wall must block player');
assert.equal(groundHeight(-10,5,3.15),3.15);assert.equal(groundHeight(-9,-7,.23),.23);
function route(points,z){
 for(let k=1;k<points.length;k++){
  const a=points[k-1],b=points[k],steps=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/.07);
  for(let i=0;i<=steps;i++){
   const x=a[0]+(b[0]-a[0])*i/steps,y=a[1]+(b[1]-a[1])*i/steps;z=groundHeight(x,y,z,data.walkableSurfaces);
   assert(!collides(x,y,z,data.colliders),`Route blocked at ${x.toFixed(2)}, ${y.toFixed(2)}, ${z.toFixed(2)}`);
  }
 }
 return z;
}
const upper=route([[-9.55,-7],[-9.55,-4.9],[-11.50,.20],[-11.5,.85],[-13.05,.85],[-13.05,2.1],[-13.05,5.55],[-12.05,5.55],[-10.75,5.3],[-10.75,3.3]],.23);
assert.equal(upper,3.15);
const lower=route([[-10.75,3.3],[-10.75,5.5],[-13.05,5.55],[-13.05,.85],[-11.5,.85]],3.15);assert.equal(lower,.48);
assert(Math.abs(groundHeight(-9.6,-6.3,.23,data.walkableSurfaces)-.133)<.001,'Feet must meet the actual street');
console.log('Continuous yard → entrance → stairs → bedroom → return: passed');
if(process.argv.includes('--routes-only'))process.exit(0);
// Three environment layers and seven separately streamed skinned characters.
const files=['world-v3','interiors-v3','vegetation-v3','terrain-v6','furniture-ground-v10','furniture-upper-v10','streets-v7','surface-v7','details/house-v10','details/connector-v9','details/stairs-support-v10','details/life-v10',...['west','east','walls'].map(id=>'nature/natural-grass-'+id),...['terrain','river-bridge','trees-west','trees-east','groundcover'].map(n=>'expansion/expansion-'+n),'vehicles/kei_hatchback','vehicles/kei_truck',...['nobita','doraemon','shizuka','gian','suneo','tamako','nobisuke'].map(n=>'actors/'+n)];
let nodeNames=[],imageNames=[],reports=[];
for(const file of files){
 const glb=fs.readFileSync('public/models/'+file+'.glb');assert.equal(glb.readUInt32LE(0),0x46546c67);assert.equal(glb.readUInt32LE(4),2);
 const j=JSON.parse(glb.subarray(20,20+glb.readUInt32LE(12)).toString());
 assert(glb.length<25*1024*1024,'Model too large: '+file);
 for(const image of j.images??[])assert(Number.isInteger(image.bufferView),'Textures must be embedded: '+file);
 for(const material of j.materials??[]){
  if(material.normalTexture){const image=j.images[j.textures[material.normalTexture.index].source];assert(!image.name.includes('basecolor'),'A color bitmap cannot stand in for a normal map: '+material.name);}
  if(material.name.includes('Decal'))assert.equal(material.alphaMode,'BLEND','Weathering must retain transparent edges');
 }
 nodeNames.push(...j.nodes.map(n=>n.name));imageNames.push(...j.images.map(i=>i.name));
 if(file.startsWith('actors/')){
  assert.equal(j.skins?.length,1,'Each actor must have a skin');assert(j.skins[0].joints.length>=17,'Complete body skeleton required');
  for(const name of ['Idle','Walk','Run','Wave'])assert(j.animations.some(a=>a.name===name&&a.channels.length>=17),'Missing actual joint motion: '+file+' '+name);
  for(const mesh of j.meshes)for(const p of mesh.primitives){assert('JOINTS_0' in p.attributes);assert('WEIGHTS_0' in p.attributes);assert('TEXCOORD_0' in p.attributes);}
 }
 reports.push({file,MB:+(glb.length/1024/1024).toFixed(2),clips:j.animations?.map(a=>a.name)});
}
for(const name of ['home_roof','home_upper','home_front_ground','hero_floor','hero_props','hero_shell','hero_closet','hero_front','hero_ceiling','furniture_ground','facade_ground','facade_upper','facade_roof','surface_detail','street_detail','traffic_signals','actor_nobita','actor_doraemon','v9_stairs_support','v9_garden','River_Water_Surface','Hill_Ascent_Trail'])assert(nodeNames.includes(name),'Missing semantic layer '+name);
assert(imageNames.some(n=>n.includes('interior-atlas')),'User wood UV atlas must be used');
console.log(JSON.stringify({destinations:PLACES.length,collisionChecks:'passed',stairs:'clear',bedroomDoor:'clear',files:reports},null,2));
