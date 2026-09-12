import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import ts from 'typescript';
import React from 'react';
const root=new URL('../',import.meta.url),out=new URL('.test-build/i18n/',root);await mkdir(out,{recursive:true});
const input=await readFile(new URL('lib/town/ui-i18n.tsx',root),'utf8');
await writeFile(new URL('ui-i18n.cjs',out),ts.transpileModule(input,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,esModuleInterop:true,resolveJsonModule:true}}).outputText);
for(const file of ['ui-translations.json','ui-traditional.json'])await copyFile(new URL('lib/town/'+file,root),new URL(file,out));
const {townText,localizeTownUI}=createRequire(import.meta.url)(new URL('ui-i18n.cjs',out).pathname);
const dictionary=JSON.parse(await readFile(new URL('lib/town/ui-translations.json',root),'utf8'));
const internalRouting=new Set(['和','聊聊','出门','上楼','开合','壁橱','拉开','进入抽屉','下楼','推门']);let count=0;
for(const file of ['components/worlds/DoraemonWorld.tsx','components/Adventure.tsx','lib/town/adventure.ts','lib/town/world.ts','lib/town/weather.ts','lib/town/sound.ts','lib/town/engine.ts']){
 const src=await readFile(new URL(file,root),'utf8'),ast=ts.createSourceFile(file,src,ts.ScriptTarget.Latest,true);
 function visit(n){if((ts.isStringLiteralLike(n)||ts.isJsxText(n))&&/[\u3400-\u9fff]/.test(n.text)){const key=n.text.trim().replace(/\s+/g,' ');if(!internalRouting.has(key)){assert(dictionary[key],`${file}: missing ${key}`);count++;}}ts.forEachChild(n,visit);}visit(ast);
}
for(const locale of ['en','ja','ko','zh-CN','zh-TW'])for(const key of Object.keys(dictionary)){const value=townText(locale,key);assert(value.trim(),`${locale} empty: ${key}`);if(locale==='en'||locale==='ko')assert(!/[\u3400-\u9fff]/.test(value),`${locale} mixed language: ${value}`);}
const dynamic=['和哆啦A梦聊聊','和静香聊聊','夏日 · 晴空','任意门通往大雄的房间，走进门或点击“穿过任意门”。','任意门已抵达：静香家','挑战结束 · 命中 3 次，个人最佳 5 次。','时光旅行抵达：飘雪冬夜。走下楼看看小镇的变化吧。','一起散步 18 / 25 米','第 3 / 5 球 · 命中 2','还剩 19 秒 · 命中 2'];
for(const text of dynamic)for(const locale of ['en','ko'])assert(!/[\u3400-\u9fff]/.test(townText(locale,text)),locale+' '+text);
const clicked=()=>{},inputTree=React.createElement('div',null,React.createElement('button',{'aria-label':'切换视角',onClick:clicked},'和静香聊聊'),React.createElement('input',{value:'静香家',placeholder:'正在打开小世界'}));const rendered=localizeTownUI(inputTree,'en');assert.equal(rendered.props.children[0].props.children,'Talk to Shizuka');assert.equal(rendered.props.children[0].props.onClick,clicked);assert.equal(rendered.props.children[1].props.value,'静香家');assert.equal(inputTree.props.children[0].props.children,'和静香聊聊');assert.equal(townText('en','我的音乐.mp3'),'我的音乐.mp3');assert.equal(townText('zh-TW','打开书桌抽屉'),'打開書桌抽屜');assert.equal(townText('zh-CN','A POCKET FULL OF WONDERS'),'口袋里的小惊喜');
console.log(`PASS: ${count} source text sites, ${Object.keys(dictionary).length} keys × 5 languages, dynamic interaction/score/weather messages, immutable callbacks/input values, user text and locale switching.`);
