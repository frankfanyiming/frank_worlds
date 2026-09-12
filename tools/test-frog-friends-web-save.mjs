// Uses a disposable browser profile; exported assets and the user's saves are untouched.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE||'/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs').href);
const out=process.env.FROG_WEB_SAVE_OUT||resolve('docs/evidence/frog-friends/web-persistence-final');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const context=await browser.newContext({viewport:{width:1280,height:900}});const page=await context.newPage();
const report={url:process.env.FROG_WEB_SAVE_URL||'http://127.0.0.1:8791/frank_worlds/worlds/frog/index.html?lang=zh-CN',errors:[],checks:{},events:[],notes:['Instrumentation exists only in this isolated test browser response; exported source and files are unmodified.','A private save fixture is seeded once to reach the stove; measured saves use real friend cooking actions and production FileAccess.']};
page.on('pageerror',e=>report.errors.push(e.message));
page.on('console',m=>{if(/SCRIPT ERROR|Parse Error/.test(m.text()))report.errors.push(m.text())});
const inject=`window.__auditEvents=[];window.__auditFS=FS;window.__auditGodotFS=GodotFS;
const auditClose=FS.close;FS.close=function(stream){const p=stream.path,flags=stream.flags;const r=auditClose.call(this,stream);if(p&&p.endsWith('woodland-save.json')&&(flags&3)){let data=null;try{data=JSON.parse(FS.readFile(p,{encoding:'utf8'}))}catch{}window.__auditEvents.push({type:'close',at:performance.now(),path:p,data});}return r;};
const auditSync=GodotFS.sync;GodotFS.sync=function(){const start=performance.now();const id=window.__auditEvents.length;window.__auditEvents.push({type:'sync-start',at:start,id});return auditSync.call(this).then(error=>{window.__auditEvents.push({type:'sync-end',at:performance.now(),id,error:String(error||'')});return error;});};`;
await page.route('**/frog/index.js',async route=>{const response=await route.fetch();let js=await response.text();if(!js.includes(';var GodotOS={'))throw Error('Godot JS marker missing');js=js.replace(';var GodotOS={',';'+inject+'var GodotOS={');await route.fulfill({response,body:js});});
async function ready(){await page.waitForFunction(()=>document.body.classList.contains('world-ready')&&window.__auditFS,{}, {timeout:180000,polling:250});}
async function getSave(){return page.evaluate(()=>{function walk(path){for(const f of window.__auditFS.readdir(path)){if(f==='.'||f==='..')continue;const p=path+'/'+f;const stat=window.__auditFS.stat(p);if(window.__auditFS.isDir(stat.mode)){const found=walk(p);if(found)return found;}else if(f==='woodland-save.json')return p;}return null;}const path=walk('/userfs');return path?{path,data:JSON.parse(window.__auditFS.readFile(path,{encoding:'utf8'}))}:null;});}
async function reload(){await page.reload({waitUntil:'domcontentloaded'});await ready();}
async function openCooking(){await page.evaluate(()=>window.xlandsUIAction('friend','open'));await page.waitForTimeout(200);await page.evaluate(()=>window.xlandsUIAction('friend','recipes'));await page.waitForTimeout(200);}
try{
 await page.goto(report.url,{waitUntil:'domcontentloaded'});await ready();await page.waitForTimeout(5500);
 const base=await getSave();if(!base)throw Error('No automatic user:// save');report.path=base.path;report.checks.initial_auto_save_created=true;
 const fixture={version:1,stage:'invited',companion:true,events:{'invite:first':{kind:'invite',value:''}},sequence:1,cooking:{id:'cook:1',recipe:'rice',step:0},cooked:[],gifts:{},keepsakes:{tea_jar:1,stone:1},memories:[],checkpoint:{home:'frog',frog:[-12.3,.2,-11.8],panda:[-13.5,.2,-11.8]},picnic_item:{},shared_tea:true};
 await page.evaluate(async ({path,data,fixture})=>{data.friend_life=fixture;data.clovers=57;data._save_sequence=100;data._saved_at=Date.now()/1000;window.__auditFS.writeFile(path,JSON.stringify(data));await window.__auditGodotFS.sync();},{...base,fixture});
 await reload();await openCooking();
 await page.evaluate(()=>{window.__auditEvents=[];window.xlandsUIAction('friend','advance:cook:1:0');});
 await page.waitForFunction(()=>window.__auditEvents.some(e=>e.type==='close'&&e.data?.friend_life?.cooking?.step===1)&&window.__auditEvents.some(e=>e.type==='sync-end'),{}, {timeout:10000,polling:20});
 report.events=await page.evaluate(()=>window.__auditEvents);report.checks.normal_action_closed_save=true;
 await reload();const normal=await getSave();report.checks.after_completed_sync_reload_preserves_step=normal.data.friend_life.cooking.step===1;report.normalStep=normal.data.friend_life.cooking.step;
 await openCooking();
 await Promise.all([page.waitForEvent('domcontentloaded'),page.evaluate(()=>{window.__auditEvents=[];window.xlandsUIAction('friend','advance:cook:1:1');sessionStorage.setItem('audit-immediate',JSON.stringify({events:window.__auditEvents,mirror:JSON.parse(localStorage.getItem('xlands:frog:state:v1'))}));location.reload();}).catch(e=>{if(!/context|navigation/i.test(e.message))throw e;})]);
 await ready();report.immediate=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('audit-immediate')));const immediate=await getSave();report.immediateStep=immediate.data.friend_life.cooking.step;report.checks.immediate_reload_observed_step=immediate.data.friend_life.cooking.step===2;
 await page.screenshot({path:out+'/after-reload.png'});
 report.checks.mirror_was_synchronous_before_reload=report.immediate.mirror.friend_life.cooking.step===2;
 report.checks.reload_preserves_clovers=immediate.data.clovers===57;
 // The third step closes a completed recipe; do the same immediate reload.
 await openCooking();await Promise.all([page.waitForEvent('domcontentloaded'),page.evaluate(()=>{window.xlandsUIAction('friend','advance:cook:1:2');location.reload();}).catch(e=>{if(!/context|navigation/i.test(e.message))throw e;})]);await ready();
 const completed=await getSave();report.checks.completed_recipe_survives_immediate_reload=completed.data.friend_life.cooked.length===2&&Object.keys(completed.data.friend_life.cooking).length===0;
 report.completed=completed.data.friend_life;
 report.checks.consecutive_reload_keeps_stove_checkpoint=Math.hypot(completed.data.friend_life.checkpoint.frog[0]+12.3, completed.data.friend_life.checkpoint.frog[2]+11.8)<.3;
 // An old mirror must not override a newer IndexedDB revision.
 await page.evaluate(()=>{let old=JSON.parse(localStorage.getItem('xlands:frog:state:v1'));old._save_sequence=1;old._saved_at=1;old.clovers=2;localStorage.setItem('xlands:frog:state:v1',JSON.stringify(old));});await page.waitForTimeout(100);await reload();
 report.checks.stale_mirror_does_not_override_newer_idb=(await getSave()).data.clovers===57;
 // Simulate unavailable localStorage only for the save key. Game should retain
 // the original userfs path and commit normally without an uncaught exception.
 await openCooking();await page.evaluate(()=>{const original=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='xlands:frog:state:v1')throw new DOMException('Simulated quota','QuotaExceededError');return original.call(this,k,v);};window.__auditEvents=[];window.xlandsUIAction('friend','recipe:tea');});
 await page.waitForFunction(()=>window.__auditEvents.some(e=>e.type==='sync-end'),{}, {timeout:10000,polling:20});
 report.checks.quota_fallback_userfs_saved=(await getSave()).data.friend_life.cooking.recipe==='tea';
 await reload();report.checks.quota_fallback_reloads_from_idb=(await getSave()).data.friend_life.cooking.recipe==='tea';

 // A mirror can be newer than the PNG commit. Preserve old ordinary metadata,
 // but remove an uncommitted friend memory and permit its picnic photo retry.
 const photoBase=await getSave();
 await page.evaluate(({data})=>{data._save_sequence+=100;data._saved_at=Date.now()/1000;data.photos=[{file:'missing-old.png',place:'legacy',time:'2026'},{file:'missing-friends.png',friend:'panda',place:'camp',time:'2026'}];data.friend_life.cooking={};data.friend_life.stage='remembered';data.friend_life.memories=[{id:'test-memory:1',photo:'missing-friends.png'}];data.friend_life.picnic_item={id:'test-picnic-meal',recipe:'rice'};localStorage.setItem('xlands:frog:state:v1',JSON.stringify(data));},photoBase);
 await reload();const repaired=await getSave();
 report.checks.missing_friend_png_restores_photo_retry=repaired.data.friend_life.stage==='picnic'&&repaired.data.friend_life.memories.length===0&&repaired.data.friend_life.picnic_item.id==='test-picnic-meal';
 report.checks.missing_png_recovery_keeps_food_and_legacy_records=repaired.data.friend_life.cooked.length===2&&repaired.data.photos.length===1&&repaired.data.photos[0].file==='missing-old.png';
 await page.evaluate(()=>{const original=window.xlandsState;window.xlandsState=function(s){window.__auditState=s;return original(s);};window.xlandsUIAction('album');});
 await page.waitForFunction(()=>window.__auditState?.panel?.kind==='album',{}, {timeout:10000,polling:50});
 report.album=await page.evaluate(()=>window.__auditState.panel);
 report.checks.missing_ordinary_png_displays_zero_count_empty_state=report.album.title.includes('0 张')&&report.album.blocks.some(b=>b.type==='text'&&b.text.includes('还没有照片'))&&!report.album.blocks.some(b=>b.type==='image');
 // Let the presentation-only dialog entrance settle before visual evidence.
 await page.waitForTimeout(400);
 await page.screenshot({path:out+'/missing-photo-empty-album.png'});
 const close=report.events.find(e=>e.type==='close'&&e.data?.friend_life?.cooking?.step===1);const end=report.events.find(e=>e.type==='sync-end'&&e.at>=close.at);report.closeToCommitMs=end?.at-close.at;
 console.log(JSON.stringify(report));
 if(Object.values(report.checks).some(passed=>!passed)||report.errors.length)process.exitCode=1;
}finally{await writeFile(out+'/report.json',JSON.stringify(report,null,2));await browser.close();}
