import {assetPath} from './asset-path';
export type AudioState={enabled:boolean;music:number;ambience:number;track:string;error:string};
export const INITIAL_AUDIO:AudioState={enabled:false,music:.28,ambience:.45,track:'原创 · 夏日口袋散步',error:''};
// Playback starts only from a deliberate user gesture. All audio stays local.
export class TownSound {
 state={...INITIAL_AUDIO};tracks=new Map<string,HTMLAudioElement>();customUrl='';
 constructor(){try{const p=JSON.parse(localStorage.getItem('town-audio-v1')??'{}');for(const k of ['music','ambience'] as const)if(typeof p[k]==='number')this.state[k]=Math.max(0,Math.min(1,p[k]));}catch{}}
 get(id:string,loop=false){let a=this.tracks.get(id);if(!a){a=new Audio(assetPath('/audio/'+id+'.m4a'));a.loop=loop;a.preload='none';this.tracks.set(id,a);}return a;}
 async enable(value=true){this.state.enabled=value;this.state.error='';if(!value){this.tracks.forEach(a=>a.pause());return;}
  // Unlock the environmental layers in the same activation as music.
  let played=0;await Promise.all(['music','wind','birds','cicadas','crickets','bamboo'].map(async id=>{const a=this.get(id,true);a.volume=id==='music'?this.state.music:0;try{await a.play();played++;}catch{this.state.error='部分声音未开始，可关闭后重新开启。';}}));if(!played){this.state.enabled=false;this.state.error='声音未开始，请点开启重试。';}
 }
 volume(kind:'music'|'ambience',v:number){this.state[kind]=Math.max(0,Math.min(1,v));try{localStorage.setItem('town-audio-v1',JSON.stringify({music:this.state.music,ambience:this.state.ambience}));}catch{}}
 importMusic(file:File){if(!file.type.startsWith('audio/')){this.state.error='请选择音频文件';return;}const old=this.tracks.get('music');old?.pause();if(this.customUrl)URL.revokeObjectURL(this.customUrl);this.customUrl=URL.createObjectURL(file);const a=new Audio(this.customUrl);a.loop=true;this.tracks.set('music',a);this.state.track=file.name;void this.enable(true);}
 effect(id:string){if(!this.state.enabled)return;const a=this.get(id,id==='bamboo');a.volume=Math.min(.48,this.state.ambience*.8);if(id!=='bamboo')a.currentTime=0;void a.play().catch(()=>{});}
 stop(id:string){this.tracks.get(id)?.pause();}
 update(dt:number,season:string,hour:number,inside:boolean,flying:boolean,nightOverride?:boolean){if(!this.state.enabled)return;const night=nightOverride??(hour<6||hour>=19);const desired:Record<string,number>={music:this.state.music,wind:this.state.ambience*(inside?.12:.42),birds:this.state.ambience*(!night&&season!=='winter'?(inside?.07:.55):0),cicadas:this.state.ambience*(season==='summer'&&!night?(inside?.035:.14):0),crickets:this.state.ambience*(night&&season!=='winter'?(inside?.045:.33):0),bamboo:flying?this.state.ambience*.32:0};const rotor=this.get('bamboo',true);if(flying&&rotor.paused)void rotor.play().catch(()=>{});if(!flying&&!rotor.paused)rotor.pause();for(const [id,a] of this.tracks){if(id in desired)a.volume+= (desired[id]-a.volume)*Math.min(1,dt*2);}}
 snapshot(){return{...this.state};}
 dispose(){this.tracks.forEach(a=>{a.pause();a.src='';});if(this.customUrl)URL.revokeObjectURL(this.customUrl);}
}
