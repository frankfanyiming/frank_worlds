import * as THREE from 'three';

const groundPattern=/V7_Turf|V7_Soil|V7_Asphalt|GardenTurf_PBR|GardenSoil_PBR|LotTransition|weathered asphalt/;
const groundSampling=`
vec2 groundHash(vec2 p){return fract(sin(vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3))))*43758.5453)*17.43;}
vec4 groundTexture(sampler2D tex,vec2 uv){
 vec2 cell=floor(uv*.31),f=fract(uv*.31);f=f*f*(3.-2.*f);
 vec4 a=texture2D(tex,uv+groundHash(cell));
 vec4 b=texture2D(tex,uv+groundHash(cell+vec2(1.,0.)));
 vec4 c=texture2D(tex,uv+groundHash(cell+vec2(0.,1.)));
 vec4 d=texture2D(tex,uv+groundHash(cell+vec2(1.,1.)));
 return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}`;

// A single world-space breeze drives the visible foliage and its shadow pass.
// Weight comes from distance along each modeled blade, keeping the root fixed.
export class TownAtmosphere {
 time={value:0};strength={value:1};seasonAmount={value:0};materials=new Set<THREE.Material>();windMeshes=0;
 install(mesh:THREE.Mesh){
  const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  const foliage=mats.some(m=>/BotanicalLeaf|Hydrangea|GrassBlade|Moss|V10_WhiteClover/.test(m.name));
  const ground=mats.some(m=>groundPattern.test(m.name));
  if(!foliage&&!ground)return;
  const g=mesh.geometry,uv=g.getAttribute('uv'),position=g.getAttribute('position');
  const modeledWeight=g.getAttribute('_wind_weight')??g.getAttribute('_WIND_WEIGHT');
  if(foliage&&!g.getAttribute('windWeight')){
   const weights=new Float32Array(position.count);let material=mats[0];
   const classify=(m:THREE.Material,i:number)=>{
    if(modeledWeight)return Math.max(0,Math.min(1,modeledWeight.getX(i)))*.012;
    const v=uv?1-uv.getY(i):0;
    if(/GrassBlade/.test(m.name))return Math.max(0,Math.min(1,v))**1.65*.028;
    if(/BotanicalLeaf/.test(m.name)){const t=Math.max(0,Math.min(1,((v% .5)-.008)/.484));return t*t*.025;}
    if(/Hydrangea|Moss/.test(m.name))return .008;
    return 0;
   };
   if(g.groups.length){for(const group of g.groups){material=mats[group.materialIndex??0]??mats[0];for(let j=group.start;j<group.start+group.count;j++){const i=g.index?g.index.getX(j):j;weights[i]=classify(material,i);}}}
   else for(let i=0;i<position.count;i++)weights[i]=classify(material,i);
   g.setAttribute('windWeight',new THREE.BufferAttribute(weights,1));this.windMeshes++;
  }
  const deform=(shader:THREE.WebGLProgramParametersWithUniforms)=>{
   shader.uniforms.breezeTime=this.time;shader.uniforms.breezeStrength=this.strength;
   shader.vertexShader='uniform float breezeTime; uniform float breezeStrength; attribute float windWeight;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
    vec3 wpos=(modelMatrix*vec4(position,1.0)).xyz;
    float gust=0.60+0.40*sin(breezeTime*.68+wpos.x*.31+wpos.z*.27);
    float bend=sin(breezeTime*2.1+wpos.x*.77+wpos.z*.49)*gust;
    vec3 drift=vec3(bend,0.12*sin(breezeTime*2.7+wpos.x),bend*.53)*windWeight*breezeStrength;
    transformed+=transpose(mat3(modelMatrix))*drift;
   `);
  };
  for(const m of mats){
   if(this.materials.has(m))continue;this.materials.add(m);
   if(!(m instanceof THREE.MeshStandardMaterial))continue;
   if(/BotanicalLeaf/.test(m.name)){m.roughness=.85;m.envMapIntensity=.16;if(m instanceof THREE.MeshPhysicalMaterial)m.transmission=0;}
   m.onBeforeCompile=shader=>{
    if(/BotanicalLeaf/.test(m.name)){
     shader.uniforms.seasonAmount=this.seasonAmount;
     shader.fragmentShader='uniform float seasonAmount;\n'+shader.fragmentShader;
     shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
      float deciduous=step(.5,fract(vMapUv.x))*(1.0-step(.5,fract(vMapUv.y)));
      float leafLight=dot(diffuseColor.rgb,vec3(.3,.59,.11));
      diffuseColor.rgb*=gl_FrontFacing?1.0:1.13;
      diffuseColor.rgb=mix(diffuseColor.rgb,leafLight*vec3(1.8,.74,.20),deciduous*seasonAmount);
     `);
    }
    if(foliage)deform(shader);
    if(groundPattern.test(m.name)){
     // Crossfade hashed offsets in every PBR channel together. Adjacent cells
     // share the same corner samples, eliminating a visible tile/grid boundary.
     shader.fragmentShader=groundSampling+'\n'+shader.fragmentShader;
     for(const [chunk,sampler,uv] of [['map_fragment','map','vMapUv'],['normal_fragment_maps','normalMap','vNormalMapUv'],['roughnessmap_fragment','roughnessMap','vRoughnessMapUv']] as const){
      const source=THREE.ShaderChunk[chunk].replaceAll(`texture2D( ${sampler}, ${uv} )`,`groundTexture( ${sampler}, ${uv} )`);
      shader.fragmentShader=shader.fragmentShader.replace(`#include <${chunk}>`,source);
     }
     shader.vertexShader='varying vec3 groundWorld;\n'+shader.vertexShader;
     shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ngroundWorld=(modelMatrix*vec4(position,1.)).xyz;');
     shader.fragmentShader='varying vec3 groundWorld;\n'+shader.fragmentShader;
     shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
      float broad=sin(groundWorld.x*.71+sin(groundWorld.z*.38))*sin(groundWorld.z*.61+sin(groundWorld.x*.24));
      float fine=sin(groundWorld.x*3.18+groundWorld.z*2.71)*sin(groundWorld.z*2.03-groundWorld.x*1.28);
      diffuseColor.rgb*=1.0+broad*.105+fine*.035;
     `);
    }
   };
   m.customProgramCacheKey=()=>`town-v7-${foliage?'breeze':'static'}-${groundPattern.test(m.name)?'stochastic-ground':'foliage'}-${/BotanicalLeaf/.test(m.name)?'season-leaf':'base'}`;m.needsUpdate=true;
  }
  if(foliage){
   const depth=new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking,side:THREE.DoubleSide});depth.onBeforeCompile=deform;depth.customProgramCacheKey=()=> 'town-v6-breeze-depth';mesh.customDepthMaterial=depth;
   const distance=new THREE.MeshDistanceMaterial({side:THREE.DoubleSide});distance.onBeforeCompile=deform;distance.customProgramCacheKey=()=> 'town-v6-breeze-distance';mesh.customDistanceMaterial=distance;
   const surface=mats[0];
   if(surface instanceof THREE.MeshStandardMaterial&&surface.alphaTest>0){for(const pass of [depth,distance]){pass.map=surface.map;pass.alphaMap=surface.alphaMap;pass.alphaTest=surface.alphaTest;}}
  }
 }
 update(elapsed:number){this.time.value=elapsed;}
}
