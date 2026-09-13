/** Keep touch resolution independent of expensive lighting and device DPR. */
export class RenderBudget {
 readonly mobile:boolean;
 ratio:number;
 private maxRatio:number;
 private elapsed=0;
 private slow=0;
 private fast=0;
 private cooldown=0;
 constructor(mobile:boolean,dpr:number){this.mobile=mobile;this.maxRatio=Math.min(dpr,1.35);this.ratio=mobile?this.maxRatio:Math.min(dpr,1.5);}
 sample(seconds:number,active:boolean):number|undefined {
  if(!this.mobile||!active||seconds<=0||seconds>.15){this.elapsed=0;this.slow=0;this.fast=0;return;}
  this.cooldown=Math.max(0,this.cooldown-seconds);this.elapsed+=seconds;
  if(seconds>1/42)this.slow+=seconds;
  if(seconds<1/55)this.fast+=seconds;
  if(this.elapsed<3)return;
  const down=this.slow/this.elapsed>.40,up=this.fast/this.elapsed>.96;
  this.elapsed=0;this.slow=0;this.fast=0;
  if(this.cooldown>0)return;
  const next=down?Math.max(Math.min(1,this.maxRatio),this.ratio-.15):up?Math.min(this.maxRatio,this.ratio+.1):this.ratio;
  if(Math.abs(next-this.ratio)<.01)return;
  this.ratio=next;this.cooldown=down?5:15;return next;
 }
}
