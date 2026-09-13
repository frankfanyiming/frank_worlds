// Cook existing render meshes for the mobile derivative. Collision primitives,
// node transforms, skin joints and animation samples are explicitly protected.
import {createRequire} from 'node:module';
import {readFile,writeFile,readdir} from 'node:fs/promises';
import {resolve,join,relative} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const req=createRequire(resolve(process.env.MOBILE_ASSET_TOOLS||'tools/mobile-assets','package.json'));
const imp=n=>import(pathToFileURL(req.resolve(n)).href);
const {NodeIO}=await imp('@gltf-transform/core'),{ALL_EXTENSIONS}=await imp('@gltf-transform/extensions'),{weldPrimitive,simplifyPrimitive,prune}=await imp('@gltf-transform/functions'),{MeshoptSimplifier}=await imp('meshoptimizer');await MeshoptSimplifier.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const project=resolve(process.argv[2]);if(!project.includes('native-mobile24'))throw Error('Use an isolated derivative');
const sha=b=>createHash('sha256').update(b).digest('hex');
const array=a=>a?sha(Buffer.from(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength)):null;
const prim=p=>JSON.stringify({indices:array(p.getIndices()),attributes:p.listSemantics().map(s=>[s,array(p.getAttribute(s))])});
const protectedState=doc=>JSON.stringify({nodes:doc.getRoot().listNodes().map(n=>[n.getName(),n.getMatrix(),n.getSkin()?.listJoints().map(j=>j.getName())]),animations:doc.getRoot().listAnimations().map(a=>[a.getName(),a.listSamplers().map(s=>[array(s.getInput()),array(s.getOutput()),s.getInterpolation()])])});
const report=[];
async function walk(dir){for(const ent of await readdir(dir,{withFileTypes:true})){
 const path=join(dir,ent.name);if(ent.isDirectory()){await walk(path);continue;}if(!path.endsWith('.glb'))continue;
 // Baked rooms use their separate UV2 scenes, not these fallback GLBs.
 const doc=await io.read(path),contract=protectedState(doc),guard=new Map();
 for(const node of doc.getRoot().listNodes())if(/collision|navigation|walkable/i.test(node.getName()))for(const p of node.getMesh()?.listPrimitives()||[])guard.set(p,prim(p));
 let before=0,after=0;
 for(const mesh of doc.getRoot().listMeshes())for(const p of mesh.listPrimitives()){
  const count=()=> (p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3;before+=count();
  if(!guard.has(p)&&p.getMode()===4&&count()>400){
   weldPrimitive(p);
   const actor=doc.getRoot().listNodes().some(n=>n.getMesh()===mesh&&n.getSkin());
   simplifyPrimitive(p,{simplifier:MeshoptSimplifier,ratio:actor?.45:.3,error:actor?.0015:.004,lockBorder:false});
  }
  after+=count();
 }
 for(const[p,value]of guard)if(prim(p)!==value)throw Error('Collision changed: '+path);
 if(protectedState(doc)!==contract)throw Error('Animation/transform changed: '+path);
 await doc.transform(prune({keepLeaves:true,keepAttributes:true,keepSolidTextures:true}));
 await io.write(path,doc);report.push({file:relative(project,path),before:Math.round(before),after:Math.round(after),protectedCollisionPrimitives:guard.size,animationAndTransformsUnchanged:true});
}}
await walk(join(project,'assets'));await writeFile(join(project,'mobile-geometry-report.json'),JSON.stringify(report,null,2)+'\n');console.log(project,JSON.stringify({before:report.reduce((n,r)=>n+r.before,0),after:report.reduce((n,r)=>n+r.after,0)}));
