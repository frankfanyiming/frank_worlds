export type ViewMode = 'orbit' | 'first';
export type PlaceId = 'home' | 'bedroom' | 'lot' | 'shizuka' | 'suneo' | 'gian' | 'school' | 'station' | 'river' | 'bridge' | 'hill';
export const TOWN_BOUNDS={x0:-42.7,x1:42.7,y0:-98.5,y1:38.1};
export function inTown(x:number,y:number,margin=0){return x>TOWN_BOUNDS.x0+margin&&x<TOWN_BOUNDS.x1-margin&&y>TOWN_BOUNDS.y0+margin&&y<TOWN_BOUNDS.y1-margin;}
export type Heightfield={x0:number;y0:number;dx:number;dy:number;nx:number;ny:number;heights:number[]};
export type WalkMesh={name:string;vertices:number[][];triangles:number[][]};
let terrain:Heightfield|undefined;
const walkTriangles=new Map<string,number[][][]>();
export function setExpansionTerrain(data:Heightfield,overlays:WalkMesh[]=[]){
 terrain=data;walkTriangles.clear();
 for(const mesh of overlays)for(const face of mesh.triangles){const tri=face.map(i=>mesh.vertices[i]);
  for(let x=Math.floor(Math.min(...tri.map(v=>v[0]))/4);x<=Math.floor(Math.max(...tri.map(v=>v[0]))/4);x++)
   for(let y=Math.floor(Math.min(...tri.map(v=>v[1]))/4);y<=Math.floor(Math.max(...tri.map(v=>v[1]))/4);y++){const key=x+','+y;const bucket=walkTriangles.get(key)??[];bucket.push(tri);walkTriangles.set(key,bucket);}
 }
}
export function overlayHeight(x:number,y:number){let height=-Infinity;
 for(const [a,b,c] of walkTriangles.get(Math.floor(x/4)+','+Math.floor(y/4))??[]){
  const det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);if(Math.abs(det)<1e-10)continue;
  const u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det,v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det;
  if(u>=-1e-6&&v>=-1e-6&&u+v<=1.000001)height=Math.max(height,a[2]*u+b[2]*v+c[2]*(1-u-v));
 }return height;
}
export function terrainHeight(x:number,y:number):number|undefined {
 if(!terrain)return;const {x0,y0,dx,dy,nx,ny,heights}=terrain,fx=(x-x0)/dx,fy=(y-y0)/dy;
 if(fx<0||fy<0||fx>nx-1||fy>ny-1)return;
 const ix=Math.min(nx-2,Math.floor(fx)),iy=Math.min(ny-2,Math.floor(fy)),u=fx-ix,v=fy-iy;
 const a=heights[iy*nx+ix],b=heights[iy*nx+ix+1],c=heights[(iy+1)*nx+ix],d=heights[(iy+1)*nx+ix+1];
 // Native terrain triangles use the lower-left to upper-right diagonal.
 return u>=v?a+(b-a)*u+(d-b)*v:a+(d-c)*u+(c-a)*v;
}
export const PLACES: {id:PlaceId;title:string;subtitle:string;x:number;y:number;floor:number;description:string}[] = [
 {id:'home',title:'大雄的家',subtitle:'野比家 · 庭院与一楼',x:-9.6,y:-6.3,floor:0,description:'穿过石板小路，推开熟悉的木门。客厅的茶还温着。'},
 {id:'bedroom',title:'大雄的房间',subtitle:'二楼 · 窗边的书桌',x:-11.35,y:3.3,floor:1,description:'绿窗帘、摊开的作业本，还有藏着童年秘密的壁橱。'},
 {id:'lot',title:'那片空地',subtitle:'三根水泥管 · 伙伴的集合点',x:18,y:0,floor:0,description:'胖虎和小夫已经到了。再玩一会儿，太阳还没下山。'},
 {id:'shizuka',title:'静香家',subtitle:'源家 · 花开的街角',x:-9,y:-24.3,floor:0,description:'粉色的门檐下，静香在等放学回家的朋友。'},
 {id:'suneo',title:'小夫家',subtitle:'骨川家 · 红瓦与喷泉',x:-31,y:-24.4,floor:0,description:'宽宽的阳台和修整过的庭院，是街区里很好认的一户。'},
 {id:'gian',title:'胖虎家',subtitle:'刚田商店 · 街角杂货铺',x:-33.4,y:-1.3,floor:0,description:'橙绿相间的遮阳棚下面，整齐摆着今天的蔬果。'},
 {id:'school',title:'小学',subtitle:'操场 · 放学之后',x:15,y:-17,floor:0,description:'走过操场，绕过球门，这就是每天往返的放学路。'},
 {id:'station',title:'月见台站',subtitle:'电车 · 小镇的另一端',x:0,y:32.3,floor:0,description:'绿白电车停在站台旁，远处的电线一直伸向天空。'},
 {id:'river',title:'学校后的河岸',subtitle:'沿河散步 · 芦苇与水声',x:-7,y:-42,floor:0,description:'沿着学校旁的小路走来，河水从桥下缓缓流过。'},
 {id:'bridge',title:'通往后山的桥',subtitle:'过桥 · 去树林里看看',x:1,y:-48,floor:0,description:'走过有石护岸的小河，顺着另一边的小路往山上去。'},
 {id:'hill',title:'后山',subtitle:'林间步道 · 俯瞰小镇',x:10,y:-78,floor:0,description:'穿过树林来到山顶，熟悉的屋顶、学校和河流都在脚下。'},
];
export type Collider={x:number;y:number;z:number;w:number;d:number;h:number;group:string};
export type Actor={id:string;name:string;x:number;y:number;z:number;color:string;lines:string[]};
export const ACTORS:Actor[]=[
 {id:'doraemon',name:'哆啦A梦',x:-10.5,y:-3.8,z:.133,color:'#008ac3',lines:['大雄，今天想去哪里？先回房间看看，还是去空地找大家？','二楼的窗边很舒服哦。走到楼梯前，就能上去。','竹蜻蜓能带你飞过屋顶，任意门能去想去的地方。时光机藏在你书桌的抽屉里哦。']},
 {id:'shizuka',name:'静香',x:-9,y:-24,z:.053,color:'#cc7190',lines:['大雄，你也放学啦。今天的风真舒服。','大家好像都在空地，我们一起去看看吧。']},
 {id:'gian',name:'胖虎',x:17,y:2,z:.213,color:'#db8a40',lines:['喂，大雄！今天要不要一起打棒球？','这三根水泥管，是我们的老地方。']},
 {id:'suneo',name:'小夫',x:13,y:1,z:.213,color:'#73977a',lines:['你看见我家的新阳台了吗？从这条街走过去就到了。','今天我们先在空地玩，晚一点再回家。']},
 {id:'tamako',name:'妈妈',x:-12.05,y:6.05,z:.48,color:'#bc7080',lines:['大雄，回来了呀。别忘了先去把作业写完。','饭快做好了，记得洗手。']},
 {id:'nobisuke',name:'爸爸',x:-16.4,y:2.2,z:.48,color:'#907b59',lines:['今天过得怎么样？过来喝杯茶吧。','这条街没有什么大事，但每天都很热闹。']},
];
// World coordinates are kept in the source model's horizontal X/Y plane.
export function collides(x:number,y:number,z:number,cs:Collider[],radius=.18){
 return cs.some(c=>z<c.z+c.h/2-.05 && z+1.30>c.z-c.h/2+.08 && Math.abs(x-c.x)<c.w/2+radius && Math.abs(y-c.y)<c.d/2+radius);
}
export const HOUSE={lower:.48,upper:3.15,stairX:-12.48,stairY0:3.05,stairY1:6.50};
export type GroundSurface={x0:number;x1:number;y0:number;y1:number;height:number;name:string;baseHeight?:number;edgeFalloff?:number;slopeY0?:number;slopeY1?:number};
export function surfaceHeight(x:number,y:number,s:GroundSurface){
 const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
 if(s.slopeY0!==undefined&&s.slopeY1!==undefined)return s.height+(s.baseHeight!-s.height)*smooth((y-s.slopeY0)/(s.slopeY1-s.slopeY0));
 if(s.edgeFalloff)return s.baseHeight!+(s.height-s.baseHeight!)*smooth(Math.min(x-s.x0,s.x1-x,y-s.y0,s.y1-y)/s.edgeFalloff);
 return s.height;
}
export function houseAt(x:number,y:number):'home'|'shizuka'|null{if(x>-16&&x<-7.9&&y>-22&&y<-14)return 'shizuka';if((x>-17.15&&x<-8.95&&y>.35&&y<8.55)||(x>-17.15&&x<-13.45&&y>-2.35&&y<=.35))return 'home';return null;
}
export function insideHouse(x:number,y:number){return houseAt(x,y)!==null;}
export function groundHeight(x:number,y:number,previous:number,surfaces:GroundSurface[]=[]){
 if(x>HOUSE.stairX-.39&&x<HOUSE.stairX+.39&&y>=HOUSE.stairY0&&y<=HOUSE.stairY1)
  return HOUSE.lower+(y-HOUSE.stairY0)/(HOUSE.stairY1-HOUSE.stairY0)*(HOUSE.upper-HOUSE.lower);
 if(houseAt(x,y)==='shizuka'){if(x>-12.56&&x<-11.70&&y>=-20.5&&y<=-17.3)return .24+(y+20.5)/3.2*2.70;return previous>2.60?2.94:.24;}
 if(houseAt(x,y)==='home'){
  if(previous>2.75&&y<6.85)return HOUSE.upper;
  return HOUSE.lower;
 }
 const land=terrainHeight(x,y);
 return surfaces.length||land!==undefined?Math.max(land??.053,overlayHeight(x,y),...surfaces.filter(s=>x>=s.x0&&x<=s.x1&&y>=s.y0&&y<=s.y1).map(s=>surfaceHeight(x,y,s))):.23;
}
