import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import ts from 'typescript';
import * as THREE from 'three';
const dir=new URL('../.test-build/',import.meta.url);await mkdir(dir,{recursive:true});
for(const name of ['world','loading','traffic']){const input=await readFile(new URL('../lib/town/'+name+'.ts',import.meta.url),'utf8');await writeFile(new URL(name+'.js',dir),ts.transpileModule(input,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText);}
const {LoadProgress,boundedMap,withDeadline,fetchBytes}=await import(new URL('loading.js',dir));
const {collides,groundHeight,HOUSE,houseAt}=await import(new URL('world.js',dir));
const {TownTraffic}=await import(new URL('traffic.js',dir));
const values=[];const p=new LoadProgress(3,v=>values.push(v));p.update(0,1.3);p.update(0,.2);p.update(1,Infinity);p.update(1,1);p.update(2,1);p.stage(96);assert.equal(values.at(-1),96);p.stage(100);assert.equal(values.at(-1),100);assert(values.every((v,i)=>v>=0&&v<=100&&(!i||v>=values[i-1])));
let active=0,peak=0;assert.deepEqual(await boundedMap([1,2,3,4,5],2,async n=>{active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,5));active--;return n*2;}),[2,4,6,8,10]);assert.equal(peak,2);
await assert.rejects(withDeadline(new Promise(()=>{}),10,'解码'),/超时/);
const realFetch=globalThis.fetch;globalThis.fetch=async()=>new Response('missing',{status:404});await assert.rejects(fetchBytes('test',new AbortController().signal),/404/);globalThis.fetch=realFetch;
const data=JSON.parse(await readFile(new URL('../public/models/world.json',import.meta.url)));
assert.equal(houseAt(-10.8,-21),'shizuka');assert.equal(groundHeight(-10.8,-21,2.94),2.94);
for(const [x,y0,y1,z0,z1] of [[HOUSE.stairX,HOUSE.stairY0,HOUSE.stairY1,.48,3.15],[-12.13,-20.5,-17.3,.24,2.94]]){let previous=z0;for(let i=0;i<=50;i++){const y=y0+(y1-y0)*i/50,h=groundHeight(x,y,previous);assert(h>=previous-.001);assert(!collides(x,y,h,data.colliders,.18),`stair blocked ${x},${y},${h}`);previous=h;}assert(Math.abs(previous-z1)<.001);}
function connected(a,b,z){const step=.15,x0=Math.min(a[0],b[0])-6,y0=Math.min(a[1],b[1])-7,w=90,h=110;const key=(x,y)=>x+','+y;const start=[Math.round((a[0]-x0)/step),Math.round((a[1]-y0)/step)];const todo=[start],seen=new Set([key(...start)]);while(todo.length){const [ix,iy]=todo.shift();const x=x0+ix*step,y=y0+iy*step;if(Math.hypot(x-b[0],y-b[1])<.24)return true;for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const nx=ix+dx,ny=iy+dy,k=key(nx,ny),xx=x0+nx*step,yy=y0+ny*step;if(nx<0||ny<0||nx>=w||ny>=h||seen.has(k)||!houseAt(xx,yy)||Math.abs(groundHeight(xx,yy,z)-z)>.15||collides(xx,yy,z,data.colliders,.18))continue;seen.add(k);todo.push([nx,ny]);}}return false;}
const routes=[['home living',[-11.5,1.8],[-14.0,2.1],.48],['home kitchen',[-11.5,1.8],[-12.0,6.5],.48],['home stairs',[-11.5,1.8],[-12.48,3.0],.48],['shizuka living',[-10.78,-21],[-9.72,-20.2],.24],['shizuka kitchen',[-10.78,-21],[-12.2,-16.2],.24],['shizuka stairs',[-10.78,-21],[-12.13,-20.55],.24]];
for(const [name,a,b,z] of routes)assert(connected(a,b,z),name+' has no walkable route');
const traffic=new TownTraffic(new THREE.Group());const asset=new THREE.Group();asset.add(new THREE.Mesh(new THREE.BoxGeometry(1.5,1.4,3.4)));traffic.addAsset(asset,'car');const car=traffic.cars.find(c=>!c.parked);car.root.position.x=-12;car.root.visible=true;car.speed=2.3;traffic.time=1;const pedestrian=new THREE.Vector3(-7,.13,6.86);for(let i=0;i<300;i++)traffic.update(1/60,new THREE.Vector3(50,0,50),[pedestrian]);assert(car.root.position.x+car.length/2<=pedestrian.x-.8);assert(traffic.collides(car.root.position.x,-car.root.position.z,.13,.55));
console.log('PASS: progress bounds/monotonicity, concurrency, timeout, HTTP failure, two staircases, six room routes, car pedestrian braking and collision.');
