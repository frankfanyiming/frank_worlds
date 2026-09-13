// Actual composed release in Chromium WebGL2; mobile viewport emulation.
// Compares each loaded pack digest with the local reviewed export.
import {chromium} from '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const base=process.env.WORLDS_URL||'https://frankfanyiming.github.io/frank_worlds/';
const out=process.env.WORLDS_EVIDENCE||resolve('docs/evidence/revision22/public-browser');
const packs=process.env.EXPECTED_RELEASE_DIR||resolve('../release22-preview/frank_worlds/worlds');
const expected={};for(const world of ['frog','conan'])expected[world]=JSON.parse(await readFile(packs+'/'+world+'/world-pack.json','utf8')).sha256;
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const report={url:base,environment:'Desktop Chrome WebGL2 with mobile touch emulation',errors:[],worlds:[]};
try{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 for(const [world,sha]of Object.entries(expected)){
  const page=await context.newPage();const item={world,console:[],views:[]};page.on('pageerror',e=>report.errors.push(e.message));page.on('console',m=>{if(/READY|SCRIPT ERROR|Parse Error/.test(m.text()))item.console.push(m.text())});
  await page.goto(base+'?v=22#world/'+world,{waitUntil:'domcontentloaded'});const el=page.locator('iframe');await el.waitFor({state:'visible'});item.iframe=await el.getAttribute('src');assert(item.iframe.includes('access-furniture-22'));
  const f=await(await el.elementHandle()).contentFrame();await f.waitForLoadState('domcontentloaded');await f.waitForFunction(()=>document.body.classList.contains('world-ready')&&!!window.xlandsUIAction,{},{timeout:240000,polling:250});
  item.sha256=await f.evaluate(async()=>(await(await fetch('world-pack.json',{cache:'no-store'})).json()).sha256);assert.equal(item.sha256,sha);
  for(const size of [{width:390,height:844},{width:844,height:390}]){
   await page.setViewportSize(size);await page.waitForTimeout(700);const actual=await page.evaluate(()=>({w:innerWidth,h:innerHeight,scroll:document.documentElement.scrollWidth}));assert.equal(actual.w,size.width);assert.equal(actual.scroll,size.width);
   await page.screenshot({path:`${out}/${world}-${size.width}.png`});await f.locator('[data-ui-action=menu]').click();await f.locator('.native-menu:visible').waitFor();await page.waitForTimeout(450);await page.screenshot({path:`${out}/${world}-${size.width}-menu.png`});assert.equal(await f.locator('.native-menu:visible').count(),1);await f.locator('.native-menu [data-ui-action=close]').click();item.views.push(actual);
  }
  if(world==='frog'){await f.locator('[data-ui-action=friend]').click();await f.locator('.native-menu-card[data-kind=friend]').waitFor();item.friendText=await f.locator('.native-menu:visible').innerText();await page.waitForTimeout(450);await page.screenshot({path:out+'/frog-friends.png'});}
  assert(item.console.some(x=>x.includes(world==='frog'?'FROG_WORLD_READY':'BLENDER_TOWN_READY')));assert(!item.console.some(x=>/SCRIPT ERROR|Parse Error/.test(x)));report.worlds.push(item);await page.close();
 }
 const p=await context.newPage();await p.goto(base+'?v=22#world/doraemon',{waitUntil:'domcontentloaded'});await p.locator('.side-tools').waitFor({timeout:90000});await p.screenshot({path:out+'/doraemon-390.png'});await p.locator('.side-tools button').first().click();await p.locator('[role=dialog][data-open]').waitFor();await p.waitForTimeout(450);assert.equal(await p.locator('[role=dialog][data-open]').count(),1);await p.screenshot({path:out+'/doraemon-pocket.png'});report.worlds.push({world:'doraemon',ready:true,dialog:true});await p.close();
 assert.equal(report.errors.length,0);report.passed=true;
}catch(e){report.passed=false;report.errors.push(String(e));process.exitCode=1;}
finally{await writeFile(out+'/browser-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
