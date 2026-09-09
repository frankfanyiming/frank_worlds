import * as THREE from 'three';

export class TownWater {
 time={value:0};surfaces=0;
 install(mesh:THREE.Mesh){
  if(!/River_Water_Surface/.test(mesh.name))return;
  this.surfaces++;
  const material=new THREE.MeshPhysicalMaterial({name:'River flowing water',color:'#417e83',roughness:.22,metalness:.08,clearcoat:.6,clearcoatRoughness:.17,envMapIntensity:.65});
  mesh.material=material;mesh.castShadow=false;mesh.receiveShadow=true;
  material.onBeforeCompile=shader=>{
   shader.uniforms.riverTime=this.time;
   shader.vertexShader='uniform float riverTime; varying vec3 riverWorld;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
    riverWorld=(modelMatrix*vec4(position,1.)).xyz;
    float wave=.014*sin(riverWorld.x*1.7+riverWorld.z*2.4-riverTime*1.5)+.007*sin(riverWorld.x*3.6-riverWorld.z*1.3+riverTime*.9);
    transformed+=transpose(mat3(modelMatrix))*vec3(0.,wave,0.);
   `);
   shader.fragmentShader='uniform float riverTime; varying vec3 riverWorld;\n'+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
    float a=riverWorld.x*1.7+riverWorld.z*2.4-riverTime*1.5;
    float b=riverWorld.x*3.6-riverWorld.z*1.3+riverTime*.9;
    vec3 ripples=normalize(vec3(-.0238*cos(a)-.0252*cos(b),1.,-.0336*cos(a)+.0091*cos(b)));
    normal=normalize((viewMatrix*vec4(ripples,0.)).xyz);
   `);
   shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
    float current=sin(riverWorld.x*2.3+sin(riverWorld.z*1.9-riverTime*.7)+riverTime*.24);
    float glint=pow(max(0.,current),16.)*.10;
    diffuseColor.rgb*=.93+current*.07;
    diffuseColor.rgb+=vec3(.12,.20,.18)*glint;
   `);
  };
  material.customProgramCacheKey=()=> 'river-v9-world-ripples';
 }
 update(elapsed:number){this.time.value=elapsed;}
}
