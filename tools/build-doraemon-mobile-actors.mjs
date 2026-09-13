// Mobile visual derivatives only; collision routes and desktop assets stay intact.
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const req=createRequire(resolve(process.env.MOBILE_ASSET_TOOLS||'tools/mobile-assets','package.json'));
const imp=n=>import(pathToFileURL(req.resolve(n)).href);
const {NodeIO}=await imp('@gltf-transform/core'),{ALL_EXTENSIONS}=await imp('@gltf-transform/extensions');
const {weldPrimitive,simplifyPrimitive,prune,textureCompress,draco}=await imp('@gltf-transform/functions');
const {MeshoptSimplifier}=await imp('meshoptimizer');await MeshoptSimplifier.ready;
const sharp=req('sharp'),draco3d=req('draco3dgltf');sharp.concurrency(2);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco3d.createDecoderModule(),'draco3d.encoder':await draco3d.createEncoderModule()});
const root=resolve('worlds/doraemon/web/public/models');
const parts=[...['nobita','doraemon-v11','shizuka','gian','suneo','tamako','nobisuke'].map(n=>'actors/'+n),...['cat','sparrow','sparrow_ash'].map(n=>'fauna/'+n),...['kei_hatchback-v11','kei_truck-v11'].map(n=>'vehicles/'+n)];
const sha=b=>createHash('sha256').update(b).digest('hex');
const data=a=>a?sha(Buffer.from(a.getArray().buffer,a.getArray().byteOffset,a.getArray().byteLength)):null;
const contract=doc=>JSON.stringify({nodes:doc.getRoot().listNodes().map(n=>[n.getName(),n.getMatrix(),n.listChildren().map(c=>c.getName())]),skins:doc.getRoot().listSkins().map(s=>[s.listJoints().map(n=>n.getName()),data(s.getInverseBindMatrices())]),animations:doc.getRoot().listAnimations().map(a=>[a.getName(),a.listSamplers().map(s=>[data(s.getInput()),data(s.getOutput()),s.getInterpolation()])])});
const triangles=doc=>doc.getRoot().listMeshes().reduce((n,m)=>n+m.listPrimitives().reduce((n,p)=>n+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0),0);
const report=[];
for(const part of parts){
 const src=resolve(root,part+'.glb'),dst=resolve(root,'mobile-v24',part+'.glb'),original=await readFile(src),doc=await io.read(src),before=triangles(doc),saved=contract(doc);
 for(const m of doc.getRoot().listMeshes())for(const p of m.listPrimitives())if(p.getMode()===4&&(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())>1200){
  weldPrimitive(p);simplifyPrimitive(p,{simplifier:MeshoptSimplifier,ratio:.35,error:.0025,lockBorder:false});
 }
 await doc.transform(prune({keepLeaves:true,keepAttributes:true,keepSolidTextures:true}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'webp',quality:88,slots:/^(?!normalTexture).*$/}),textureCompress({encoder:sharp,resize:[512,512],targetFormat:'jpeg',quality:92,chromaSubsampling:'4:4:4',slots:/^normalTexture$/}));
 if(saved!==contract(doc))throw Error('Animation, skeleton or transform changed: '+part);
 await doc.transform(draco({encodeSpeed:5,decodeSpeed:8,quantizePosition:16,quantizeNormal:10,quantizeTexcoord:14}));
 await mkdir(dirname(dst),{recursive:true});await io.write(dst,doc);const output=await readFile(dst);
 report.push({part,before:{triangles:before,bytes:original.length,sha256:sha(original)},after:{triangles:triangles(doc),bytes:output.length,sha256:sha(output)},animationSkeletonAndTransformsUnchanged:true});console.log(part,before,'->',triangles(doc));
}
await writeFile('docs/evidence/performance-revision24/doraemon-mobile-actors.json',JSON.stringify(report,null,2)+'\n');
