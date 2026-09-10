import * as THREE from 'three';
import {ASSET_VERSION} from './model-manifest';
import {assetPath} from './asset-path';
import {boundedMap,fetchBytes,withDeadline,evictCachedAsset} from './loading';
type Finish={scan?:string;family?:string;scale?:[number,number];tint?:[number,number,number];depth?:number;projection?:boolean;cloth?:boolean;rotate?:boolean};
type MapInfo={file:string};
type Manifest={scans:Record<string,{maps:Record<string,MapInfo>}>;materials:Record<string,{replace_source_materials:string[];maps:Record<string,MapInfo>}>};
function finish(key:string):Finish|undefined{
 if(['V10_Plaster','Plaster','WashiUV'].includes(key))return{scan:'painted_plaster_wall',projection:true,tint:[1.16,1.05,.84],depth:.8};
 if(['V10_GreenLinen','V10_BlueLinen','V10_Canvas'].includes(key))return{scan:'rough_linen',cloth:true,scale:[.08/.271,.08/.271],depth:1};
 if(key==='V10_Cedar')return{scan:'japanese_cedar_planks',scale:[.35/1.13,1.2/1.13],tint:[.66,.83,1],depth:.55};
 if(key==='V10_Tatami')return{scan:'tatami_mat',tint:[1.18,1.27,.76],depth:1.1};
 if(['V10_Desktop','V10_Drawer'].includes(key))return{scan:'oak_veneer_02',scale:key==='V10_Desktop'?[.6,1.18]:[.168,.306],tint:key==='V10_Desktop'?[.9,.75,.57]:[.76,.59,.37],depth:.65,rotate:true};
 if(/walnut|oak/i.test(key)||['Timber.001','F7_Wood'].includes(key)){const walnut=/walnut/i.test(key);return{scan:walnut?'fine_grained_wood':'oak_veneer_02',scale:walnut?[.35/.6,1.2/.6]:[.35,1.2],tint:walnut?[1.15,1.12,1.05]:[.85,.77,.65],depth:.4,rotate:!walnut};}
}
// Equivalent to the accepted room's separate straw/binding shader. The scan
// contains two mats: sample their straw without painting another border on top.
function tatamiShader(mat:THREE.MeshStandardMaterial){
 mat.onBeforeCompile=shader=>{
  shader.fragmentShader=`vec4 roomWeave(sampler2D tex,vec2 baseUv){vec2 q=baseUv*vec2(.1,.2380952381);float odd=mod(floor(q.y),2.);float fy=mix(fract(q.y),1.-fract(q.y),odd);vec2 uv=vec2(fract(q.x),.04+.42*fy);return textureGrad(tex,uv,dFdx(q)*vec2(1.,.42*(1.-2.*odd)),dFdy(q)*vec2(1.,.42*(1.-2.*odd)));}\n`+shader.fragmentShader;
  for(const [chunk,sampler,uv] of [['map_fragment','map','vMapUv'],['normal_fragment_maps','normalMap','vNormalMapUv'],['roughnessmap_fragment','roughnessMap','vRoughnessMapUv'],['aomap_fragment','aoMap','vAoMapUv']] as const){
   let code=THREE.ShaderChunk[chunk].replaceAll(`texture2D( ${sampler}, ${uv} )`,`roomWeave( ${sampler}, ${uv} )`);
   if(chunk==='normal_fragment_maps')code=code.replace('mapN.xy *= normalScale;','mapN.y *= 1. - 2. * mod(floor(vNormalMapUv.y * .2380952381), 2.);\nmapN.xy *= normalScale;');
   shader.fragmentShader=shader.fragmentShader.replace(`#include <${chunk}>`,code);
  }
 };
 mat.customProgramCacheKey=()=> 'accepted-room-weave-v12';
}
export async function restoreBedroomMaterials(room:THREE.Object3D,signal:AbortSignal,anisotropy:number,onProgress:(fraction:number)=>void=()=>{}){
 const manifestUrl=assetPath('/bedroom-materials/manifest.json?v='+ASSET_VERSION);let manifest:Manifest;
 try{const bytes=await fetchBytes(manifestUrl,signal);manifest=JSON.parse(new TextDecoder().decode(bytes)) as Manifest;if(!manifest.scans||!manifest.materials)throw new Error('房间材质清单不完整');}catch(e){if(!signal.aborted)await evictCachedAsset(manifestUrl);throw e;}
 const mats=new Set<THREE.MeshStandardMaterial>();room.traverse(o=>{if(o instanceof THREE.Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m instanceof THREE.MeshStandardMaterial)mats.add(m);});
 const assignments=new Map<THREE.MeshStandardMaterial,Finish>();const wanted=new Map<string,boolean>();
 for(const m of mats){const config=finish(m.name)??{};config.family=Object.keys(manifest.materials).find(k=>manifest.materials[k].replace_source_materials.includes(m.name));assignments.set(m,config);
  if(config.family)for(const [channel,info]of Object.entries(manifest.materials[config.family].maps))if(!config.scan||(config.cloth&&channel==='albedo'))wanted.set(info.file,channel==='albedo');
  if(config.scan)for(const [channel,info]of Object.entries(manifest.scans[config.scan].maps))if(!config.cloth||channel!=='albedo')wanted.set(info.file,channel==='albedo');
 }
 let complete=0;const textures=new Map<string,THREE.Texture>(),local=new AbortController();
 const abort=()=>local.abort();signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();
 try{await boundedMap([...wanted],3,async([file,srgb])=>{
  const path=assetPath('/bedroom-materials/'+file+'?v='+ASSET_VERSION);
  try{
   const data=await fetchBytes(path,local.signal);local.signal.throwIfAborted();const url=URL.createObjectURL(new Blob([data]));
   try{
    let t:THREE.Texture;try{t=await withDeadline(new THREE.TextureLoader().loadAsync(url).then(t=>{if(local.signal.aborted){t.dispose();local.signal.throwIfAborted();}return t;}),45000,'房间材质解码');}catch(e){if(!local.signal.aborted)await evictCachedAsset(path);throw e;}
    t.flipY=false;t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.NoColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=anisotropy;textures.set(file,t);onProgress(++complete/wanted.size);
   }finally{URL.revokeObjectURL(url);}
  }catch(e){local.abort();throw e;}
 });}catch(e){local.abort();for(const t of textures.values())t.dispose();throw e;}finally{signal.removeEventListener('abort',abort);}
 const original=new Set<THREE.Texture>();for(const m of mats)for(const t of [m.map,m.normalMap,m.roughnessMap,m.aoMap])if(t)original.add(t);
 for(const [m,c]of assignments){
  const apply=(maps:Record<string,MapInfo>,cloth=false)=>{for(const [channel,key]of [['albedo','map'],['normal','normalMap'],['roughness','roughnessMap'],['ao','aoMap']] as const){if(cloth&&channel==='albedo')continue;const t=textures.get(maps[channel]?.file);if(!t)continue;const copy=t.clone();copy.channel=0;if(c.scale){if(c.rotate){copy.matrixAutoUpdate=false;copy.matrix.set(0,c.scale[1],0,c.scale[0],0,0,0,0,1);}else copy.repeat.set(...c.scale);}m[key]=copy;}};
  if(c.family){apply(manifest.materials[c.family].maps);m.color.setRGB(1,1,1);m.normalScale.setScalar(1);m.roughness=1;m.metalness=0;}
  if(c.scan){apply(manifest.scans[c.scan].maps,c.cloth);if(c.tint)m.color.setRGB(...c.tint,THREE.SRGBColorSpace);m.normalScale.setScalar(c.depth??1);m.roughness=1;m.metalness=0;m.metalnessMap=null;m.aoMapIntensity=.8;}
  if(m instanceof THREE.MeshPhysicalMaterial&&(c.scan||c.family)){m.clearcoat=0;m.specularIntensity=c.cloth?.23:.4;m.sheen=c.cloth?.08:0;}
  if(m.name==='V10_GreenLinen')m.color.set('#a5ae86');if(m.name==='V10_BlueLinen')m.color.setRGB(1.25,1.32,1.13);
  if(m.name==='V10_Tatami')tatamiShader(m);
  if(/glass/i.test(m.name)){m.transparent=true;m.opacity=.10;m.roughness=.14;m.metalness=0;m.depthWrite=false;}
  m.needsUpdate=true;
 }
 room.updateMatrixWorld(true);room.traverse(o=>{if(!(o instanceof THREE.Mesh))return;const m=Array.isArray(o.material)?o.material[0]:o.material;if(!(m instanceof THREE.MeshStandardMaterial))return;
  if(/glass/i.test(m.name)){o.castShadow=false;}
  if(assignments.get(m)?.projection){const g=o.geometry.clone(),pos=g.getAttribute('position'),normal=g.getAttribute('normal'),uv=new Float32Array(pos.count*2),v=new THREE.Vector3();for(let i=0;i<pos.count;i++){v.fromBufferAttribute(pos,i).applyMatrix4(o.matrixWorld);const x=Math.abs(normal.getX(i)),y=Math.abs(normal.getY(i)),z=Math.abs(normal.getZ(i));uv[i*2]=(x>y&&x>z?v.z:v.x)/2;uv[i*2+1]=(y>x&&y>z?v.z:v.y)/2;}g.setAttribute('uv',new THREE.BufferAttribute(uv,2));g.deleteAttribute('tangent');o.geometry=g;}
 });
 const used=new Set<THREE.Texture>();for(const m of mats)for(const t of [m.map,m.normalMap,m.roughnessMap,m.aoMap])if(t)used.add(t);for(const t of original)if(!used.has(t))t.dispose();
 return{materials:[...mats].filter(m=>assignments.get(m)?.scan||assignments.get(m)?.family).length,textures:textures.size};
}
