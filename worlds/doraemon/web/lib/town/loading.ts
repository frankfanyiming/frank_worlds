/** Progress follows completed downloads AND decoding, never compressed Content-Length. */
export class LoadProgress {
 private values:number[]; private last=0;
 constructor(count:number,private report:(value:number)=>void){this.values=Array(count).fill(0);}
 update(index:number,value:number){this.values[index]=Math.max(this.values[index],Math.min(1,Math.max(0,Number.isFinite(value)?value:0)));this.set(this.values.reduce((a,b)=>a+b,0)/this.values.length*90);}
 stage(value:number){this.set(value);}
 private set(value:number){this.last=Math.max(this.last,Math.min(100,Math.floor(value)));this.report(this.last);}
}
export async function boundedMap<T,R>(items:T[],limit:number,run:(item:T,index:number)=>Promise<R>):Promise<R[]>{
 const out:R[]=new Array(items.length);let next=0;let failed=false;
 await Promise.all(Array.from({length:Math.min(limit,items.length)},async()=>{while(!failed&&next<items.length){const i=next++;try{out[i]=await run(items[i],i);}catch(e){failed=true;throw e;}}}));return out;
}
export async function withDeadline<T>(work:Promise<T>,ms:number,label:string):Promise<T>{
 let timer:ReturnType<typeof setTimeout>;try{return await Promise.race([work,new Promise<T>((_,reject)=>{timer=setTimeout(()=>reject(new Error(label+'超时，请检查网络后重试。')),ms);})]);}finally{clearTimeout(timer!);}
}
export async function fetchBytes(url:string,signal:AbortSignal):Promise<ArrayBuffer>{
 // Abort the actual network request on timeout; a timed-out Promise alone leaks downloads.
 const local=new AbortController(),abort=()=>local.abort();signal.addEventListener('abort',abort,{once:true});
 const timer=setTimeout(abort,90000);try{if(signal.aborted)abort();const r=await fetch(url,{signal:local.signal});if(!r.ok)throw new Error('资源请求失败（'+r.status+'）');return await r.arrayBuffer();}finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
}
