/** Keep touch resolution independent of expensive lighting and device DPR. */
export class RenderBudget {
 readonly mobile:boolean;
 ratio:number;
 private maxRatio:number;
 private elapsed=0;
 private slow=0;
 private fast=0;
 private cooldown=0;
 constructor(mobile:boolean,dpr:number){this.mobile=mobile;this.maxRatio=Math.min(dpr,1);this.ratio=mobile?this.maxRatio:Math.min(dpr,1.5);}
 /** Mobile prioritises a steady 30 fps and leaves time for touch + browser UI. */
 shouldPaint(now:number,last:number,paused:boolean){return now-last >= (paused?125:this.mobile?1000/30-1:0);}
 pixelRatio(width:number,height:number){return this.mobile?Math.min(this.ratio,Math.sqrt(480000/Math.max(1,width*height))):this.ratio;}
 sample(seconds:number,active:boolean):number|undefined {
  if(!this.mobile||!active||seconds<=0||seconds>.15){this.elapsed=0;this.slow=0;this.fast=0;return;}
  this.cooldown=Math.max(0,this.cooldown-seconds);this.elapsed+=seconds;
  if(seconds>1/25)this.slow+=seconds;
  if(seconds<1/28)this.fast+=seconds;
  if(this.elapsed<3)return;
  const down=this.slow/this.elapsed>.40,up=this.fast/this.elapsed>.96;
  this.elapsed=0;this.slow=0;this.fast=0;
  if(this.cooldown>0)return;
  const next=down?Math.max(Math.min(.7,this.maxRatio),this.ratio-.1):up?Math.min(this.maxRatio,this.ratio+.05):this.ratio;
  if(Math.abs(next-this.ratio)<.01)return;
  this.ratio=Math.round(next*100)/100;this.cooldown=down?5:15;return this.ratio;
 }
}
