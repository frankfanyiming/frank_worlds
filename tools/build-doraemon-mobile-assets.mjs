// Reproducible derivatives only; never overwrite desktop GLBs or source maps.
// Tool versions and source/result hashes are written into the output report.
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const toolRoot=process.env.MOBILE_ASSET_TOOLS||resolve('tools/mobile-assets');
const require=createRequire(resolve(toolRoot,'package.json'));
const imp=n=>import(pathToFileURL(require.resolve(n)).href);
const {NodeIO,PropertyType}=await imp('@gltf-transform/core');
const {ALL_EXTENSIONS}=await imp('@gltf-transform/extensions');
const {weld,simplifyPrimitive,prune,dedup,textureCompress,draco}=await imp('@gltf-transform/functions');
const {MeshoptSimplifier}=await imp('meshoptimizer');
const sharp=require('sharp'),draco3d=require('draco3dgltf');
sharp.concurrency(2);await MeshoptSimplifier.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco3d.createDecoderModule(),'draco3d.encoder':await draco3d.createEncoderModule()});
const root=resolve('worlds/doraemon/web/public'),sourceMaps=resolve(root,'bedroom-materials'),destMaps=resolve(sourceMaps,'mobile-v23');
const sourceManifest=JSON.parse(await readFile(resolve(sourceMaps,'manifest.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={version:'20260913-mobile23',tools:Object.fromEntries(await Promise.all(Object.keys(JSON.parse(await readFile(resolve(toolRoot,'package.json'),'utf8')).dependencies).map(async name=>[name,JSON.parse(await readFile(resolve(toolRoot,'node_modules',name,'package.json'),'utf8')).version]))),models:[],textures:[]};
const manifest={...sourceManifest,scans:{},materials:{},files:[],mobile:true};
await mkdir(destMaps,{recursive:true});
async function emitMap(file,pipeline,sources){
 const data=await pipeline.toBuffer();const meta=await sharp(data).metadata();const path=resolve(destMaps,file);await mkdir(dirname(path),{recursive:true});await writeFile(path,data);
 const item={file,bytes:data.length,width:meta.width,height:meta.height,sha256:sha(data)};
 manifest.files.push(item);report.textures.push({...item,sources:await Promise.all(sources.map(async p=>{const b=await readFile(resolve(sourceMaps,p));return{file:p,sha256:sha(b),bytes:b.length};}))});return{file};
}
// Albedo remains 1K; fine normal and roughness data are band-limited to 512px.
// AO and roughness share one RGB texture, sampled by standard glTF channels R/G.
for(const section of ['scans','materials'])for(const [name,item]of Object.entries(sourceManifest[section])){
 const maps={},prefix=section+'/'+name;
 for(const channel of ['albedo','normal'])if(item.maps[channel]){
  // Linen intentionally takes its colour from the authored green/blue canvas.
  // The historical manifest lists a scan albedo that the game never requests.
  if(section==='scans'&&name==='rough_linen'&&channel==='albedo')continue;
  const file=item.maps[channel].file,pipeline=sharp(resolve(sourceMaps,file)).resize(channel==='albedo'?1024:512,channel==='albedo'?1024:512,{fit:'inside',withoutEnlargement:true,kernel:'lanczos3'});
  maps[channel]=await emitMap(prefix+'/'+channel+(channel==='normal'?'.png':'.webp'),channel==='normal'?pipeline.png({compressionLevel:9}):pipeline.webp({quality:88,alphaQuality:100}),[file]);
 }
 if(item.maps.roughness||item.maps.ao){
  const ref=item.maps.roughness??item.maps.ao,meta=await sharp(resolve(sourceMaps,ref.file)).metadata();const w=Math.min(512,meta.width),h=Math.max(1,Math.round(meta.height*w/meta.width));
  const read=async(channel,fallback)=>item.maps[channel]?sharp(resolve(sourceMaps,item.maps[channel].file)).resize(w,h,{kernel:'lanczos3'}).removeAlpha().greyscale().raw().toBuffer():Buffer.alloc(w*h,fallback);
  const [ao,rough]=await Promise.all([read('ao',255),read('roughness',255)]),rgb=Buffer.alloc(w*h*3,255);
  for(let i=0;i<w*h;i++){rgb[i*3]=ao[i];rgb[i*3+1]=rough[i];}
  const info=await emitMap(prefix+'/orm.webp',sharp(rgb,{raw:{width:w,height:h,channels:3}}).webp({quality:92}),['ao','roughness'].filter(c=>item.maps[c]).map(c=>item.maps[c].file));
  if(item.maps.ao)maps.ao=info;if(item.maps.roughness)maps.roughness=info;
 }
 manifest[section][name]={...item,maps};
}
await writeFile(resolve(destMaps,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
const desktopManifest=await readFile(resolve(root,'../lib/town/model-manifest.ts'),'utf8');
// Evaluate only the literal curated part list, not arbitrary project source.
const literal=desktopManifest.match(/MODEL_PARTS: string\[\] = (\[.*?\]);/s)?.[1];
if(!literal||!/\['world-v11'/.test(literal))throw Error('Review changed model manifest before rebuilding');
const parts=Function('return '+literal)().filter(p=>!['actors/','fauna/','vehicles/','gadgets/'].some(prefix=>p.startsWith(prefix)));
const restores=name=>Object.values(sourceManifest.materials).some(v=>v.replace_source_materials.includes(name))||/walnut|oak/i.test(name)||['V10_Plaster','Plaster','WashiUV','V10_GreenLinen','V10_BlueLinen','V10_Canvas','V10_Cedar','V10_Tatami','V10_Desktop','V10_Drawer','Timber.001','F7_Wood'].includes(name);
const counts=doc=>({triangles:doc.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().reduce((s,p)=>s+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0),0),primitives:doc.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().length,0),nodes:doc.getRoot().listNodes().length,textures:doc.getRoot().listTextures().length});
function spatialChunks(doc){
 let chunks=0;
 for(const node of [...doc.getRoot().listNodes()]){
  const mesh=node.getMesh();if(!mesh||node.getSkin())continue;
  const matrix=node.getWorldMatrix(),xAt=(a,i)=>matrix[0]*a[i]+matrix[4]*a[i+1]+matrix[8]*a[i+2]+matrix[12],zAt=(a,i)=>matrix[2]*a[i]+matrix[6]*a[i+1]+matrix[10]*a[i+2]+matrix[14];
  let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity,total=0;
  for(const p of mesh.listPrimitives()){const a=p.getAttribute('POSITION').getArray();total+=(p.getIndices()?.getCount()??a.length/3)/3;for(let i=0;i<a.length;i+=3){const x=xAt(a,i),z=zAt(a,i);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minZ=Math.min(minZ,z);maxZ=Math.max(maxZ,z);}}
  if(total<12000||Math.max(maxX-minX,maxZ-minZ)<25)continue;
  const cells=new Map();
  for(const p of mesh.listPrimitives()){
   if(p.getMode()!==4)throw Error('Review non-triangle chunk '+node.getName());
   const a=p.getAttribute('POSITION').getArray(),indices=p.getIndices()?.getArray()??Uint32Array.from({length:a.length/3},(_,i)=>i),buckets=new Map();
   for(let i=0;i<indices.length;i+=3){let x=0,z=0;for(let k=0;k<3;k++){x+=xAt(a,indices[i+k]*3);z+=zAt(a,indices[i+k]*3);}const key=Math.floor(x/3/24)+','+Math.floor(z/3/24);const ids=buckets.get(key)??[];ids.push(indices[i],indices[i+1],indices[i+2]);buckets.set(key,ids);}
   for(const [key,ids]of buckets){
    const copy=p.clone(),map=new Map(),vertices=[],local=new Uint32Array(ids.length);
    ids.forEach((id,i)=>{if(!map.has(id)){map.set(id,vertices.length);vertices.push(id);}local[i]=map.get(id);});
    copy.setIndices(doc.createAccessor().setType('SCALAR').setBuffer(doc.getRoot().listBuffers()[0]).setArray(local));
    for(const semantic of p.listSemantics()){
     const accessor=p.getAttribute(semantic),src=accessor.getArray(),stride=accessor.getElementSize(),dst=new src.constructor(vertices.length*stride);
     vertices.forEach((id,i)=>dst.set(src.subarray(id*stride,(id+1)*stride),i*stride));copy.setAttribute(semantic,accessor.clone().setArray(dst));
    }
    let child=cells.get(key);if(!child){child=doc.createMesh(mesh.getName()+' cell '+key);cells.set(key,child);}child.addPrimitive(copy);
   }
  }
  node.setMesh(null);
  for(const [key,mesh]of cells){node.addChild(doc.createNode(node.getName()+' cell '+key).setMesh(mesh));chunks++;}
 }
 return chunks;
}
for(const part of parts){
 const src=resolve(root,'models/'+part+'.glb'),dst=resolve(root,'models/mobile-v23/'+part+'.glb'),original=await readFile(src),doc=await io.read(src),before=counts(doc);
 const originalNodes=[...doc.getRoot().listNodes()],nodeContract=originalNodes.map(n=>({name:n.getName(),matrix:n.getMatrix()}));
 if(part==='bedroom-v12')for(const m of doc.getRoot().listMaterials())if(restores(m.getName())){m.setBaseColorTexture(null).setNormalTexture(null).setMetallicRoughnessTexture(null).setOcclusionTexture(null);}
 // Mobile uses standard surfaces; refraction's full-scene replay is too costly.
 for(const ext of doc.getRoot().listExtensionsUsed())if(/^KHR_materials_(clearcoat|transmission|volume|ior|specular|sheen|anisotropy)$/.test(ext.extensionName))ext.dispose();
 await doc.transform(weld());
 for(const mesh of doc.getRoot().listMeshes())for(const primitive of mesh.listPrimitives()){
  const pos=primitive.getAttribute('POSITION'),a=pos.getArray();let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<a.length;i++) {const d=i%3;lo[d]=Math.min(lo[d],a[i]);hi[d]=Math.max(hi[d],a[i]);}
  const extent=Math.max(...hi.map((v,i)=>v-lo[i]),.01);
  const botanical=/Botanical|Hydrangea|GrassBlade|Moss|FallenLeaf/.test(primitive.getMaterial()?.getName()??'');
  simplifyPrimitive(primitive,{simplifier:MeshoptSimplifier,ratio:botanical?.12:part==='bedroom-v12'?.24:.40,error:botanical?Math.min(.012,.012/extent):Math.min(.001,.003/extent),lockBorder:!botanical&&/terrain|surface|streets|connector/.test(part)});
 }
 const chunks=part==='bedroom-v12'?0:spatialChunks(doc);
 await doc.transform(prune({keepLeaves:true,keepAttributes:true,keepSolidTextures:true}),dedup({propertyTypes:[PropertyType.TEXTURE,PropertyType.ACCESSOR]}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'webp',quality:86,slots:/^(?!normalTexture).*$/}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'jpeg',quality:90,chromaSubsampling:'4:4:4',slots:/^normalTexture$/}),draco({encodeSpeed:5,decodeSpeed:8,quantizePosition:16,quantizeNormal:10,quantizeTexcoord:14}));
 const afterContract=originalNodes.map(n=>({name:n.getName(),matrix:n.getMatrix()}));
 if(JSON.stringify(nodeContract)!==JSON.stringify(afterContract))throw Error('Node hierarchy/placement changed: '+part);
 await mkdir(dirname(dst),{recursive:true});await io.write(dst,doc);const output=await readFile(dst);
 const record={part,before:{...before,bytes:original.length,sha256:sha(original)},after:{...counts(doc),bytes:output.length,sha256:sha(output)},spatialChunks:chunks,nodeTransformsUnchanged:true};report.models.push(record);console.log(JSON.stringify(record));
}
const evidence=resolve('docs/evidence/mobile-revision23');await mkdir(evidence,{recursive:true});
await writeFile(resolve(evidence,'mobile-assets.json'),JSON.stringify(report,null,2)+'\n');
console.log('MOBILE ASSETS READY',report.models.length,'models',report.textures.length,'maps');
