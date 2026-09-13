// Real WebGL assets + touch UI. Desktop emulation, not a physical-phone benchmark.
import {chromium,webkit} from '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const base=process.env.WORLDS_URL||'http://127.0.0.1:8792/frank_worlds/';
const out=resolve(process.env.MOBILE_EVIDENCE||'docs/evidence/mobile-revision23/before');
await mkdir(out,{recursive:true});
const safari=process.env.BROWSER==='webkit';
const browser=await (safari?webkit.launch({headless:true}):chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']}));
const report={url:base,environment:`Desktop ${safari?'WebKit':'Chrome Metal'}, 390×844, DPR 3, touch emulation`,cpuThrottle:Number(process.env.CPU_THROTTLE||1),checks:[],errors:[],environmentErrors:[]};
const save=()=>writeFile(out+'/report.json',JSON.stringify(report,null,2));
try {
 const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:3,isMobile:true,hasTouch:true});
 const page=await context.newPage();
 page.on('pageerror',e=>{if(new URL(base).hostname==='127.0.0.1'&&e.message.includes('chatgpt.site/api/community/')&&e.message.includes('access control'))report.environmentErrors.push(e.message);else report.errors.push(e.message);});
 page.on('console',m=>{if(m.type()==='error')console.log('PAGE',m.text().slice(0,350));});
 await page.addInitScript(()=>{
  window.__townTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__townTools[t.name]=t;}}});
  window.__longFrames=[];if(PerformanceObserver.supportedEntryTypes.includes('longtask'))new PerformanceObserver(list=>{for(const e of list.getEntries())window.__longFrames.push({at:e.startTime,ms:e.duration});}).observe({type:'longtask',buffered:true});
 });
 const cdp=safari?null:await context.newCDPSession(page);if(report.cpuThrottle>1)await cdp.send('Emulation.setCPUThrottlingRate',{rate:report.cpuThrottle});
 const state=()=>page.evaluate(()=>window.__townTools.read_town_state.execute({}));
 const tool=(name,args)=>page.evaluate(({name,args})=>window.__townTools[name].execute(args),{name,args});
 const sample=async(name)=>{
  await page.waitForTimeout(1200);
  const timing=await page.evaluate(()=>new Promise(resolve=>{const frames=[],start=performance.now();let last=start;function tick(now){frames.push(now-last);last=now;if(now-start<6000)requestAnimationFrame(tick);else {frames.sort((a,b)=>a-b);resolve({frames:frames.length,medianMs:frames[Math.floor(frames.length*.5)],p95Ms:frames[Math.floor(frames.length*.95)],over50ms:frames.filter(n=>n>50).length});}}requestAnimationFrame(tick);}));
  const snapshot=await state();report.checks.push({name,timing,state:snapshot});await page.screenshot({path:out+'/'+name+'.png'});await save();console.log(name,JSON.stringify({timing,render:snapshot.renderHealth,bedroom:snapshot.bedroom,cache:snapshot.assetCache}));
 };
 const started=Date.now();await page.goto(base+'#world/doraemon',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>window.__townTools?.read_town_state?.execute({}).ready,{},{timeout:120000});
 report.startupMs=Date.now()-started;await sample('street');
 await page.locator('.side-tools button').first().tap();
 const upstairs=page.getByRole('button',{name:'去二楼 ↗'});await upstairs.scrollIntoViewIfNeeded();const entered=Date.now();await upstairs.tap();
 await page.waitForFunction(()=>{const s=window.__townTools.read_town_state.execute({});return s.floor===1&&s.bedroom.status==='ready'||s.bedroom.status==='error'||s.error;},{},{timeout:180000});
 report.bedroomEntryMs=Date.now()-entered;const room=await state();assert.equal(room.floor,1,room.bedroom?.error||room.error);assert.equal(room.bedroom.status,'ready');
 await tool('navigate_town',{place:'bedroom',mode:'first'});await tool('set_town_season_time',{hour:15.5,auto:false});await sample('bedroom');
 await page.setViewportSize({width:844,height:390});await sample('bedroom-landscape');
 await tool('navigate_town',{place:'home',mode:'orbit'});await sample('returned-street');
 const again=Date.now();await tool('navigate_town',{place:'bedroom',mode:'first'});report.repeatEntryMs=Date.now()-again;
 report.longTasks=await page.evaluate(()=>window.__longFrames);report.resources=await page.evaluate(()=>performance.getEntriesByType('resource').filter(e=>/\.glb|bedroom-materials/.test(e.name)).map(e=>({path:new URL(e.name).pathname,bytes:e.decodedBodySize,ms:e.duration})));
 assert.equal(report.errors.length,0);report.passed=true;
} catch(e){report.passed=false;report.errors.push(String(e));process.exitCode=1;console.error(e);}
finally{await save();await browser.close();console.log('REPORT',out);}
