// Measure submitted WebGL work, not just the browser's empty rAF heartbeat.
// A desktop GPU with touch/CPU emulation is not a physical-phone benchmark.
import {chromium} from '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const base=process.env.WORLDS_URL||'http://127.0.0.1:8795/frank_worlds/';
const out=resolve(process.env.PERF_OUT||'docs/evidence/performance-revision24/before');
const worlds=(process.env.PERF_WORLDS||'frog,conan,doraemon').split(',');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const report={environment:'Desktop Chrome Metal; touch emulation, DPR 3; not a physical phone',cpuThrottle:Number(process.env.CPU_THROTTLE||4),url:base,worlds:[],errors:[]};
const save=()=>writeFile(out+'/report.json',JSON.stringify(report,null,2));
try{
 for(const world of worlds){
  const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:3,isMobile:true,hasTouch:true});
  await context.addInitScript(()=>{
   window.__townTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__townTools[t.name]=t;}}});
   const count={calls:0,triangles:0};window.__glAudit={count,frames:[],buffers:[],active:false};
   const proto=WebGL2RenderingContext.prototype;
   for(const [key,index,instances]of [['drawElements',1,-1],['drawArrays',2,-1],['drawElementsInstanced',1,4],['drawArraysInstanced',2,3]]){
    const old=proto[key];proto[key]=function(...a){if(window.__glAudit.active){count.calls++;if(a[0]===this.TRIANGLES)count.triangles+=a[index]/3*(instances<0?1:a[instances]);}return old.apply(this,a);};
   }
   const old=proto.renderbufferStorageMultisample;proto.renderbufferStorageMultisample=function(...a){window.__glAudit.buffers.push({samples:a[1],width:a[3],height:a[4]});return old.apply(this,a);};
   let last=0;function tick(now){if(window.__glAudit.active&&last)window.__glAudit.frames.push({ms:now-last,calls:count.calls,triangles:count.triangles});count.calls=0;count.triangles=0;last=now;requestAnimationFrame(tick);}requestAnimationFrame(tick);
  });
  const page=await context.newPage(),item={world,views:[],errors:[]};report.worlds.push(item);
  page.on('pageerror',e=>item.errors.push(e.message));page.on('console',m=>{if(/SCRIPT ERROR|Parse Error/.test(m.text()))item.errors.push(m.text());});
  const cdp=await context.newCDPSession(page);if(report.cpuThrottle>1)await cdp.send('Emulation.setCPUThrottlingRate',{rate:report.cpuThrottle});
  const url=world==='doraemon'?base+'#world/doraemon':base+'worlds/'+world+'/index.html?lang=zh-CN';
  const begin=Date.now();await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(w=>w==='doraemon'?window.__townTools?.read_town_state?.execute({}).ready:document.body.classList.contains('world-ready'),world,{timeout:240000,polling:300});
  item.startupMs=Date.now()-begin;
  async function sample(name){
   await page.waitForTimeout(1800);await page.evaluate(()=>{window.__glAudit.frames=[];window.__glAudit.active=true;});await page.waitForTimeout(8000);
   const result=await page.evaluate(()=>{
    const a=window.__glAudit;a.active=false;const all=a.frames,drawn=all.filter(f=>f.calls>0),total=all.reduce((n,f)=>n+f.ms,0),timings=all.map(f=>f.ms).sort((a,b)=>a-b);const mean=k=>drawn.reduce((n,f)=>n+f[k],0)/Math.max(1,drawn.length);
    const canvas=document.querySelector('canvas');return{elapsedMs:Math.round(total),paintedFps:+(1000*drawn.length/total).toFixed(1),browserP95Ms:timings[Math.floor(timings.length*.95)],meanDrawCalls:Math.round(mean('calls')),meanTriangles:Math.round(mean('triangles')),maxTriangles:Math.max(...drawn.map(f=>f.triangles)),canvas:{width:canvas.width,height:canvas.height,cssWidth:canvas.clientWidth,cssHeight:canvas.clientHeight},buffers:a.buffers.slice(-8),diagnostics:window.xlandsReadPerformance?.()??window.__townTools?.read_town_state?.execute({}).renderHealth??null};
   });
   item.views.push({name,...result});console.log(world,name,JSON.stringify(result));await page.screenshot({path:out+'/'+world+'-'+name+'.png'});await save();
  }
  await sample('street-portrait');await page.setViewportSize({width:844,height:390});await sample('street-landscape');
  if(world==='doraemon'){
   await page.evaluate(()=>window.__townTools.navigate_town.execute({place:'bedroom',mode:'first'}));await page.waitForFunction(()=>window.__townTools.read_town_state.execute({}).floor===1,{},{timeout:180000});await sample('bedroom');
  }else if(world==='conan'){
   await page.evaluate(()=>window.xlandsUIAction('menu'));await page.locator('.native-menu:visible').waitFor();
   item.destinations=await page.locator('.native-menu-items').innerText();
   const office=page.getByRole('button',{name:'事务所',exact:false}).first();if(await office.count()){await office.tap();await sample('office');}
  }
  await context.close();await save();
 }
}catch(e){report.errors.push(String(e));process.exitCode=1;console.error(e);}finally{await save();await browser.close();}
