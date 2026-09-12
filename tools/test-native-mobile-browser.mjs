// Run with a locally installed playwright-core and Chrome. Real exported WebGL,
// desktop Chromium with mobile viewport/touch emulation, not a physical handset.
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs');
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const world=process.argv[2]||'frog';
const out=process.env.MOBILE_EVIDENCE_DIR || new URL('../docs/evidence/mobile/native-'+world+'/',import.meta.url).pathname;
const base=(process.env.NATIVE_BASE || 'http://127.0.0.1:8790/frank_worlds/worlds').replace(/\/$/,'');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
const page=await context.newPage();const report={world,environment:'Exported Godot WebGL2 in desktop Chrome, mobile viewport and touch emulation',errors:[],console:[],checks:[]};
page.on('pageerror',e=>report.errors.push(e.message));
page.on('console',m=>{if(/READY|ERROR|SCRIPT ERROR|WebGL/.test(m.text()))report.console.push(m.text())});
try{
 const start=Date.now();
 await page.goto(base+'/'+world+'/index.html?lang=zh-CN&v=mobile-18',{waitUntil:'domcontentloaded'});
 await page.screenshot({path:out+'loading.png'});
 await page.waitForFunction(()=>document.body.classList.contains('world-ready'),{},{timeout:180000});
 report.checks.push({case:'real exported scene ready',seconds:(Date.now()-start)/1000,pass:true});
 for(const size of [{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(size);await page.waitForTimeout(700);
  const dimensions=await page.evaluate(()=>({w:innerWidth,h:innerHeight,scroll:document.documentElement.scrollWidth,canvas:{w:document.querySelector('canvas').getBoundingClientRect().width,h:document.querySelector('canvas').getBoundingClientRect().height},controls:[...document.querySelectorAll('.touch-stick,.touch-actions button')].map(el=>{const b=el.getBoundingClientRect();return{x:b.x,y:b.y,w:b.width,h:b.height}})}));
  assert.equal(dimensions.w,dimensions.scroll);assert.equal(dimensions.h,dimensions.canvas.h);assert(dimensions.controls.every(b=>b.w>=44&&b.h>=44&&b.x>=0&&b.y>=0&&b.x+b.w<=dimensions.w&&b.y+b.h<=dimensions.h));
  report.checks.push({case:'viewport '+size.width+'x'+size.height,pass:true,...dimensions});
  await page.screenshot({path:out+'viewport-'+size.width+'.png'});
 }
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(500);
 const before=await page.screenshot({path:out+'touch-before.png'});
 const stick=await page.locator('.touch-stick').boundingBox();const run=await page.locator('[data-action=run]').boundingBox();const cdp=await context.newCDPSession(page);
 const move={id:1,x:stick.x+stick.width/2,y:stick.y+stick.height/2,radiusX:6,radiusY:6};const look={id:2,x:260,y:330,radiusX:6,radiusY:6};const running={id:3,x:run.x+run.width/2,y:run.y+run.height/2,radiusX:6,radiusY:6};
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[move]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...move,y:move.y-38}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...move,y:move.y-38},look,running]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...move,y:move.y-38},{...look,x:305},running]});
 await page.waitForTimeout(1100);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(350);
 const after=await page.screenshot({path:out+'touch-after.png'});assert(!before.equals(after));
 assert.equal(await page.locator('button.held').count(),0);
 report.checks.push({case:'simultaneous joystick, view drag and run then release',pass:true,render_changed:true,held_buttons_after_release:0});
 await page.locator('[data-action=view]').tap();await page.waitForTimeout(300);await page.screenshot({path:out+'view-button.png'});
 if(world==='frog'){
  await page.locator('[data-action=jump]').tap();await page.waitForTimeout(220);await page.screenshot({path:out+'jump.png'});
 }
 await cdp.detach();assert.equal(report.errors.length,0);
 assert(!report.console.some(line=>/SCRIPT ERROR|Parse Error|Failed loading resource/.test(line)));
}catch(error){report.errors.push(String(error));process.exitCode=1;}
finally{await writeFile(out+'report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
