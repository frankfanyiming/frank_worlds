import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';

const source=await readFile(new URL('./native-loader.js',import.meta.url),'utf8');
const prelude=source.slice(0,source.indexOf('// Each surface owns its pointer.'));
function fixture(mobile,width,height){
 const events=new Map(),elements=new Map(),classes=new Set(),messages=[];
 const body={classList:{contains:k=>classes.has(k),add:k=>classes.add(k),remove:k=>classes.delete(k)},append:el=>{el.isConnected=true;}};
 const window={devicePixelRatio:3,matchMedia:()=>({matches:mobile}),addEventListener:(name,fn)=>events.set('window:'+name,fn)};
 const canvas={width:300,height:150,addEventListener:(name,fn)=>events.set('canvas:'+name,fn)};elements.set('#canvas',canvas);
 let timer;
 const ctx={window,innerWidth:width,innerHeight:height,location:{search:''},URLSearchParams,AbortController,console:{error(){}},setInterval:fn=>(timer=fn,1),clearInterval(){},setTimeout,clearTimeout,
  parent:{postMessage:msg=>messages.push(msg)},document:{body,hidden:false,documentElement:{},querySelector:id=>{if(!elements.has(id))elements.set(id,{isConnected:true});return elements.get(id);}}};
 const api=runInNewContext(prelude+'\n({render:installRenderBudget(),becomeReady(){ready=true;document.body.classList.add("world-ready");statusPanel.isConnected=false;}})',ctx);
 return{ctx,api,canvas,events,elements,classes,messages,tick:()=>timer()};
}
const phone=fixture(true,390,844);
assert.equal(phone.api.render.resizePolicy,0);
assert.deepEqual([phone.canvas.width,phone.canvas.height],[390,844]);
phone.api.becomeReady();phone.ctx.window.xlandsReadPerformance=()=>({fps:18});
for(let i=0;i<40;i++)phone.tick();
assert(Math.abs(phone.ctx.window.__xlandsPixelRatio-.65)<.00001);
const reduced=phone.canvas.width;phone.ctx.document.hidden=true;
phone.ctx.window.xlandsReadPerformance=()=>({fps:30});for(let i=0;i<60;i++)phone.tick();
assert.equal(phone.canvas.width,reduced,'Hidden pages must not adapt rendering');
phone.ctx.document.hidden=false;for(let i=0;i<300;i++)phone.tick();
assert.equal(phone.canvas.width,390,'Recovery is gradual and bounded');
phone.events.get('canvas:webglcontextlost')({preventDefault(){}});
assert.equal(phone.elements.get('#status').isConnected,true);
assert.equal(phone.elements.get('#retry').hidden,false);
assert(!phone.classes.has('world-ready'));
assert.equal(phone.messages.at(-1).type,'xlands-error');
assert.match(phone.messages.at(-1).detail,/图形加载失败/);
const tablet=fixture(true,1024,1366);assert(tablet.canvas.width*tablet.canvas.height<482000);
const pc=fixture(false,1440,900);assert.equal(pc.api.render.resizePolicy,2);assert.equal(pc.canvas.width,300,'Godot retains ownership of desktop resolution');
console.log('PASS: phone pixel budget, tablet ceiling, gradual recovery, hidden pause, PC ownership and visible context-loss retry');
