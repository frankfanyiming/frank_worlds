'use client';
import {useEffect,useRef,useState} from 'react';
import {Waves,Mountain,Landmark,Moon,Gift,Hand,Bell,Sun,Sunset,Home,Footprints,Map,Layers,ArrowUpRight,ArrowUp,ArrowDown,ArrowLeft,ArrowRight,MousePointer2,Compass,SlidersHorizontal,X,Maximize,MessageCircle,DoorOpen,RotateCcw,View,TrainFront,School,TreePine,Navigation,BookOpen} from 'lucide-react';
import {Tabs,TabsList,TabsTrigger} from '@/components/ui/tabs';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import {Progress} from '@/components/ui/progress';
import {Switch} from '@/components/ui/switch';
import {PLACES,type PlaceId} from '@/lib/town/world';
import type {TownEngine,TownState} from '@/lib/town/engine';
import {registerTownTools} from '@/lib/town/webmcp';
import {Pocket,TalkActions,AdventureHUD,WorldSettings} from '@/components/Adventure';
import {SEASONS} from '@/lib/town/weather';
const initial:TownState={ready:false,progress:0,mode:'orbit',inside:false,floor:0,cutaway:false,place:'home',position:{x:-9.6,y:-6.3},near:'',actor:null,sunset:false,error:null};
const iconFor=(id:string)=>id==='school'?School:id==='station'?TrainFront:id==='lot'?TreePine:id==='bedroom'?BookOpen:id==='river'?Waves:id==='hill'?Mountain:id==='bridge'?Landmark:Home;
function TownMap({position,onGo,large=false}:{position:{x:number;y:number};onGo:(id:PlaceId)=>void;large?:boolean}){
 const px=(x:number)=>(x+45)/90*300,py=(y:number)=>(43-y)/144*430;
 const rect=(x:number,y:number,w:number,d:number)=>({x:px(x),y:py(y+d),width:w/90*300,height:d/144*430});
 return <div className={'town-map '+(large?'map-large':'')}>
 <svg viewBox="0 0 300 430" role="img" aria-label="小镇地图：住宅区、学校、河岸、桥与后山。点击地点可前往。"><rect width="300" height="430" rx="12" fill="#e6ebd6"/>
 <ellipse cx={px(10)} cy={py(-78)} rx="88" ry="63" fill="#bccca2"/><ellipse cx={px(10)} cy={py(-78)} rx="59" ry="43" fill="none" stroke="#92ad84" strokeWidth="1"/><ellipse cx={px(10)} cy={py(-78)} rx="30" ry="22" fill="none" stroke="#92ad84" strokeWidth="1"/>
 {[[-45,-10.5,90,5],[-1.5,-30.25,5,69.75],[-45,17.75,90,4.5],[-45,-30.25,90,4.5],[-29,-10,4,20]].map(([x,y,w,d],i)=><rect key={i} {...rect(x,y,w,d)} fill="#fcfbf1"/>)}
 <path d={`M${px(-44)} ${py(38)}H${px(44)}`} stroke="#aaa58a" strokeWidth="3" strokeDasharray="2 3"/>
 <rect {...rect(5.5,-4.7,21,19.7)} rx="4" fill="#dccda7"/><rect {...rect(5,-34.6,29,23.6)} rx="3" fill="#d6ddc3"/>
 <rect {...rect(6.5,-34.6,27,5.2)} fill="#b5b497"/>
 {[[ -18,.4,10,9.6],[-38,1,8,8],[-38,-22,10,8],[-16,-21.5,8,7],[-34,27,8,7],[-16,27,8,6],[8,26,8,6],[28,25,9,8],[31,-4,7,7],[28,9,7,6],[-15,-37.5,8,5],[-36.5,-37.5,7,5]].map(([x,y,w,d],i)=><rect key={i} {...rect(x,y,w,d)} rx="2" fill={i===0?'#c87e55':'#a8b6a0'} stroke="#7d8c72" strokeWidth=".5"/>)}
 <rect {...rect(-44,-52,88,8)} fill="#80b9c5"/><path d={`M${px(-42)} ${py(-48)}H${px(42)}`} stroke="#cae5df" strokeWidth="1" strokeDasharray="8 7"/>
 <path d={`M${px(-42)} ${py(-42)}H${px(42)}M${px(-42)} ${py(-54)}H${px(42)}`} stroke="#ede3c8" strokeWidth="4"/>
 <rect {...rect(-1,-55,4,24.75)} fill="#eee3c8"/><rect {...rect(-1,-53,4,10)} fill="#c3ac88" stroke="#7c7e6e" strokeWidth="1"/>
 <path d={[[1,-55],[1,-56],[-8,-64],[-10,-73],[0,-81],[10,-78]].map(([x,y],i)=>`${i?'L':'M'}${px(x)} ${py(y)}`).join(' ')} fill="none" stroke="#e9dfc0" strokeWidth="5" strokeLinejoin="round"/>
 {PLACES.filter(p=>p.id!=='bedroom').map(p=><g className="map-pin" key={p.id} role="button" tabIndex={0} aria-label={'前往'+p.title} onClick={()=>onGo(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onGo(p.id)}}} transform={`translate(${px(p.x)},${py(p.y)})`}><circle r={large?7:5} fill={p.id==='home'?'#b66038':'#477360'} stroke="#fffbed" strokeWidth="2"/>{large&&<text x={p.id==='river'?-12:p.id==='bridge'?14:0} y={p.id==='river'||p.id==='bridge'?4:-13} textAnchor={p.id==='river'?'end':p.id==='bridge'?'start':'middle'}>{p.title}</text>}</g>)}
 <g transform={`translate(${px(position.x)},${py(position.y)})`}><circle r="8" fill="#f2b844" opacity=".35"/><circle r="3.5" fill="#e5a023" stroke="#fff" strokeWidth="1.3"/></g><text x="270" y="413" fill="#6c806a" fontSize="12">N ↑</text></svg>
 </div>;
}

export default function Page(){
 const canvas=useRef<HTMLDivElement>(null),engine=useRef<TownEngine|null>(null);const [s,setS]=useState(initial),[panel,setPanel]=useState<'map'|'settings'|'pocket'|null>(null),[quality,setQuality]=useState(true),[dialogLine,setDialogLine]=useState(0),[help,setHelp]=useState(false);
 useEffect(()=>{let disposed=false;let unregister=()=>{};import('@/lib/town/engine').then(({TownEngine})=>{if(disposed||!canvas.current)return;try{engine.current=new TownEngine(canvas.current,setS);unregister=registerTownTools(engine.current);}catch(e){console.error(e);setS(v=>({...v,error:'无法启动 3D 画面。请使用支持 WebGL 2 的浏览器，并开启图形加速。'}));}});return()=>{disposed=true;unregister();engine.current?.destroy();engine.current=null;}},[]);
 useEffect(()=>engine.current?.setPaused(!!panel||help),[panel,help]);
 useEffect(()=>setDialogLine(0),[s.actor?.id]);
 const place=PLACES.find(p=>p.id===s.place)??PLACES[0];
 const go=(id:PlaceId)=>{engine.current?.teleport(id);setPanel(null);};
 return <main className={'town-app '+(s.mode==='first'?'first-person':'')}>
  <div className="world-canvas" ref={canvas}/><div className="viewport-shade" aria-hidden="true"/>
  <header className="topbar">
   <div className="brand"><div className="brand-mark"><Bell size={24} strokeWidth={1.5}/></div><div><a className="eyebrow creator-signature" href="https://github.com/frankfanyiming/frank_worlds" target="_blank" rel="noopener noreferrer" title="frank 小世界 · 一起共建">frank 小世界</a><h1>那个夏天<span>。</span></h1><p>哆啦A梦的小镇</p></div></div>
   <div className="camera-switch"><Tabs value={s.mode} onValueChange={v=>engine.current?.setMode(v as 'orbit'|'first')}><TabsList aria-label="探索视角"><TabsTrigger value="orbit"><View size={17}/>45° 小镇</TabsTrigger><TabsTrigger value="first"><Footprints size={17}/>第一人称</TabsTrigger></TabsList></Tabs></div>
   <button className="day-chip" onClick={()=>setPanel('settings')} aria-label="调整时间和四季">{s.weather?.night?<Moon size={23}/>:<Sun size={23}/>} <div><b>{s.weather?.time??'15:30'}</b><span>{(SEASONS.find(v=>v.id===s.weather?.season)?.name??'夏')+'日 · '+(s.weather?.night?'夜色':'晴空')}</span></div><i/></button>
  </header>
  {s.ready&&<>
  <nav className="side-tools" aria-label="探索工具">
   <button onClick={()=>setPanel('pocket')} title="道具与小冒险"><Gift/><span>口袋</span></button>
   <button onClick={()=>engine.current?.wave()} title="挥手打招呼 · H"><Hand/><span>招手</span></button>
   <button className={panel==='map'?'active':''} onClick={()=>setPanel('map')} title="小镇地图"><Map/><span>地图</span></button>
   <button className={s.cutaway?'active':''} onClick={()=>engine.current?.toggleCutaway()} title="查看大雄家剖面" aria-pressed={s.cutaway}><Layers/><span>剖面</span></button>
   <button onClick={()=>engine.current?.showTown()} title="鸟瞰全镇"><Maximize/><span>全镇</span></button>
   <button onClick={()=>setPanel('settings')} title="光照与画质"><SlidersHorizontal/><span>设置</span></button>
  </nav>
  {(s.inside||s.cutaway)&&s.mode==='orbit'&&<div className="floor-switch"><span>野比家</span><button className={s.floor===0?'chosen':''} onClick={()=>engine.current?.setFloor(0)}>一楼</button><button className={s.floor===1?'chosen':''} onClick={()=>engine.current?.setFloor(1)}>二楼</button></div>}
  <section className="location-card" aria-label="当前位置"><div className="location-top"><span className="tiny-compass"><Compass size={16}/></span><span>{s.inside?'屋内漫游':'小镇漫游'}</span><span className="location-index">{String(PLACES.indexOf(place)+1).padStart(2,'0')} / {String(PLACES.length).padStart(2,'0')}</span></div><h2>{place.title}</h2><p>{place.description}</p><div className="place-actions">{s.place==='home'&&!s.inside?<button className="primary-action" onClick={()=>engine.current?.enterHome()}><DoorOpen size={16}/>进屋看看<ArrowUpRight size={16}/></button>:s.floor===1?<button className="primary-action" onClick={()=>engine.current?.setMode('first')}><Footprints size={16}/>走到窗边<ArrowUpRight size={16}/></button>:<button className="primary-action" onClick={()=>setPanel('map')}><Map size={16}/>继续探索<ArrowUpRight size={16}/></button>}{s.place==='home'&&<button className="text-action" onClick={()=>go('bedroom')}>去二楼</button>}</div></section>
  <aside className="minimap"><div className="minimap-head"><span>月见台 · 街巷与后山</span><button onClick={()=>setPanel('map')} title="展开地图"><ArrowUpRight size={17}/></button></div><TownMap position={s.position} onGo={go}/><div className="minimap-foot"><i/>你在这里<span>点击地点前往</span></div></aside>
  <AdventureHUD s={s} engine={engine.current}/><div className="walk-guide"><span><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>行走</span><i/><span><MousePointer2 size={15}/>{s.mode==='orbit'?'拖动环视 · 滚轮缩放':'拖动环视'}</span><i/><span><kbd>V</kbd>切换视角</span><button title="查看完整操作" onClick={()=>setHelp(true)}>?</button></div>
  {s.near&&!s.actor&&<button className="interaction-prompt" onClick={()=>engine.current?.interact()}><kbd>E</kbd>{s.near}<span>↗</span></button>}
  {s.mode==='first'&&<div className="crosshair" aria-hidden="true">+</div>}
  <div className="touch-pad" aria-label="触屏行走控制">{[['forward',0,-1,ArrowUp],['left',-1,0,ArrowLeft],['back',0,1,ArrowDown],['right',1,0,ArrowRight]].map(([id,x,y,Icon])=>{const I=Icon as typeof ArrowUp;return <button key={String(id)} className={String(id)} aria-label={id==='forward'?'前进':id==='left'?'左移':id==='back'?'后退':'右移'} onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);engine.current?.setTouch(Number(x),Number(y));}} onPointerUp={()=>engine.current?.setTouch(0,0)} onPointerCancel={()=>engine.current?.setTouch(0,0)}><I size={22}/></button>;})}</div>
  </>}
  {!s.ready&&!s.error&&<div className="loading-screen"><div className="loading-bell"><Bell size={32}/></div><span className="eyebrow">月见台 · 夏日午后</span><h2>沿着放学路，回家。</h2><p>正在准备街巷、庭院和房间里的小细节</p><Progress value={s.progress} className="load-progress" aria-label="小镇加载进度"/><span className="load-percent">{s.progress}%</span></div>}
  {s.error&&<div className="loading-screen"><h2>小镇暂时没有打开</h2><p role="alert">{s.error}</p><button className="primary-action" onClick={()=>location.reload()}><RotateCcw size={16}/>重新载入</button></div>}
  <Pocket open={panel==='pocket'} onClose={()=>setPanel(null)} s={s} engine={engine.current}/><Dialog open={panel==='map'} onOpenChange={v=>!v&&setPanel(null)}><DialogContent className="map-dialog"><DialogHeader><span className="eyebrow">THE NEIGHBORHOOD</span><DialogTitle>今天，想去哪里？</DialogTitle><DialogDescription>沿着学校旁的小路，过桥去后山。也可以点击地点直接前往。</DialogDescription></DialogHeader><div className="map-dialog-grid"><TownMap large position={s.position} onGo={go}/><div className="place-list">{PLACES.map(p=>{const I=iconFor(p.id);return <button key={p.id} onClick={()=>go(p.id)} className={p.id===s.place?'selected':''}><I size={19}/><div><b>{p.title}</b><span>{p.subtitle}</span></div><ArrowUpRight size={16}/></button>})}</div></div></DialogContent></Dialog>
  <Dialog open={panel==='settings'} onOpenChange={v=>!v&&setPanel(null)}><DialogContent className="settings-dialog"><DialogHeader><DialogTitle>小镇的此刻</DialogTitle><DialogDescription>四季、昼夜，还有街巷里的声音。</DialogDescription></DialogHeader><WorldSettings s={s} engine={engine.current}/><div className="setting-row"><div><b>细腻光影</b><p>接触阴影与更清晰的画面</p></div><Switch checked={quality} onCheckedChange={v=>{setQuality(v);engine.current?.setQuality(v)}} aria-label="细腻光影"/></div><button className="reset-btn" onClick={()=>{go('home');engine.current?.setMode('orbit');setPanel(null)}}><RotateCcw size={16}/>回到大雄家门前</button></DialogContent></Dialog>
  <Dialog open={!!s.actor} onOpenChange={v=>{if(!v)engine.current?.closeDialogue()}}><DialogContent className="dialogue-box"><DialogHeader><div className="dialogue-name"><span style={{background:s.actor?.color}}><MessageCircle size={19}/></span><DialogTitle>{s.actor?.name}</DialogTitle></div><DialogDescription className="dialogue-line">{s.actor?.lines[dialogLine%s.actor.lines.length]}</DialogDescription></DialogHeader><TalkActions s={s} engine={engine.current}/><div className="dialogue-footer"><span>{dialogLine+1} / {s.actor?.lines.length}</span><button className="primary-action" onClick={()=>{if(s.actor&&dialogLine<s.actor.lines.length-1)setDialogLine(v=>v+1);else engine.current?.closeDialogue()}}>{s.actor&&dialogLine<s.actor.lines.length-1?'再聊一句':'继续散步'}<ArrowRight size={16}/></button></div></DialogContent></Dialog>
  <Dialog open={help} onOpenChange={setHelp}><DialogContent className="settings-dialog"><DialogHeader><DialogTitle>在小镇里散步</DialogTitle><DialogDescription>随时切换视角，按自己的节奏探索。</DialogDescription></DialogHeader><div className="help-lines"><p><kbd>W A S D</kbd>或方向键行走，按住 Shift 跑步</p><p><kbd>鼠标拖动</kbd>转动视角，俯视时滚轮缩放</p><p><kbd>点击地面</kbd>向那个位置行走，遇到障碍停下</p><p><kbd>V</kbd>切换第一人称与 45° 视角</p><p><kbd>E</kbd>与身边的人聊天、进屋、上下楼</p><p><kbd>R</kbd>查看大雄家的屋内剖面</p><p><kbd>H</kbd>挥手打招呼；走路、跑步和待机会自动切换</p><p><kbd>空格 / Ctrl</kbd>竹蜻蜓上升 / 下降，C 安全着陆</p><p><kbd>空格</kbd>棒球挑战里挥棒或投球</p><p>地图上的地点可直接前往。其他住宅以外观和庭院探索为主。</p></div></DialogContent></Dialog>
 </main>;
}
