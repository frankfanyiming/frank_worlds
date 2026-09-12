// Desktop Chromium emulates mobile viewports/touches; this is not a physical-device claim.
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs');
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const out=path.resolve('docs/evidence/mobile');await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const report={environment:'Desktop Chromium with mobile viewport and touch emulation; not a physical phone',checks:[],errors:[]};
async function check(name,fn){try{const detail=await fn();report.checks.push({name,pass:true,detail});console.log('PASS',name,JSON.stringify(detail??{}));}catch(e){report.checks.push({name,pass:false,error:String(e)});console.error('FAIL',name,String(e));}}
const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
await page.addInitScript(()=>{window.__townTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(tool){window.__townTools[tool.name]=tool;}}});});
const size=()=>page.evaluate(()=>({w:innerWidth,h:innerHeight,scroll:document.documentElement.scrollWidth}));
const tool=(name,args={})=>page.evaluate(({name,args})=>window.__townTools[name].execute(args),{name,args});
try{
 await page.goto('http://127.0.0.1:8784/frank_worlds/',{waitUntil:'domcontentloaded'});
 await page.getByRole('heading',{name:'机器猫在等你回家'}).waitFor();
 for(const viewport of [{width:390,height:844},{width:844,height:390},{width:360,height:640}]){
  await page.setViewportSize(viewport);
  await check('portal fits '+viewport.width+'x'+viewport.height,async()=>{const s=await size();assert.equal(s.scroll,s.w);const boxes=await page.locator('.hub-header nav>.icon-button,.hub-header .language-select,.hub-header .guest-link').evaluateAll(els=>els.map(e=>({text:e.textContent,r:{x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}})));assert(boxes.every(b=>b.r.h>=43&&b.r.x>=0&&b.r.x+b.r.w<=s.w));return{s,controls:boxes};});
  await page.screenshot({path:path.join(out,`portal-${viewport.width}.png`)});
 }
 await page.setViewportSize({width:390,height:844});
 await page.locator('.language-select select').selectOption('en');
 await check('portal language and guestbook remain usable',async()=>{await page.locator('.guest-link').click();await page.locator('#guestbook').waitFor();const r=await page.locator('#guestbook').boundingBox();assert(r.width<=390);return{language:await page.locator('.language-select select').inputValue(),guestbookWidth:r.width};});
 await page.locator('.language-select select').selectOption('zh-CN');
 await page.goto('http://127.0.0.1:8784/frank_worlds/#world/doraemon',{waitUntil:'domcontentloaded'});
 console.log('WAIT Doraemon real assets');
 await page.waitForFunction(()=>window.__townTools?.read_town_state?.execute({}).ready,{},{timeout:150000});
 await check('Doraemon real scene starts on mobile',async()=>{const state=await tool('read_town_state');assert(state.ready&&!state.error);return{ready:state.ready,quality:state.quality,shaderErrors:state.renderHealth.shaderErrors};});
 for(const viewport of [{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(viewport);
  await check('Doraemon canvas and touch controls fit '+viewport.width,async()=>{const s=await size();assert.equal(s.scroll,s.w);const canvas=await page.locator('.world-canvas canvas').boundingBox();const controls=await page.locator('.touch-stick,.touch-actions button').evaluateAll(els=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})));assert(canvas.height>=s.h-80);assert(controls.every(b=>b.w>=44&&b.h>=44&&b.x>=0&&b.y>=canvas.y&&b.x+b.w<=s.w&&b.y+b.h<=s.h));return{canvas,controls};});
  await page.screenshot({path:path.join(out,`doraemon-${viewport.width}.png`)});
 }
 await page.setViewportSize({width:390,height:844});await tool('navigate_town',{place:'home',mode:'first'});
 await check('Doraemon real concurrent joystick + look + run',async()=>{
  const start=await tool('read_town_state'),stick=await page.locator('.touch-stick').boundingBox(),run=await page.locator('.touch-actions button').first().boundingBox(),cdp=await context.newCDPSession(page);
  const move={id:1,x:stick.x+stick.width/2,y:stick.y+stick.height/2-34,radiusX:6,radiusY:6},look={id:2,x:200,y:370,radiusX:6,radiusY:6},running={id:3,x:run.x+run.width/2,y:run.y+run.height/2,radiusX:6,radiusY:6};
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[move]});await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[move,look]});await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[move,look,running]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[move,{...look,x:245},running]});await new Promise(r=>setTimeout(r,1200));
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await new Promise(r=>setTimeout(r,350));
  const end=await tool('read_town_state'),distance=Math.hypot(end.position.x-start.position.x,end.position.y-start.position.y);assert(distance>.1);assert.equal(end.mode,'first');await cdp.detach();return{distance,start:start.position,end:end.position};
 });
 await check('Doraemon mobile settings open and close',async()=>{await page.getByRole('button',{name:'调整时间和四季'}).click();const dialog=page.getByRole('dialog');await dialog.waitFor();await new Promise(r=>setTimeout(r,350));const b=await dialog.boundingBox();assert(b.x>=0&&b.x+b.width<=390&&b.y>=0&&b.y+b.height<=844);await page.screenshot({path:path.join(out,'doraemon-settings-390.png')});await page.getByRole('button',{name:'Close',exact:true}).click();await dialog.waitFor({state:'hidden'});return b;});
 console.log('WAIT requested bedroom original assets');
 await check('Doraemon requested bedroom and interior light',async()=>{await tool('navigate_town',{place:'bedroom',mode:'first'});await tool('set_town_season_time',{hour:15.5,auto:false});await new Promise(r=>setTimeout(r,600));const state=await tool('read_town_state');assert(state.bedroom.status==='ready'&&state.house==='home'&&state.floor===1);assert.equal(state.renderHealth.shaderErrors.length,0);await page.screenshot({path:path.join(out,'doraemon-bedroom-day-390.png')});await tool('set_town_season_time',{hour:21,auto:false});await new Promise(r=>setTimeout(r,500));await page.screenshot({path:path.join(out,'doraemon-bedroom-night-390.png')});return{house:state.house,bedroom:state.bedroom,light:state.interiorLight};});
 await page.goto('http://127.0.0.1:8785/',{waitUntil:'domcontentloaded'});
 for(const viewport of [{width:390,height:844},{width:844,height:390},{width:360,height:640}]){
  await page.setViewportSize(viewport);await page.locator('#hero-title').waitFor();
  await check('company site fits '+viewport.width+'x'+viewport.height,async()=>{const s=await size();assert.equal(s.scroll,s.w);const buttons=await page.locator('#previous-view,#next-view,#toggle-audio,#toggle-playback').evaluateAll(els=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})));assert(buttons.every(b=>b.x>=0&&b.x+b.w<=s.w&&b.h>=43&&b.y+b.h<=Math.max(650,s.h)));return{s,buttons};});
  await page.screenshot({path:path.join(out,`company-${viewport.width}.png`)});
 }
 await page.setViewportSize({width:390,height:844});
 await check('company touch carousel and video dialog',async()=>{const before=await page.locator('#view-counter').innerText();const cdp=await context.newCDPSession(page);const box=await page.locator('.pov-card.is-active').boundingBox(),y=box.y+box.height/2;await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:285,y}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{id:1,x:110,y}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForFunction(value=>document.querySelector('#view-counter').textContent!==value,before);await new Promise(r=>setTimeout(r,500));await page.locator('.pov-card.is-active .card-select').click();await page.locator('#clip-dialog').waitFor({state:'visible'});const d=await page.locator('#clip-dialog').boundingBox();assert(d.x>=0&&d.x+d.width<=390&&d.y>=0&&d.y+d.height<=844);await page.screenshot({path:path.join(out,'company-video-390.png')});await page.locator('#close-dialog').click();await cdp.detach();return{before,after:await page.locator('#view-counter').innerText(),dialog:d};});
 await check('company form fits portrait',async()=>{await page.getByRole('link',{name:'About',exact:true}).click();await page.locator('.access-form').scrollIntoViewIfNeeded();const widths=await page.locator('.access-form input:not([type=checkbox]),.access-form textarea,.access-form select').evaluateAll(els=>els.map(e=>({w:e.getBoundingClientRect().width,x:e.getBoundingClientRect().x,font:getComputedStyle(e).fontSize})));assert(widths.every(b=>b.x>=0&&b.x+b.w<=390&&parseFloat(b.font)>=16));await page.screenshot({path:path.join(out,'company-form-390.png')});return widths;});
}finally{await writeFile(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));await browser.close();console.log('REPORT',out);}
if(report.checks.some(x=>!x.pass)||report.errors.length)process.exitCode=1;
