// Real decoded model intersections; this runs without WebGL or a browser.
import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import {resolve} from 'node:path';import {writeFile} from 'node:fs/promises';import assert from 'node:assert/strict';
const require=createRequire(resolve(process.env.MOBILE_ASSET_TOOLS||'tools/mobile-assets','package.json'));const webRequire=createRequire(resolve('worlds/doraemon/web/package.json'));
const {NodeIO}=await import(pathToFileURL(require.resolve('@gltf-transform/core')));const {ALL_EXTENSIONS}=await import(pathToFileURL(require.resolve('@gltf-transform/extensions')));const THREE=webRequire('three');const draco=require('draco3dgltf');const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco.createDecoderModule()});const report=[];
for(const profile of ['desktop','mobile']){
 const doc=await io.read('worlds/doraemon/web/public/models/'+(profile==='mobile'?'mobile-v27/':'')+'nobi-home-v27.glb'),group=new THREE.Group();
 for(const node of doc.getRoot().listNodes())if(node.getMesh())for(const p of node.getMesh().listPrimitives()){
  const geometry=new THREE.BufferGeometry().setAttribute('position',new THREE.BufferAttribute(p.getAttribute('POSITION').getArray(),3)).setIndex(new THREE.BufferAttribute(p.getIndices().getArray(),1));
  const mesh=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({side:THREE.DoubleSide}));mesh.name=node.getName();mesh.matrix.fromArray(node.getWorldMatrix());mesh.matrixAutoUpdate=false;group.add(mesh);
 }
 group.updateMatrixWorld(true);let probes=0;
 for(const y of [1.18,1.30,1.42])for(const height of [.92,1.25,1.72]){
  const ray=new THREE.Raycaster(new THREE.Vector3(-12.35,height,-y),new THREE.Vector3(-1,0,0),0,1.40);const hits=ray.intersectObjects(group.children);assert.equal(hits.length,0,JSON.stringify({profile,y,height,hits:hits.map(h=>({node:h.object.name,d:h.distance}))}));probes++;
 }
 report.push({profile,clearanceProbes:probes,passed:true});group.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
}
await writeFile('docs/evidence/nobi-rollback27/clearance.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: living-room access is clear in both decoded model files (18 ray probes)');
