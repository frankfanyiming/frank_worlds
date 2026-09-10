const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),ts=require('typescript'),THREE=require('three');
require.extensions['.ts']=(module,file)=>module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,file);
global.document={documentElement:{dataset:{assetBase:'/frank_worlds/'}},exitPointerLock(){}};
const {fetchBytes,settleAssetCache,evictCachedAsset,assetCacheStats}=require('../lib/town/loading.ts');
const {TownEngine}=require('../lib/town/engine.ts');
const {GLTFLoader}=require('three/addons/loaders/GLTFLoader.js');
const {MODEL_PARTS,STARTUP_PARTS,BEDROOM_PART,ASSET_VERSION}=require('../lib/town/model-manifest.ts');
const {HOUSE,groundHeight}=require('../lib/town/world.ts');
const realFetch=global.fetch,realDecode=THREE.TextureLoader.prototype.loadAsync,realParse=GLTFLoader.prototype.parseAsync;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function memoryCache(){const saved=new Map();return{saved,async match(url){return saved.get(url)?.clone();},async put(url,response){saved.set(url,new Response(await response.arrayBuffer(),{status:response.status,headers:response.headers}));},async delete(url){return saved.delete(url);}};}
function engine(){const e=Object.create(TownEngine.prototype);Object.assign(e,{
 scene:new THREE.Scene(),world:new THREE.Group(),player:new THREE.Group(),playerPosition:new THREE.Vector3(-9.6,.23,6.3),camera:new THREE.PerspectiveCamera(),target:new THREE.Vector3(),targetGoal:new THREE.Vector3(),
 state:{ready:false,progress:0,error:null,mode:'orbit',floor:0,inside:false,place:'home',bedroom:{status:'idle',progress:0,requested:false,error:null}},
 renderer:{capabilities:{getMaxAnisotropy:()=>8},compileAsync:async()=>{}},sun:{shadow:{}},shaderErrors:[],navigation:0,bedroomQueued:false,disposers:[],loadAbort:new AbortController(),quality:true,
 colliders:[],groundSurfaces:[],slidingDoors:[],motions:new Map(),keys:new Set(),touch:{x:0,y:0},elapsed:0,yaw:0,azimuth:0,
 atmosphere:{install(){}},water:{install(){}},weather:{install(){},addAsset(){}},adventure:{addAsset(){},onTeleport(){},state:{activity:'none'},flightMove:()=>false},sound:{effect(){}},emit(){}
 });return e;}
(async()=>{try{
 // Actual fetch/cache implementation: repeated loads, version changes, offline cache,
 // quota/private-mode failure, HTTP errors and cancellation.
 let cache=memoryCache(),requests=0;global.caches={open:async()=>cache};global.fetch=async()=>{requests++;return new Response('original quality bytes');};
 const signal=new AbortController().signal,url='/models/test.glb?v=1';
 assert.equal(new TextDecoder().decode(await fetchBytes(url,signal)),'original quality bytes');await settleAssetCache();
 global.fetch=async()=>{throw Error('offline');};assert.equal(new TextDecoder().decode(await fetchBytes(url,signal)),'original quality bytes');assert.equal(requests,1);
 global.fetch=async()=>{requests++;return new Response('updated bytes');};assert.equal(new TextDecoder().decode(await fetchBytes('/models/test.glb?v=2',signal)),'updated bytes');await settleAssetCache();assert.equal(requests,2);
 await evictCachedAsset(url);assert(!cache.saved.has(url));
 global.caches={open:async()=>{throw Error('private mode');}};await fetchBytes('/models/test.glb?v=3',signal);assert.equal(requests,3);
 cache=memoryCache();cache.put=async()=>{throw Error('quota exceeded');};global.caches={open:async()=>cache};await fetchBytes('/models/test.glb?v=4',signal);await settleAssetCache();assert(assetCacheStats.writeFailures>0);
 cache=memoryCache();global.caches={open:async()=>cache};global.fetch=async()=>new Response('missing',{status:404});await assert.rejects(fetchBytes('/models/missing.glb?v=1',signal),/404/);await settleAssetCache();assert.equal(cache.saved.size,0);
 const cancelled=new AbortController();cancelled.abort();let calls=0;global.fetch=async()=>{calls++;return new Response('wrong');};await assert.rejects(fetchBytes(url,cancelled.signal),{name:'AbortError'});assert.equal(calls,0);
 const running=new AbortController();global.fetch=async(_,options)=>new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('Cancelled','AbortError'))));delete global.caches;
 const download=fetchBytes(url,running.signal);running.abort();await assert.rejects(download,{name:'AbortError'});
 // Use real asset names/material assignments and the real engine loading pipeline;
 // only WebGL, image decoding and network payloads are replaced for Node.
 const b=fs.readFileSync('public/models/bedroom-v12.glb'),roomJson=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));
 const requested=[],materialRequests=[];let releaseMaterials;const materialGate=new Promise(r=>releaseMaterials=r);let holdMaterials=true;
 const paths=new Map();
 global.fetch=async url=>{
  requested.push(url);const relative=new URL(url,'https://test.invalid').pathname.replace('/frank_worlds/','');const file=path.join('public',relative);paths.set(relative,fs.statSync(file).size);
  if(relative==='models/world.json'||relative.endsWith('manifest.json'))return new Response(fs.readFileSync(file));
  if(relative.startsWith('bedroom-materials/')){materialRequests.push(url);if(holdMaterials)await materialGate;return new Response('exact-image-decoder-fixture');}
  return new Response(JSON.stringify({part:relative.slice(7,-4)}));
 };
 function room(){const root=new THREE.Group();for(const name of ['hero_floor','hero_props','hero_closet','hero_shell','hero_front','hero_ceiling','v12_nobita_slide','v12_closet_slide']){const group=new THREE.Group();group.name=name;root.add(group);}for(const m of roomJson.materials){const material=new THREE.MeshStandardMaterial();material.name=m.name;root.getObjectByName('hero_props').add(new THREE.Mesh(new THREE.BoxGeometry(.1,.1,.1),material));}return root;}
 GLTFLoader.prototype.parseAsync=async bytes=>{const {part}=JSON.parse(new TextDecoder().decode(bytes));if(part===BEDROOM_PART)return{scene:room(),animations:[]};const scene=new THREE.Group();const mesh=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial());if(part.startsWith('actors/'))mesh.name='actor_'+part.split('/')[1].replace('-v11','');scene.add(mesh);return{scene,animations:[]};};
 THREE.TextureLoader.prototype.loadAsync=async()=>new THREE.Texture();
 const e=engine();await e.load();assert.equal(e.state.error,null);assert.equal(e.loadedForFrame,true);assert.equal(e.state.ready,false);assert(!requested.some(url=>url.includes(BEDROOM_PART)||url.includes('bedroom-materials')));assert.equal(requested.filter(url=>url.includes('.glb')).length,STARTUP_PARTS.length);
 e.state.ready=true;e.queueBedroom();assert(!requested.some(url=>url.includes(BEDROOM_PART)));await delay(1550);assert.equal(e.state.bedroom.status,'loading');assert.equal(e.state.ready,true);assert.equal(e.world.getObjectByName('hero_props'),undefined);
 const entry=e.teleport('bedroom');assert.equal(e.state.floor,0);assert.equal(e.state.bedroom.requested,true);e.cancelBedroomEntry();releaseMaterials();holdMaterials=false;assert.equal(await entry,false);assert.equal(e.state.floor,0);assert.equal(e.state.bedroom.status,'ready');assert(e.world.getObjectByName('hero_props'));assert.equal(e.slidingDoors.length,2);
 const total=requested.length;assert(await e.teleport('bedroom'));assert.equal(e.state.floor,1);assert.equal(e.yaw,Math.PI);e.enterHome();assert(await e.teleport('bedroom'));assert.equal(requested.length,total);assert.equal(e.slidingDoors.length,2);
 // Slow room: a newer destination wins, including a staircase attempt.
 const slow=engine();slow.state.ready=true;slow.modelLoader={};let resolveRoom;let attempts=0;slow.loadBedroom=async()=>{attempts++;return await new Promise(r=>resolveRoom=()=>{slow.state.bedroom.status='ready';slow.state.bedroom.requested=false;r(true);});};
 const pending=slow.teleport('bedroom');assert.equal(slow.state.floor,0);slow.enterShizuka();resolveRoom();assert.equal(await pending,false);assert.equal(slow.state.house,'shizuka');assert.equal(attempts,1);
 slow.state.bedroom.status='idle';slow.state.house='home';slow.state.inside=true;slow.state.floor=0;slow.colliders=[];
 const stairY=HOUSE.stairY0+(2.69-HOUSE.lower)/(HOUSE.upper-HOUSE.lower)*(HOUSE.stairY1-HOUSE.stairY0);slow.playerPosition.set(HOUSE.stairX,2.69,-stairY);slow.keys.add('KeyW');slow.move(.05);assert(slow.playerPosition.y<=2.7);assert.equal(slow.state.bedroom.requested,true);slow.cancelBedroomEntry();resolveRoom();await slow.bedroomTask;
 // Room failure leaves the street usable and retry starts a single new attempt.
 const fail=engine();fail.state.ready=true;fail.modelLoader={parseAsync:async()=>{throw Error('decode failed');}};const warn=console.warn;console.warn=()=>{};assert.equal(await fail.teleport('bedroom'),false);console.warn=warn;assert.equal(fail.state.ready,true);assert.equal(fail.state.error,null);assert.equal(fail.state.bedroom.status,'error');assert.equal(fail.state.floor,0);fail.modelLoader=new GLTFLoader();assert(await fail.teleport('bedroom'));assert.equal(fail.slidingDoors.length,2);
 // Invalid cached metadata is evicted so a retry can recover without clearing storage.
 cache=memoryCache();global.caches={open:async()=>cache};const manifestUrl='/frank_worlds/bedroom-materials/manifest.json?v='+ASSET_VERSION;await cache.put(manifestUrl,new Response('invalid json'));
 const badManifest=engine();badManifest.state.ready=true;badManifest.modelLoader=new GLTFLoader();console.warn=()=>{};assert.equal(await badManifest.teleport('bedroom'),false);console.warn=warn;assert(!cache.saved.has(manifestUrl));assert(await badManifest.teleport('bedroom'));await settleAssetCache();
 const startupModelBytes=STARTUP_PARTS.reduce((n,p)=>n+fs.statSync('public/models/'+p+'.glb').size,fs.statSync('public/models/world.json').size);
 const uniqueMaterials=[...new Set(materialRequests)].map(url=>new URL(url,'https://test.invalid').pathname.replace('/frank_worlds/',''));
 const deferredMaterialBytes=uniqueMaterials.reduce((n,p)=>n+fs.statSync('public/'+p).size,fs.statSync('public/bedroom-materials/manifest.json').size);
 const previousBlockingBytes=startupModelBytes+b.length+deferredMaterialBytes;
 const report={startupModelBytes,deferredModelBytes:b.length,deferredMaterialBytes,previousBlockingBytes,blockingByteReduction:1-startupModelBytes/previousBlockingBytes,materialFiles:uniqueMaterials.length,cacheColdWarmOffline:true,cacheQuotaFallback:true,failedResponsesNotCached:true,abortSupported:true,startupDoesNotRequestBedroom:true,backgroundDoesNotBlockTown:true,noPartialRoom:true,cancelAndNewDestinationWin:true,stairsWaitSafely:true,repeatedEntryReusesScene:true,roomFailureAndRetry:true,originalBedroomAssetVersion:ASSET_VERSION};
 fs.mkdirSync('.test-build',{recursive:true});fs.writeFileSync('.test-build/loading-report.json',JSON.stringify(report,null,2));console.log('PASS: asset cache and deferred room integration',report);
 for(const instance of [e,slow,fail])for(const dispose of instance.disposers)dispose();
 }finally{global.fetch=realFetch;delete global.caches;THREE.TextureLoader.prototype.loadAsync=realDecode;GLTFLoader.prototype.parseAsync=realParse;}})().catch(e=>{console.error(e);process.exitCode=1;});
