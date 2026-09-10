import * as THREE from 'three';
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
import {DAYLIGHT,type Season} from './weather';

// Broad window sources preserve a visible difference between grazing light,
// fabric folds and wood, instead of lighting every surface from a ceiling point.
export class TownInteriorLight {
 windows:{light:THREE.RectAreaLight;power:number}[]=[];
 practicals:THREE.PointLight[]=[];
 bedroomSun:THREE.SpotLight;
 constructor(scene:THREE.Scene){
  RectAreaLightUniformsLib.init();
  const sources:[string,number[],number[],number,number,number][]=[
   ['bedroom bounce',[-10.775,4.45,-5.6],[-10.775,3.85,-1.8],1.9,2.9,1.7],
   ['bedroom',[-10.775,4.55,-.52],[-10.775,3.85,-3.1],1.1,1.65,1.5],
   ['kitchen north',[-10.8,2.05,-8.2],[-10.9,1.1,-6.3],3.2,1.3,1.2],
   ['kitchen side',[-9.25,2.03,-6.35],[-11.1,1.1,-6.5],2.2,1.1,1.2],
   ['living',[-16.9,1.93,-3.6],[-14.8,.9,-3.5],3.0,1.7,1.1],
  ];
  for(const [name,p,t,power,w,h] of sources){const light=new THREE.RectAreaLight('#eef5ff',power,w,h);light.name='Window daylight '+name;light.position.fromArray(p);light.lookAt(new THREE.Vector3().fromArray(t));scene.add(light);this.windows.push({light,power});}
  this.bedroomSun=new THREE.SpotLight('#fff1db',12,5.8,Math.PI*62/180,.45,2);this.bedroomSun.position.set(-10.775,5.18,-.5);this.bedroomSun.target.position.set(-10.6,3.3,-3.8);this.bedroomSun.castShadow=true;this.bedroomSun.shadow.mapSize.set(2048,2048);this.bedroomSun.shadow.bias=-.00008;this.bedroomSun.shadow.normalBias=.003;scene.add(this.bedroomSun,this.bedroomSun.target);
  for(const p of [[-13.05,5.08,-5.75],[-12.69,2.55,-1.5],[-10.9,2.7,-6.6]]){const light=new THREE.PointLight('#ffdfb2',2.2,4.2,2);light.position.fromArray(p);scene.add(light);this.practicals.push(light);}
 }
 update(hour:number,season:Season){const [rise,set]=DAYLIGHT[season];const elevation=hour>=rise&&hour<set?Math.sin((hour-rise)/(set-rise)*Math.PI):-1;const day=THREE.MathUtils.smoothstep(elevation,-.08,.42);this.bedroomSun.intensity=12*day;for(const {light,power} of this.windows){light.intensity=power*day;light.color.set(light.name.startsWith('Window daylight bedroom')?'#f6dfb8':elevation<.25?'#ffdeb9':'#eef5ff');}for(const light of this.practicals)light.intensity=1.25+(1-day)*4.25;}
 snapshot(){return{windowSources:this.windows.length,practicals:this.practicals.length,daylightIntensity:+this.windows[0].light.intensity.toFixed(3)};}
}
