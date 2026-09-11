import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {runInNewContext} from 'node:vm';
import {createHash} from 'node:crypto';

const root=resolve(process.argv[2]||'dist/worlds');
for(const world of ['frog','conan']){
 const dir=join(root,world),html=await readFile(join(dir,'index.html'),'utf8');
 const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)?.[1];assert(script,'Custom loader must be present');
 const descriptor=JSON.parse(await readFile(join(dir,'world-pack.json'),'utf8'));
 const wasm=await readFile(join(dir,'index.wasm'));assert.deepEqual([...wasm.subarray(0,4)],[0,97,115,109]);
 const elements=new Map(),messages=[],calls=[];let assembled,corrupted=false;
 const element=id=>{if(!elements.has(id))elements.set(id,{hidden:true,textContent:'',value:0,remove(){this.removed=true;}});return elements.get(id);};
 const Engine=class{
  static getMissingFeatures(){return [];}
  constructor(options){this.options=options;assert.equal(options.fileSizes['index.wasm'],wasm.length);}
  async init(base){assert.equal(base,'index');calls.push('init');}
  async preloadFile(buffer,path){assert.equal(path,'index.pck');assembled=Buffer.from(buffer);calls.push('preload');}
  async start(options){assert.deepEqual([...options.args],['--main-pack','index.pck']);calls.push('start');this.options.onPrint(world.toUpperCase()+'_WORLD_READY');}
 };
 const parent={postMessage:m=>messages.push(m)},window={addEventListener(){},xlandsSound(){}};
 const sandbox={URLSearchParams,Uint8Array,Response,DecompressionStream,AbortController,setTimeout,clearTimeout,crypto,console:{log(){},warn(){},error(){throw Error('Loader unexpectedly failed');}},location:{search:'?lang=ja&sound=1'},document:{documentElement:{},querySelector:element,querySelectorAll:()=>[]},window,parent,Engine,fetch:async file=>{
  file=file.split('?')[0];
  if(file==='world-pack.json')return Response.json(descriptor);
  let bytes=await readFile(join(dir,file));
  // A corrupt download must be retried and must never reach the engine.
  if(file===descriptor.chunks[0].file&&!corrupted){corrupted=true;bytes=Buffer.from([0,1,2,3]);}
  return new Response(bytes);
 }};
 await runInNewContext(script,sandbox,{timeout:10000});
 assert.deepEqual(calls,['init','preload','start']);
 assert.equal(assembled.length,descriptor.totalBytes);
 assert.equal(createHash('sha256').update(assembled).digest('hex'),descriptor.sha256);
 assert.equal(element('#status').removed,true);assert(messages.some(m=>m.type==='xlands-ready'));
 assert.equal(sandbox.document.documentElement.lang,'ja');
 assert(messages.some(m=>m.type==='xlands-progress'&&m.progress>0&&m.progress<15),'Progress must appear before a complete chunk arrives');
 const errorMessages=[];
 await runInNewContext(script,{...sandbox,console:{...sandbox.console,error(){}},parent:{postMessage:m=>errorMessages.push(m)},fetch:async()=>new Response('Unavailable',{status:503})},{timeout:10000});
 assert(errorMessages.some(m=>m.type==='xlands-error'));assert.equal(element('#retry').hidden,false);
 console.log(JSON.stringify({world,bytes:descriptor.totalBytes,chunks:descriptor.chunks.length,checks:['WASM header','loader API sequence','parallel chunk assembly','SHA-256 integrity','corrupt download retry','error retry UI','language','ready signal'],passed:true}));
}
