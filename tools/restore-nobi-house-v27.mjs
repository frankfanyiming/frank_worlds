// Restore only Nobita's pre-rebuild house. Other houses and the current bedroom
// retain their existing files; mobile gets a separate, bounded derivative.
import {openNobiStairSides} from './nobi-stair-clearance.mjs';
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
const require=createRequire(resolve(process.env.MOBILE_ASSET_TOOLS||'tools/mobile-assets','package.json'));
const imp=n=>import(pathToFileURL(require.resolve(n)).href);
const {Document,NodeIO,PropertyType}=await imp('@gltf-transform/core');
const {ALL_EXTENSIONS}=await imp('@gltf-transform/extensions');
const {copyToDocument,unpartition,prune,dedup,weld,simplifyPrimitive,textureCompress,draco}=await imp('@gltf-transform/functions');
const {MeshoptSimplifier}=await imp('meshoptimizer');
const draco3d=require('draco3dgltf'),sharp=require('sharp');
sharp.concurrency(2);await MeshoptSimplifier.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco3d.createDecoderModule(),'draco3d.encoder':await draco3d.createEncoderModule()});
const snapshot='bafe7f3fa6f9aa63a9e02a3729c77432335ef885';
const base='worlds/doraemon/web/public/models';
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={snapshot,scope:'Nobita house only; current bedroom-v12 and non-Nobita models are unchanged',sources:[],outputs:[]};
const doc=new Document(),scene=doc.createScene('Restored Nobita home');doc.getRoot().setDefaultScene(scene);
const selections=[['world-v3',n=>/^(home_|facade_)/.test(n)],['furniture-ground-v10',n=>n==='furniture_ground'],['furniture-upper-v10',n=>n==='furniture_upper'],['details/house-v10',n=>n.startsWith('v9_home_')||n==='v9_stairs'],['details/life-v10',n=>n==='v10_life_ground'],['details/stairs-support-v10',n=>n==='v9_stairs_support']];
for(const [part,keep] of selections){
 const bytes=execFileSync('git',['show',snapshot+':'+base+'/'+part+'.glb'],{maxBuffer:100*1024*1024});
 const source=await io.readBinary(bytes),nodes=source.getRoot().listNodes().filter(n=>keep(n.getName()));
 if(!nodes.length||nodes.some(n=>n.getParentNode()))throw Error('Review source node hierarchy: '+part);
 for(const ext of source.getRoot().listExtensionsUsed())if(ext.extensionName!=='KHR_draco_mesh_compression')doc.createExtension(ext.constructor).setRequired(ext.isRequired());
 const copied=copyToDocument(doc,source,nodes);for(const node of nodes)scene.addChild(copied.get(node));
 report.sources.push({part,sha256:sha(bytes),bytes:bytes.length,nodes:nodes.map(n=>n.getName())});
}
report.stairClearance=openNobiStairSides(doc);
await doc.transform(unpartition(),prune({keepLeaves:true,keepAttributes:true,keepSolidTextures:true}),dedup({propertyTypes:[PropertyType.TEXTURE,PropertyType.MATERIAL,PropertyType.ACCESSOR]}));
const stats=d=>({triangles:d.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().reduce((v,p)=>v+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0),0),primitives:d.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().length,0),textures:d.getRoot().listTextures().length,nodes:d.getRoot().listNodes().map(n=>({name:n.getName(),matrix:n.getMatrix()}))});
report.original=stats(doc);
async function output(path,d){await mkdir(dirname(path),{recursive:true});await io.write(path,d);const bytes=await readFile(path);const decoded=await io.read(path);const record={path,bytes:bytes.length,sha256:sha(bytes),...stats(decoded)};if(JSON.stringify(record.nodes)!==JSON.stringify(report.original.nodes))throw Error('Node names/transforms changed');report.outputs.push(record);console.log(JSON.stringify({...record,nodes:record.nodes.length}));}
const mobile=await io.readBinary(await io.writeBinary(doc));
await doc.transform(draco({encodeSpeed:5,decodeSpeed:8,quantizePosition:16,quantizeNormal:12,quantizeTexcoord:14}));
await output(base+'/nobi-home-v27.glb',doc);
for(const ext of mobile.getRoot().listExtensionsUsed())if(/^KHR_materials_(clearcoat|transmission|volume|ior|specular|sheen|anisotropy)$/.test(ext.extensionName))ext.dispose();
await mobile.transform(weld());
for(const mesh of mobile.getRoot().listMeshes())for(const p of mesh.listPrimitives()){
 const a=p.getAttribute('POSITION').getArray(),lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(let i=0;i<a.length;i++){const d=i%3;lo[d]=Math.min(lo[d],a[i]);hi[d]=Math.max(hi[d],a[i]);}
 const extent=Math.max(...hi.map((v,i)=>v-lo[i]),.01);
 const normals=p.getAttribute('NORMAL')?.getArray(),uv=p.getAttribute('TEXCOORD_0')?.getArray(),stride=(normals?3:0)+(uv?2:0),attributes=new Float32Array(a.length/3*stride);
 const weights=[...(normals?[.1,.1,.1]:[]),...(uv?[.05,.05]:[])];
 for(let v=0;v<a.length/3;v++){let k=v*stride;if(normals)for(let j=0;j<3;j++)attributes[k++]=normals[v*3+j];if(uv)for(let j=0;j<2;j++)attributes[k++]=uv[v*2+j];}
 const simplifier={simplify:(ids,positions,ps,target,error)=>MeshoptSimplifier.simplifyWithAttributes(ids,positions,ps,attributes,stride,weights,null,target,error,['Permissive'])};
 simplifyPrimitive(p,{simplifier,ratio:.15,error:Math.min(.004,.008/extent)});
}
await mobile.transform(prune({keepLeaves:true,keepAttributes:true,keepSolidTextures:true}),dedup({propertyTypes:[PropertyType.TEXTURE,PropertyType.ACCESSOR]}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'webp',quality:86,slots:/^(?!normalTexture).*$/}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'jpeg',quality:90,chromaSubsampling:'4:4:4',slots:/^normalTexture$/}),draco({encodeSpeed:5,decodeSpeed:8,quantizePosition:16,quantizeNormal:10,quantizeTexcoord:14}));
await output(base+'/mobile-v27/nobi-home-v27.glb',mobile);
// Patch only the house's static colliders; use a new metadata URL so cached v26
// engines never receive v27 collision data for the v21 building.
const current=JSON.parse(await readFile(base+'/world.json','utf8'));
const old=JSON.parse(execFileSync('git',['show',snapshot+':'+base+'/world.json'],{maxBuffer:20*1024*1024}));
const kept=current.colliders.filter(c=>!c.group.startsWith('v11_home_'));
const restored=old.colliders.filter(c=>c.group.startsWith('home_')||c.group==='furniture_ground');
for(const c of restored)if(c.group==='home_stairs'){const end=c.y+c.d/2;c.y=(1.75+end)/2;c.d=end-1.75;}
const data={...current,colliders:[...kept,...restored],actors:{...current.actors,actor_tamako:[current.actors.actor_tamako[0],6.05,current.actors.actor_tamako[2]]},stairs:{x:-13.05,y0:1.2,y1:4.8,width:.82,steps:16,rise:(3.15-.48)/16},houseRevision:{nobita:'original-v10-restored27',source:snapshot,bedroom:'bedroom-v12',otherHouses:'neighborhood-v21'}};
// Some historical exports encode actors as an array. Preserve that schema.
if(Array.isArray(current.actors))data.actors=current.actors.map(a=>a.id==='tamako'?{...a,y:6.05}:a);
await writeFile(base+'/world-v27.json',JSON.stringify(data));
report.colliders={unaffected:kept.length,removed:current.colliders.length-kept.length,restored:restored.length};
const evidence='docs/evidence/nobi-rollback27';await mkdir(evidence,{recursive:true});await writeFile(evidence+'/assets.json',JSON.stringify(report,null,2)+'\n');
