import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';
const source=await readFile(new URL('./native-loader.js',import.meta.url),'utf8');
const install=source.slice(source.indexOf('function installTouchControls()'),source.indexOf('installTouchControls();'));
class Surface {
 constructor(action){this.dataset=action?{action}:{};this.handlers={};this.style={};this.classes=new Set();this.classList={add:n=>this.classes.add(n),remove:n=>this.classes.delete(n),toggle:(n,on)=>on?this.classes.add(n):this.classes.delete(n)};this.captured=new Set();}
 addEventListener(type,fn){(this.handlers[type]??=[]).push(fn);}
 fire(type,id,x=58,y=58){for(const fn of this.handlers[type]??[])fn({pointerId:id,clientX:x,clientY:y,pointerType:'touch',preventDefault(){}});}
 append(...nodes){(this.children??=[]).push(...nodes);} replaceChildren(){this.children=[];} focus(){}
 setPointerCapture(id){this.captured.add(id);} setAttribute(){} getBoundingClientRect(){return{left:0,top:0,width:116,height:116};}
}
const stick=new Surface(),knob=new Surface(),canvas=new Surface(),run=new Surface('run'),jump=new Surface('jump'),interact=new Surface('interact'),view=new Surface('view');
stick.querySelector=()=>knob;
const window=new Surface(),document=new Surface(),moves=[],looks=[],actions=[];
Object.assign(window,{xlandsMove:(x,y)=>moves.push([x,y]),xlandsLook:(x,y)=>looks.push([x,y]),xlandsInput:(...args)=>actions.push(args)});
Object.assign(document,{body:new Surface(),createElement:()=>new Surface(),querySelector:id=>id==='#touch-stick'?stick:canvas,querySelectorAll:selector=>selector==='[data-action]'?[run,jump,interact,view]:[],hidden:false});
runInNewContext(install+'\ninstallTouchControls();',{window,document,lang:'en',Math,Set,Map});
stick.fire('pointerdown',1,58,16);assert(moves.at(-1)[1]<-.99);
canvas.fire('pointerdown',2,160,140);canvas.fire('pointermove',2,187,131);assert.deepEqual(looks.at(-1),[27,-9]);
run.fire('pointerdown',3);jump.fire('pointerdown',4);assert(actions.some(a=>a[0]==='run'&&a[1]));assert(actions.some(a=>a[0]==='jump'&&a[1]));
// Releasing a camera or action finger must not release the moving finger.
canvas.fire('pointerup',2);jump.fire('pointerup',4);assert(moves.at(-1)[1]<-.99);
stick.fire('pointerdown',9,100,58);stick.fire('pointercancel',9);assert(moves.at(-1)[1]<-.99);
stick.fire('pointermove',1,100,58);assert(moves.at(-1)[0]>.99);assert.equal(moves.at(-1)[1],0);
run.fire('pointerdown',8);run.fire('pointerup',3);assert.equal(actions.filter(a=>a[0]==='run').at(-1)[1],true);run.fire('pointercancel',8);assert.equal(actions.filter(a=>a[0]==='run').at(-1)[1],false);
stick.fire('lostpointercapture',1);assert.deepEqual(moves.at(-1),[0,0]);
stick.fire('pointerdown',12,58,16);run.fire('pointerdown',13);window.fire('blur',0);assert.deepEqual(moves.at(-1),[0,0]);assert(actions.slice(-4).every(a=>a[1]===false));
stick.fire('pointerdown',14,58,16);document.hidden=true;document.fire('visibilitychange',0);assert.deepEqual(moves.at(-1),[0,0]);
stick.fire('pointerdown',21,58,16);run.fire('pointerdown',22);
window.xlandsMenu({title:'Destinations',items:[{id:25,text:'Kitchen',separator:false}]});
assert(document.body.classes.has('world-ui-open'));assert.deepEqual(moves.at(-1),[0,0]);
const moveCount=moves.length,lookCount=looks.length;stick.fire('pointerdown',23,58,16);canvas.fire('pointerdown',24,100,100);canvas.fire('pointermove',24,120,150);
assert.equal(moves.length,moveCount);assert.equal(looks.length,lookCount);
window.xlandsMenu(null);assert(!document.body.classes.has('world-ui-open'));
stick.fire('pointerdown',25,58,16);assert(moves.at(-1)[1]<-.99);
window.xlandsOverlayLocked(true);assert.deepEqual(moves.at(-1),[0,0]);window.xlandsOverlayLocked(false);
console.log('PASS: menus and panels release controls, block camera and restore input');
console.log('PASS: native four simultaneous pointers, independent release, wrong-pointer rejection, cancel, capture loss, blur and hidden-page cleanup');
