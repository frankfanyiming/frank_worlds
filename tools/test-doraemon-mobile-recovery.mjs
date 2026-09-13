// Actual mobile-sized browser + real model assets; transport faults are deliberate.
import {chromium} from '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const base=process.env.WORLDS_URL||'http://127.0.0.1:8795/frank_worlds/';
const out=resolve(process.env.MOBILE_EVIDENCE||'docs/evidence/mobile-revision23/recovery');await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const report={environment:'Desktop Chrome touch emulation; real asset decode; 6 Mbps / 150 ms latency / 4× CPU slowdown after startup',checks:[],errors:[]};
try{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:3});const page=await context.newPage();const cdp=await context.newCDPSession(page);
 await page.addInitScript(()=>{window.__townTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__townTools[t.name]=t;}}});});
 page.on('pageerror',e=>report.errors.push(e.message));
 const state=()=>page.evaluate(()=>window.__townTools.read_town_state.execute({}));
 const tool=(name,args)=>page.evaluate(({name,args})=>window.__townTools[name].execute(args),{name,args});
 const ready=()=>page.waitForFunction(()=>window.__townTools?.read_town_state?.execute({}).ready,{},{timeout:120000});
 const upstairs=async()=>{await page.locator('.side-tools button').first().tap();await page.getByRole('button',{name:'去二楼 ↗'}).tap();};
 await page.goto(base+'#world/doraemon',{waitUntil:'domcontentloaded'});await ready();
 const failedRequests=[];page.on('requestfailed',r=>{if(r.url().includes('/mobile-v23/'))failedRequests.push({url:r.url(),error:r.failure()?.errorText});});
 await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:150,downloadThroughput:6*1024*1024/8,uploadThroughput:1024*1024/8});await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
 await upstairs();await page.waitForFunction(()=>window.__townTools.read_town_state.execute({}).bedroom.downloadedBytes>200000,{},{timeout:40000});
 await page.screenshot({path:out+'/download-progress.png'});const partial=(await state()).bedroom;assert(partial.progress>0&&partial.progress<20);assert(await page.locator('.room-loading').innerText().then(s=>s.includes('MB')));
 await page.getByRole('button',{name:'先逛小镇'}).tap();await page.waitForFunction(()=>window.__townTools.read_town_state.execute({}).bedroom.status==='idle');
 assert.equal((await state()).floor,0);assert(failedRequests.some(r=>/ABORTED/.test(r.error)),'Cancellation aborts the real HTTP stream');report.checks.push({cancelledBytes:partial.downloadedBytes,progressBeforeCompletion:partial.progress});
 const retryStart=Date.now();await upstairs();await page.waitForFunction(()=>window.__townTools.read_town_state.execute({}).floor===1,{},{timeout:180000});assert.equal((await state()).bedroom.status,'ready');report.checks.push({slowNetworkRetryMs:Date.now()-retryStart});await page.screenshot({path:out+'/slow-network-bedroom.png'});
 await tool('navigate_town',{place:'home',mode:'orbit'});await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});
 // Real touch contact drives the authored animation, not only a position tween.
 const start=(await state()).position,box=await page.locator('.touch-stick').boundingBox();const touch={id:1,x:box.x+box.width/2,y:box.y+box.height*.77};
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[touch]});await page.waitForTimeout(900);const moving=await state();await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 assert(Math.hypot(moving.position.x-start.x,moving.position.y-start.y)>.2);assert.equal(moving.characterActions.find(v=>v.id==='nobita').current,'Walk');await page.waitForTimeout(500);assert.equal((await state()).characterActions.find(v=>v.id==='nobita').current,'Idle');report.checks.push({touchWalk:true,walkDistance:Math.hypot(moving.position.x-start.x,moving.position.y-start.y)});
 // A fresh engine reuses the saved room while the network is unavailable.
 await page.waitForTimeout(1500);await page.reload({waitUntil:'domcontentloaded'});await ready();const cold=(await state()).assetCache;await context.setOffline(true);await upstairs();await page.waitForFunction(()=>window.__townTools.read_town_state.execute({}).floor===1,{},{timeout:120000});const warm=(await state()).assetCache;assert(warm.hits>cold.hits);assert.equal(warm.downloads,cold.downloads);report.checks.push({offlineBedroomFromCache:true,additionalCacheHits:warm.hits-cold.hits});await context.setOffline(false);
 // Rotate around the complete room to check preserved furniture and windows.
 await tool('navigate_town',{place:'bedroom',mode:'first'});await tool('set_town_season_time',{hour:15.5,auto:false});
 for(let angle=0;angle<4;angle++){if(angle){const a={id:4,x:190,y:420};await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[a]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...a,x:190+Math.PI/2/.004}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}await page.waitForTimeout(500);await page.screenshot({path:out+'/room-angle-'+angle+'.png'});}
 await page.setViewportSize({width:844,height:390});await page.waitForTimeout(500);await page.screenshot({path:out+'/room-landscape.png'});assert.equal((await state()).error,null);await context.close();
 // Deliberate 503 must show retry UI, then recover without a full-page reload.
 const failing=await browser.newContext({viewport:{width:360,height:780},isMobile:true,hasTouch:true,deviceScaleFactor:2}),fault=await failing.newPage();await fault.addInitScript(()=>{window.__townTools={};Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(t){window.__townTools[t.name]=t;}}});});let failures=0;
 await fault.route('**/models/mobile-v23/bedroom-v12.glb*',route=>++failures===1?route.fulfill({status:503,body:'Intentional recovery test'}):route.continue());await fault.goto(base+'#world/doraemon',{waitUntil:'domcontentloaded'});await fault.waitForFunction(()=>window.__townTools?.read_town_state?.execute({}).ready,{},{timeout:120000});await fault.locator('.side-tools button').first().tap();await fault.getByRole('button',{name:'去二楼 ↗'}).tap();await fault.getByRole('button',{name:'重试',exact:true}).waitFor({timeout:30000});await fault.screenshot({path:out+'/retry-ui.png'});await fault.getByRole('button',{name:'重试',exact:true}).tap();await fault.waitForFunction(()=>window.__townTools.read_town_state.execute({}).floor===1,{},{timeout:120000});assert.equal(failures,2);report.checks.push({serverFailureRetry:true});await failing.close();
 assert.equal(report.errors.length,0);report.passed=true;
}catch(e){report.passed=false;report.errors.push(String(e));process.exitCode=1;console.error(e);}
finally{await browser.close();await writeFile(out+'/report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));}
