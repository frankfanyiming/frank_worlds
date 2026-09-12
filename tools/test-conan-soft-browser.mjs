// Actual exported WebGL scene: destination navigation, day/night and interaction.
// Chrome touch emulation is not a physical phone test.
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || '/tmp/xlands-browser-audit/node_modules/playwright-core/index.mjs');
const out=process.env.CONAN_EVIDENCE_DIR;
if(!out)throw new Error('Set CONAN_EVIDENCE_DIR to a dedicated output directory');
await mkdir(out,{recursive:true});
const url=process.env.CONAN_URL || 'http://127.0.0.1:8790/frank_worlds/worlds/conan/index.html';
const report={environment:'Exported Godot in Chrome WebGL2, touch emulation',url,errors:[],console:[],checks:[]};
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--ignore-gpu-blocklist']});
const context=await browser.newContext({viewport:{width:844,height:390},hasTouch:true,isMobile:true,deviceScaleFactor:1});
const page=await context.newPage();
page.on('pageerror',e=>report.errors.push(e.message));
page.on('console',m=>{if(/READY|ERROR|SCRIPT ERROR|WebGL/.test(m.text()))report.console.push(m.text());});
try{
  await page.goto(url+'?lang=zh-CN&v=soft-review-'+Date.now(),{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.body.classList.contains('world-ready'),{},{timeout:180000});
  report.pack=await page.evaluate(async()=>await(await fetch('world-pack.json',{cache:'no-store'})).json());
  if(process.env.EXPECTED_CONAN_SHA)assert.equal(report.pack.sha256,process.env.EXPECTED_CONAN_SHA);
  assert(report.console.some(m=>m.includes('BLENDER_TOWN_READY')));
  report.checks.push({case:'production scene ready and expected pack hash',passed:true});
  async function choose(name){
    await page.touchscreen.tap(110,104);
    const dialog=page.getByRole('dialog');await dialog.waitFor({state:'visible'});
    await dialog.getByRole('button',{name,exact:true}).tap();
    await dialog.waitFor({state:'hidden'});await page.waitForTimeout(650);
  }
  for(const [room,name] of [['毛利侦探事务所','mouri-office'],['工藤家 · 挑空书房','kudo-library'],['阿笠宅 · 环形厨房','agasa-kitchen']]){
    await choose(room);
    assert.equal(await page.locator('body.world-ui-open').count(),0);
    await page.screenshot({path:out+'/'+name+'-day.png'});
    await choose('昼夜');
    await page.screenshot({path:out+'/'+name+'-night.png'});
    await choose('昼夜');
    // View and interaction actions must remain functional after navigation.
    await page.locator('[data-action=view]').tap();await page.waitForTimeout(200);
    await page.locator('[data-action=interact]').tap();await page.waitForTimeout(200);
    await page.locator('[data-action=view]').tap();
    report.checks.push({case:room+' navigation, day/night and controls',passed:true});
  }
  assert.equal(report.errors.length,0);
  assert(!report.console.some(m=>/SCRIPT ERROR|Parse Error|Failed loading resource/.test(m)));
}catch(error){report.errors.push(String(error));process.exitCode=1;await page.screenshot({path:out+'/failure.png'}).catch(()=>{});}
finally{report.passed=report.errors.length===0;await writeFile(out+'/report.json',JSON.stringify(report,null,2)+'\n');await browser.close();console.log(JSON.stringify(report));}
