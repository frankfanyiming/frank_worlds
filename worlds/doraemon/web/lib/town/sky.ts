import * as THREE from 'three';
import {Sky} from 'three/addons/objects/Sky.js';

// Atmospheric scattering and a slowly advecting, layered cloud field. The dome
// follows the eye, so clouds remain in the sky when walking through the town.
export class TownSky {
 sky=new Sky(); cloud:THREE.Mesh<THREE.SphereGeometry,THREE.ShaderMaterial>;
 sun=new THREE.Vector3(-28,48,35).normalize();stars:THREE.Points;
 constructor(scene:THREE.Scene){
  this.sky.scale.setScalar(180);this.sky.frustumCulled=false;this.sky.renderOrder=-100;
  const u=this.sky.material.uniforms;u.turbidity.value=3.4;u.rayleigh.value=1.55;u.mieCoefficient.value=.0038;u.mieDirectionalG.value=.79;u.sunPosition.value.copy(this.sun);
  scene.add(this.sky);
  const material=new THREE.ShaderMaterial({side:THREE.BackSide,transparent:true,depthWrite:false,depthTest:true,
   uniforms:{time:{value:0},sunDirection:{value:this.sun.clone()},dusk:{value:0},daylight:{value:1}},
   vertexShader:`varying vec3 skyRay;
    void main(){skyRay=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);gl_Position.z=gl_Position.w;}`,
   fragmentShader:`precision highp float;
    varying vec3 skyRay;uniform float time;uniform float dusk;uniform float daylight;uniform vec3 sunDirection;
    float hash(vec3 p){p=fract(p*.3183099+vec3(.13,.37,.71));p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
    float cloudNoise(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
      return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
                 mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
    float fbm(vec3 p){float s=0.,a=.53;for(int i=0;i<5;i++){s+=a*cloudNoise(p);p=p*2.07+vec3(3.1,7.3,1.8);a*=.48;}return s;}
    void main(){
      vec3 ray=normalize(skyRay);float horizon=smoothstep(.025,.19,ray.y);
      if(horizon<.001)discard;
      vec2 wind=vec2(time*.007,time*.0025);
      vec2 q=ray.xz/max(.08,ray.y)*1.75+wind;
      float cover=fbm(vec3(q*.31,2.7));float opacity=0.;vec3 accum=vec3(0.);
      for(int i=0;i<5;i++){
        float z=float(i)*.22;vec3 p=vec3(q,z);
        float density=smoothstep(.46,.72,fbm(p)+cover*.17)*.34;
        float lightSample=fbm(p+sunDirection*.32);
        float shade=clamp(.65+(fbm(p)-lightSample)*1.3+z*.16,.44,1.);
        vec3 color=mix(vec3(.51,.61,.68),vec3(1.22,1.19,1.07),shade);
        color=mix(color,color*vec3(1.23,.82,.60),dusk*.62);
        accum+=(1.-opacity)*density*color;opacity+=(1.-opacity)*density;
      }
      float silver=pow(max(0.,dot(ray,sunDirection)),16.);
      vec3 color=accum/max(opacity,.001)+silver*.24;
      color*=mix(vec3(.04,.055,.095),vec3(1.),daylight);
      gl_FragColor=vec4(color,opacity*horizon*.92);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`});
  this.cloud=new THREE.Mesh(new THREE.SphereGeometry(160,32,20),material);this.cloud.frustumCulled=false;this.cloud.renderOrder=-99;scene.add(this.cloud);
  const starGeometry=new THREE.BufferGeometry(),positions=new Float32Array(900);
  for(let i=0;i<300;i++){const a=i*2.39996,y=.12+.86*((i*.618034)%1),r=Math.sqrt(1-y*y);positions.set([Math.cos(a)*r*150,y*150,Math.sin(a)*r*150],i*3);}
  starGeometry.setAttribute('position',new THREE.BufferAttribute(positions,3));this.stars=new THREE.Points(starGeometry,new THREE.PointsMaterial({color:'#dceaff',size:1.4,sizeAttenuation:false,transparent:true,opacity:0,depthWrite:false}));this.stars.frustumCulled=false;this.stars.renderOrder=-98;scene.add(this.stars);
 }
 setTime(hour:number,sunrise=6,sunset=18){const a=(hour-sunrise)/(sunset-sunrise)*Math.PI,elevation=hour>=sunrise&&hour<sunset?Math.sin(a):-Math.sin(((hour<sunrise?hour+24:hour)-sunset)/(24-sunset+sunrise)*Math.PI);this.sun.set(-Math.cos(a)*.8,elevation,.48).normalize();this.sky.material.uniforms.sunPosition.value.copy(this.sun);this.cloud.material.uniforms.sunDirection.value.copy(this.sun);this.cloud.material.uniforms.dusk.value=1-THREE.MathUtils.smoothstep(elevation,-.03,.4);this.cloud.material.uniforms.daylight.value=THREE.MathUtils.smoothstep(elevation,-.13,.2);(this.stars.material as THREE.PointsMaterial).opacity=1-THREE.MathUtils.smoothstep(elevation,-.2,.03);}
 setSunset(value:boolean){this.sun.set(value?-42:-28,value?22:48,35).normalize();this.sky.material.uniforms.sunPosition.value.copy(this.sun);this.sky.material.uniforms.turbidity.value=value?4.5:3.4;this.cloud.material.uniforms.sunDirection.value.copy(this.sun);this.cloud.material.uniforms.dusk.value=value?1:0;}
 update(time:number,camera:THREE.Camera){this.sky.position.copy(camera.position);this.cloud.position.copy(camera.position);this.stars.position.copy(camera.position);this.cloud.material.uniforms.time.value=time;}
 snapshot(){return{atmosphericScattering:true,cloudLayers:5,cloudTime:this.cloud.material.uniforms.time.value};}
}
