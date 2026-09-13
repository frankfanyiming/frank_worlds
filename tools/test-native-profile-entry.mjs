import {chromium,webkit} from '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const base=process.env.WORLDS_URL||'http://127.0.0.1:8796/frank_worlds/';
const out=resolve(process.env.ENTRY_OUT||'docs/evidence/performance-revision24/entry');await mkdir(out,{recursive:true});
const isWebKit=process.env.BROWSER==='webkit',mobile=process.env.PROFILE!=='desktop';
const world=process.env.ENTRY_WORLD||'conan';
const browser=await(isWebKit?webkit.launch({headless:true}):chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']}));
const report={url:base,world,environment:`Desktop ${isWebKit?'WebKit':'Chrome'}; ${mobile?'touch emulation':'mouse/desktop profile'}`,physicalPhone:false,checks:[],manifests:[],errors:[],environmentErrors:[]};
try{
 const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1440,height:900},deviceScaleFactor:mobile?3:2,isMobile:mobile,hasTouch:mobile});
 const page=await context.newPage();
 page.on('pageerror',e=>{if(e.message.includes('chatgpt.site/api/community/'))report.environmentErrors.push(e.message);else report.errors.push(e.message);});
 page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Failed loading resource/.test(m.text()))report.errors.push(m.text());});
 page.on('request',r=>{if(r.url().includes('world-pack.json'))report.manifests.push(r.url());});
 const enter=async()=>{
  await page.locator('.native-world iframe').waitFor();
  const frame=await(await page.locator('.native-world iframe').elementHandle()).contentFrame();
  await frame.waitForFunction(()=>document.body.classList.contains('world-ready')&&!!window.xlandsUIAction,{},{timeout:240000,polling:300});
  await frame.waitForTimeout(500);return frame;
 };
 await page.goto(base+'?v=24#world/'+world,{waitUntil:'domcontentloaded'});let frame=await enter();
 const read=()=>frame.evaluate(()=>{const c=document.querySelector('canvas');return{coarse:matchMedia('(any-pointer: coarse)').matches,canvas:[c.width,c.height],css:[innerWidth,innerHeight],health:window.xlandsReadPerformance?.()??null,place:document.querySelector('.world-location').innerText};});
 const start=await read();assert.equal(start.coarse,mobile);
 assert.equal(report.manifests.at(-1).includes('/mobile/'),mobile);
 if(mobile){assert(start.canvas[0]*start.canvas[1]<482000);assert.equal(start.health.profile,'mobile-speed');}
 else{assert(start.canvas[0]>=start.css[0]);assert.equal(start.health,null);}
 report.checks.push({name:'correct resource and rendering profile',...start});
 await page.screenshot({path:out+'/entry.png'});
 if(world==='conan'){
  for(const [label,file]of [['毛利侦探事务所','office'],['阿笠宅 · 环形厨房','agasa-kitchen'],['阿笠宅 · 后车库','agasa-garage']]){
   await frame.locator('[data-ui-action=menu]').click();await frame.locator('.native-menu:visible').waitFor();
   const destination=frame.getByRole('button',{name:label+' ↗',exact:true});await destination.scrollIntoViewIfNeeded();await destination.click();await frame.waitForTimeout(800);
   assert.equal(await frame.locator('.native-menu:visible').count(),0);report.checks.push({name:label,...await read()});await page.screenshot({path:out+'/'+file+'.png'});
  }
 }else{
  // Start at the authored doorway and use the same input callbacks as touch.
  await frame.evaluate(()=>window.xlandsMove(-Math.sin(.53),-Math.cos(.53)));await frame.waitForTimeout(3700);await frame.evaluate(()=>window.xlandsMove(0,0));await frame.waitForTimeout(700);
  const room=await read();report.checks.push({name:'frog doorway approach',...room});await page.screenshot({path:out+'/frog-room.png'});
  assert.match(room.place,/树干小屋|夹层睡铺/,'The mobile room must actually open');
 }
 if(mobile){
  await page.setViewportSize({width:844,height:390});await frame.waitForTimeout(650);const landscape=await read();assert(landscape.canvas[0]*landscape.canvas[1]<482000);report.checks.push({name:'landscape',...landscape});await page.screenshot({path:out+'/landscape.png'});
 }
 // Exercise a real lost GPU context and the parent page's retry, not a fake DOM.
 if(!isWebKit&&mobile&&world==='conan'){
  await frame.evaluate(()=>document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context').loseContext());
  await page.getByRole('button',{name:'重试',exact:true}).waitFor();await page.screenshot({path:out+'/graphics-retry.png'});
  await page.getByRole('button',{name:'重试',exact:true}).click();frame=await enter();report.checks.push({name:'real context loss and retry',...await read()});
 }
 assert.equal(report.errors.length,0);report.passed=true;
}catch(error){report.errors.push(String(error));report.passed=false;process.exitCode=1;console.error(error);}
finally{await writeFile(out+'/report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
