import {collides, groundHeight, insideHouse, type Collider, type GroundSurface} from './world';

export type Point={x:number;y:number};
export type Routine={id:string;speed:number;stops:Point[];wait:number;zone:'outside'|'kitchen'|'living'};
const p=(x:number,y:number)=>({x,y});
export const ROUTINES:Routine[]=[
 {id:'doraemon',speed:.28,wait:4,zone:'outside',stops:[p(-11,-6.5),p(-15,-6.5),p(-18,-7.7),p(-10,-7.8),p(-8.3,-6.6)]},
 {id:'shizuka',speed:.52,wait:7,zone:'outside',stops:[p(-9,-24),p(-13,-24),p(-16,-24),p(-15,-23),p(-10,-23.6)]},
 {id:'gian',speed:.57,wait:3,zone:'outside',stops:[p(17,2),p(19,4),p(21,1),p(19,-1),p(16,-1)]},
 {id:'suneo',speed:.51,wait:6,zone:'outside',stops:[p(13,1),p(15,-1),p(18,-2),p(17,1),p(12,3)]},
 {id:'tamako',speed:.55,wait:8,zone:'kitchen',stops:[p(-12.05,6.05),p(-12.4,7.05),p(-11.2,7.45),p(-9.5,7.3),p(-9.55,6.1)]},
 {id:'nobisuke',speed:.55,wait:11,zone:'living',stops:[p(-16.4,2.2),p(-16.45,2.65),p(-14.1,2.6),p(-14.1,1.1),p(-15.5,.8)]},
];
export function allowed(p:Point,r:Routine,cs:Collider[],surfaces:GroundSurface[]){
 const z=groundHeight(p.x,p.y,.48,surfaces);
 if(r.zone==='outside'&&insideHouse(p.x,p.y))return false;
 if(r.zone==='kitchen'&&(p.x< -12.5||p.x> -9.35||p.y<5.9||p.y>7.6))return false;
 if(r.zone==='living'&&(p.x< -16.65||p.x> -13.85||p.y<.68||p.y>2.8))return false;
 return !collides(p.x,p.y,z,cs,.23);
}
// Small local navigation grids keep each resident on a measured, unobstructed route.
// Every smoothed segment is checked; residents never cut diagonally through furniture.
export function findRoute(start:Point,end:Point,r:Routine,cs:Collider[],surfaces:GroundSurface[]):Point[]{
 const clear=(a:Point,b:Point)=>{const n=Math.ceil(Math.hypot(a.x-b.x,a.y-b.y)/.10);for(let i=1;i<=n;i++)if(!allowed({x:a.x+(b.x-a.x)*i/n,y:a.y+(b.y-a.y)*i/n},r,cs,surfaces))return false;return true;};
 if(!allowed(end,r,cs,surfaces))return [];
 if(clear(start,end))return [end];
 const step=.25,x0=Math.min(start.x,end.x)-2,y0=Math.min(start.y,end.y)-2;
 const w=Math.ceil((Math.abs(start.x-end.x)+4)/step),h=Math.ceil((Math.abs(start.y-end.y)+4)/step);
 const key=(x:number,y:number)=>y*w+x,at=(k:number)=>({x:x0+(k%w)*step,y:y0+Math.floor(k/w)*step});
 const index=(p:Point)=>key(Math.round((p.x-x0)/step),Math.round((p.y-y0)/step));
 const first=index(start),last=index(end),open=new Set([first]),came=new Map<number,number>(),g=new Map([[first,0]]);
 let loops=0;
 while(open.size&&loops++<6000){let current=first,best=Infinity;for(const k of open){const v=at(k),score=g.get(k)!+Math.hypot(v.x-end.x,v.y-end.y);if(score<best){best=score;current=k;}}
  if(current===last){const raw:Point[]=[end];let k=current;while(came.has(k)){raw.push(at(k));k=came.get(k)!;}raw.push(start);raw.reverse();const result:Point[]=[];let i=0;while(i<raw.length-1){let j=raw.length-1;while(j>i+1&&!clear(raw[i],raw[j]))j--;result.push(raw[j]);i=j;}return result;}
  open.delete(current);const cx=current%w,cy=Math.floor(current/w);
  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){
   const nx=cx+dx,ny=cy+dy;if(nx<0||nx>=w||ny<0||ny>=h)continue;const k=key(nx,ny),point=at(k);
   if(!clear(at(current),point))continue;const cost=g.get(current)!+Math.hypot(dx,dy)*step;if(cost>=(g.get(k)??Infinity))continue;came.set(k,current);g.set(k,cost);open.add(k);
  }
 }
 return [];
}

export function smoothEdge(distance:number,width:number){const t=Math.max(0,Math.min(1,distance/width));return t*t*(3-2*t);}
