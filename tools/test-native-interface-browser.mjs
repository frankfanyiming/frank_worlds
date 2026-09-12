// Checks the shared interface with the exported game by default. --shell-only
// is a fast, explicitly isolated layout check and is never runtime evidence.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs');
const root=fileURLToPath(new URL('../',import.meta.url));
const shellOnly=process.argv.includes('--shell-only');
const world=process.argv.includes('conan')?'conan':'frog';
const out=process.env.UI_EVIDENCE||root+'docs/evidence/ui-revision21/'+(shellOnly?'shell-':'runtime-')+world;
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const report={mode:shellOnly?'Isolated browser shell, no game model':'Exported WebGL game in desktop Chrome; touch emulation',world,checks:[],errors:[]};
const viewportCases=[{width:1440,height:900,touch:false},{width:390,height:844,touch:true},{width:844,height:390,touch:true}];
const locales=process.env.UI_LANGUAGES?.split(',')||(shellOnly?['zh-CN','zh-TW','en','ja','ko']:['zh-CN','en']);
try{
 for(const lang of locales){
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));page.on('console',m=>{if(/SCRIPT ERROR|Parse Error|Failed loading resource/.test(m.text()))report.errors.push(m.text());});
  if(shellOnly){
   let shell=await readFile(root+'tools/native-world-shell.html','utf8');let js=await readFile(root+'tools/native-loader.js','utf8');
   js=js.replace('load().catch(fail);','');shell=shell.replace('CONFIG_JSON','{}').replace('NATIVE_LOADER_JS',()=>js).replace('JUMP_BUTTON',world==='frog'?'<button data-action="jump">Jump</button>':'');
   await page.route('**/worlds/**/index.html*',route=>route.fulfill({status:200,contentType:'text/html',body:shell}));
  }
  await page.goto((process.env.NATIVE_BASE||'http://127.0.0.1:8790/frank_worlds/worlds')+'/'+world+'/index.html?lang='+lang,{waitUntil:'domcontentloaded'});
  if(shellOnly){
   const translations=JSON.parse(await readFile(root+`worlds/${world}/${world==='frog'?'source':'web-project'}/translations.json`,'utf8'));
   await page.evaluate(({lang,translations,world})=>{
    const t=s=>translations[s]?.[lang]||s;
    window.fixtureState={world,place:t(world==='frog'?'树干小屋':'毛利事务所'),time:'15:30',counter:57,prompt:t('采收三叶草'),toast:'',friend:{summary:''},menu:null,panel:null};
    window.fixtureTranslate=t;window.fixtureLog=[];
    window.xlandsUIAction=(action,value)=>{
     window.fixtureLog.push({action,value});
     if(action==='menu')window.fixtureState.menu={items:[{id:0,text:t('俯看小世界')},{id:1,text:t('相册')},{id:2,text:t('午后 / 黄昏')},{id:3,text:t('拍一张 P')},{id:4,text:t('行囊')}]};
     if(action==='album'){window.fixtureState.menu=null;window.fixtureState.panel={kind:'album',title:t('相册'),blocks:[],actions:[]};}
     if(action==='close'||action==='photo'){window.fixtureState.menu=null;window.fixtureState.panel=null;}
     window.xlandsState(window.fixtureState);
    };
    document.querySelector('#status').remove();document.body.classList.add('world-ready');window.xlandsState(window.fixtureState);
   },{lang,translations,world});
  }else await page.waitForFunction(()=>document.body.classList.contains('world-ready')&&!!window.xlandsUIAction,{},{timeout:180000,polling:250});
  for(const size of viewportCases){
   await page.setViewportSize(size);await page.waitForTimeout(350);
   await page.locator('[data-ui-action=menu]').click();await page.waitForTimeout(300);
   assert.equal(await page.locator('.native-menu:visible').count(),1);
   if(lang==='en'||lang==='ko')assert(!/[\u4e00-\u9fff]/.test(await page.locator('.native-menu:visible').innerText()),'menu must use the selected language');
   const geometry=await page.evaluate(()=>{
    const card=document.querySelector('.native-menu-card'),b=card.getBoundingClientRect();
    return{w:innerWidth,h:innerHeight,card:{x:b.x,y:b.y,w:b.width,h:b.height},controls:[...card.querySelectorAll('button')].map(el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}}),hudHidden:getComputedStyle(document.querySelector('.world-hud')).visibility==='hidden',noOver:document.documentElement.scrollWidth===innerWidth};
   });
   assert.equal(geometry.w,size.width,'CSS viewport width must match the actual device viewport');assert.equal(geometry.h,size.height,'CSS viewport height must match the actual device viewport');
   assert(geometry.card.x>=0&&geometry.card.y>=0&&geometry.card.x+geometry.card.w<=geometry.w+.5&&geometry.card.y+geometry.card.h<=geometry.h+.5);
   assert(geometry.noOver&&geometry.hudHidden);assert(geometry.controls.every(b=>b.w>=44&&b.h>=44));
   report.checks.push({case:`${lang} ${size.width}×${size.height} single menu`,pass:true,...geometry});
   await page.screenshot({path:`${out}/${lang}-${size.width}-menu.png`});
   if(world==='conan'&&!shellOnly){
    const destination=page.locator('.native-menu-items .menu-row').last();const target=await destination.innerText();await destination.scrollIntoViewIfNeeded();
    const closeBox=await page.locator('.native-menu [data-ui-action=close]').boundingBox();assert(closeBox.y>=0&&closeBox.y+closeBox.height<=size.height);
    await page.screenshot({path:`${out}/${lang}-${size.width}-menu-bottom.png`});
    await destination.click();await page.waitForTimeout(500);assert.equal(await page.locator('.native-menu:visible').count(),0);
    const place=await page.locator('.world-location').innerText();assert.equal(place.split('\n')[0],target.split('\n')[0]);
    report.checks.push({case:`${lang} ${size.width} scroll and select final destination`,target,place,pass:true});
   }else{await page.keyboard.press('Escape');await page.waitForTimeout(250);assert.equal(await page.locator('.native-menu:visible').count(),0);}
   if(world==='frog'){
    await page.locator('[data-ui-action=album]').click();await page.waitForTimeout(250);
    assert.equal(await page.locator('.native-menu:visible').count(),1);
    assert.equal(await page.locator('.native-menu-card[data-kind=album]').count(),1);
    await page.screenshot({path:`${out}/${lang}-${size.width}-album.png`});
    await page.locator('.native-menu [data-ui-action=close]').click();await page.waitForTimeout(250);
    if(!shellOnly){
     await page.locator('[data-ui-action=friend]').click();await page.waitForTimeout(300);
     assert.equal(await page.locator('.native-menu:visible').count(),1);
     if(lang==='en'||lang==='ko')assert(!/[\u4e00-\u9fff]/.test(await page.locator('.native-menu:visible').innerText()),'friend sheet must use the chosen language');
     await page.screenshot({path:`${out}/${lang}-${size.width}-friends.png`});
     await page.locator('.native-menu [data-ui-action=close]').click();await page.waitForTimeout(250);
     await page.locator('[data-ui-action=bag]').click();await page.waitForTimeout(300);
     assert.equal(await page.locator('.native-menu:visible').count(),1);
     assert.equal(await page.locator('.native-menu-card[data-kind=panel]').count(),1);
     if(lang==='en'||lang==='ko')assert(!/[\u4e00-\u9fff]/.test(await page.locator('.native-menu:visible').innerText()),'bag must use the chosen language');
     assert(await page.locator('.world-hud').evaluate(el=>getComputedStyle(el).visibility==='hidden'));
     await page.screenshot({path:`${out}/${lang}-${size.width}-bag.png`});
     await page.locator('.sheet-choice').last().click();await page.waitForTimeout(300);
     assert.equal(await page.locator('.native-menu:visible').count(),1);
     assert.equal(await page.locator('.native-menu-card[data-kind=friend]').count(),1);
     await page.locator('.native-menu [data-ui-action=close]').click();await page.waitForTimeout(250);
     assert.equal(await page.locator('.native-menu:visible').count(),0);
     report.checks.push({case:`${lang} ${size.width} bag to friend journal has one layer`,pass:true});
    }
   }
   await page.screenshot({path:`${out}/${lang}-${size.width}-hud.png`});
  }
  if(!shellOnly&&world==='frog'){
   await page.locator('[data-ui-action=album]').click();await page.waitForTimeout(250);
   const shoot=page.locator('.album-empty .sheet-primary');
   if(await shoot.count()){
    await shoot.click();await page.waitForTimeout(700);
    await page.locator('[data-ui-action=album]').click();await page.waitForTimeout(400);
    assert.equal(await page.locator('.album-photo img').count(),1);
    assert(await page.locator('.album-photo img').evaluate(el=>el.naturalWidth>0));
    await page.screenshot({path:`${out}/${lang}-saved-photo-album.png`});
    report.checks.push({case:lang+' real photo capture to populated album',pass:true});
    await page.locator('.native-menu [data-ui-action=close]').click();
   }
  }
  await context.close();
 }
 assert.equal(report.errors.length,0);
}catch(error){report.errors.push(String(error));process.exitCode=1;}
finally{await writeFile(out+'/report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
