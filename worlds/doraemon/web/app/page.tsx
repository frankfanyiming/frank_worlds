'use client';
import {assetPath} from '@/lib/town/asset-path';
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
export default function Page(){
 const canvas=useRef<HTMLDivElement>(null),engine=useRef<TownEngine|null>(null);const [s,setS]=useState(initial),[panel,setPanel]=useState<'settings'|'pocket'|null>(null),[quality,setQuality]=useState(false),[dialogLine,setDialogLine]=useState(0),[help,setHelp]=useState(false);
 useEffect(()=>{let disposed=false;let unregister=()=>{};import('@/lib/town/engine').then(({TownEngine})=>{if(disposed||!canvas.current)return;try{engine.current=new TownEngine(canvas.current,setS);setQuality(engine.current.quality);unregister=registerTownTools(engine.current);}catch(e){console.error(e);setS(v=>({...v,error:'无法启动 3D 画面。请使用支持 WebGL 2 的浏览器，并开启图形加速。'}));}}).catch(e=>{console.error(e);setS(v=>({...v,error:'程序没有下载完成，请检查网络后重新载入。'}));});return()=>{disposed=true;unregister();engine.current?.destroy();engine.current=null;}},[]);
 useEffect(()=>engine.current?.setPaused(!!panel||help),[panel,help]);
 useEffect(()=>setDialogLine(0),[s.actor?.id]);
 const go=(id:PlaceId)=>{engine.current?.teleport(id);setPanel(null);};
 return <main className={'town-app '+(s.mode==='first'?'first-person':'')}>
  <div className="world-canvas" ref={canvas}/><div className="viewport-shade" aria-hidden="true"/>
  <header className="topbar">
   <div className="camera-switch"><Tabs value={s.mode} onValueChange={v=>engine.current?.setMode(v as 'orbit'|'first')}><TabsList aria-label="探索视角"><TabsTrigger value="orbit"><View size={17}/>45° 小镇</TabsTrigger><TabsTrigger value="first"><Footprints size={17}/>第一人称</TabsTrigger></TabsList></Tabs></div>
   <button className="day-chip" onClick={()=>setPanel('settings')} aria-label="调整时间和四季">{s.weather?.night?<Moon size={23}/>:<Sun size={23}/>} <div><b>{s.weather?.time??'15:30'}</b><span>{(SEASONS.find(v=>v.id===s.weather?.season)?.name??'夏')+'日 · '+(s.weather?.night?'夜色':'晴空')}</span></div><i/></button>
  </header>
  {s.ready&&<>
  <nav className="side-tools" aria-label="探索工具">
   <button onClick={()=>setPanel('pocket')} title="道具与小冒险"><Gift/><span>口袋</span></button>
   <button className={s.cutaway?'active':''} onClick={()=>engine.current?.toggleCutaway()} title="查看大雄家剖面" aria-pressed={s.cutaway}><Layers/><span>剖面</span></button>
   <button onClick={()=>engine.current?.showTown()} title="鸟瞰全镇"><Maximize/><span>全镇</span></button>
   <button onClick={()=>setPanel('settings')} title="光照与画质"><SlidersHorizontal/><span>设置</span></button>
  </nav>
  {(s.inside||s.cutaway)&&s.mode==='orbit'&&<div className="floor-switch"><span>{s.house==='shizuka'?'静香家':'野比家'}</span><button className={s.floor===0?'chosen':''} onClick={()=>engine.current?.setFloor(0)}>一楼</button><button className={s.floor===1?'chosen':''} onClick={()=>engine.current?.setFloor(1)}>二楼</button></div>}
  <AdventureHUD s={s} engine={engine.current}/><div className="walk-guide"><span><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>行走</span><i/><span><MousePointer2 size={15}/>{s.mode==='orbit'?'拖动环视 · 滚轮缩放':'拖动环视'}</span><i/><span><kbd>V</kbd>切换视角</span><button title="查看完整操作" onClick={()=>setHelp(true)}>?</button></div>
  {s.near&&!s.actor&&<button className="interaction-prompt" onClick={()=>engine.current?.interact()}><kbd>E</kbd>{s.near}<span>↗</span></button>}
  {s.mode==='first'&&<div className="crosshair" aria-hidden="true">+</div>}
  <div className="touch-pad" aria-label="触屏行走控制">{[['forward',0,-1,ArrowUp],['left',-1,0,ArrowLeft],['back',0,1,ArrowDown],['right',1,0,ArrowRight]].map(([id,x,y,Icon])=>{const I=Icon as typeof ArrowUp;return <button key={String(id)} className={String(id)} aria-label={id==='forward'?'前进':id==='left'?'左移':id==='back'?'后退':'右移'} onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);engine.current?.setTouch(Number(x),Number(y));}} onPointerUp={()=>engine.current?.setTouch(0,0)} onPointerCancel={()=>engine.current?.setTouch(0,0)}><I size={22}/></button>;})}</div>
  </>}
  {s.ready&&s.bedroom?.requested&&<div className="room-loading" role="status" aria-live="polite"><b>{s.bedroom.status==='error'?'房间暂时没有打开':'正在准备大雄的房间'}</b><p>{s.bedroom.error??'稍等一下，窗帘、榻榻米和书桌正在就位。'}</p>{s.bedroom.status!=='error'&&<><Progress value={s.bedroom.progress} aria-label="房间加载进度"/><span>{s.bedroom.progress}%</span></>}<div>{s.bedroom.status==='error'&&<button className="primary-action" onClick={()=>engine.current?.retryBedroomEntry()}>重试</button>}<button className="text-action" onClick={()=>engine.current?.cancelBedroomEntry()}>先逛小镇</button></div></div>}
  {!s.ready&&!s.error&&<div className="loading-screen"><div className="loading-orbit" aria-hidden="true"><img src={assetPath('/doraemon-loading.png')} alt="" width="80" height="80"/></div><h2>来一起共建有趣的小世界吧</h2><p role="status">{s.loadingStage??'正在打开小世界'}</p><Progress value={s.progress} className="load-progress" aria-label="小镇加载进度"/><span className="load-percent">{s.progress}%</span><button className="text-action" onClick={()=>{const url=new URL(location.href);url.searchParams.set('safe','1');location.assign(url);}}>设备较慢？使用流畅模式</button></div>}
  {s.error&&<div className="loading-screen"><h2>小镇暂时没有打开</h2><p role="alert">{s.error}</p><div className="recovery-actions"><button className="primary-action" onClick={()=>location.reload()}><RotateCcw size={16}/>重新载入</button><button className="primary-action" onClick={()=>{const url=new URL(location.href);url.searchParams.set('safe','1');location.assign(url);}}>使用流畅模式</button></div><p>如果在聊天应用内打不开，可复制网址到 Safari、Chrome 或 Edge。若仍无响应，尝试切换 Wi-Fi / 移动网络。</p></div>}
  <Pocket open={panel==='pocket'} onClose={()=>setPanel(null)} s={s} engine={engine.current}/>

  <Dialog open={panel==='settings'} onOpenChange={v=>!v&&setPanel(null)}><DialogContent className="settings-dialog"><DialogHeader><DialogTitle>小镇的此刻</DialogTitle><DialogDescription>四季、昼夜，还有街巷里的声音。</DialogDescription></DialogHeader><WorldSettings s={s} engine={engine.current}/><div className="setting-row"><div><b>细腻光影</b><p>接触阴影与更清晰的画面</p></div><Switch checked={quality} onCheckedChange={v=>{setQuality(v);engine.current?.setQuality(v)}} aria-label="细腻光影"/></div><button className="reset-btn" onClick={()=>{go('home');engine.current?.setMode('orbit');setPanel(null)}}><RotateCcw size={16}/>回到大雄家门前</button></DialogContent></Dialog>
  <Dialog open={!!s.actor} onOpenChange={v=>{if(!v)engine.current?.closeDialogue()}}><DialogContent className="dialogue-box"><DialogHeader><div className="dialogue-name"><span style={{background:s.actor?.color}}><MessageCircle size={19}/></span><DialogTitle>{s.actor?.name}</DialogTitle></div><DialogDescription className="dialogue-line">{s.actor?.lines[dialogLine%s.actor.lines.length]}</DialogDescription></DialogHeader><TalkActions s={s} engine={engine.current}/><div className="dialogue-footer"><span>{dialogLine+1} / {s.actor?.lines.length}</span><button className="primary-action" onClick={()=>{if(s.actor&&dialogLine<s.actor.lines.length-1)setDialogLine(v=>v+1);else engine.current?.closeDialogue()}}>{s.actor&&dialogLine<s.actor.lines.length-1?'再聊一句':'继续散步'}<ArrowRight size={16}/></button></div></DialogContent></Dialog>
  <Dialog open={help} onOpenChange={setHelp}><DialogContent className="settings-dialog"><DialogHeader><DialogTitle>在小镇里散步</DialogTitle><DialogDescription>随时切换视角，按自己的节奏探索。</DialogDescription></DialogHeader><div className="help-lines"><p><kbd>W A S D</kbd>或方向键行走，按住 Shift 跑步</p><p><kbd>鼠标拖动</kbd>转动视角，俯视时滚轮缩放</p><p><kbd>点击地面</kbd>向那个位置行走，遇到障碍停下</p><p><kbd>V</kbd>切换第一人称与 45° 视角</p><p><kbd>E</kbd>与身边的人聊天、进屋、上下楼</p><p><kbd>R</kbd>查看大雄家的屋内剖面</p><p><kbd>空格 / Ctrl</kbd>竹蜻蜓上升 / 下降，C 安全着陆</p><p><kbd>空格</kbd>棒球挑战里挥棒或投球</p><p>靠近门口按 E 进出房屋；口袋里的任意门可以前往其他地点。</p></div></DialogContent></Dialog>
 </main>;
}
