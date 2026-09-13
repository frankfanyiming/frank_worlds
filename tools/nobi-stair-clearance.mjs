// The historical side stringers seal the ground-floor living-room doorway.
// Open the first 55 cm on both sides, retaining all 16 original stair treads.
export function openNobiStairSides(doc, startY=1.75) {
 const changes=[];
 for(const node of doc.getRoot().listNodes().filter(n=>['home_stairs','v9_stairs','v9_stairs_support'].includes(n.getName())))for(const primitive of node.getMesh().listPrimitives()){
  const material=primitive.getMaterial()?.getName()||'',name=node.getName();
  const cedar=name==='home_stairs'&&material==='V10_Cedar';
  const rail=cedar||(name==='home_stairs'&&/^(Oak|Steel)/.test(material))||(name==='v9_stairs'&&material==='B9 nickel hardware')||name==='v9_stairs_support';
  if(!rail)continue;
  const pos=primitive.getAttribute('POSITION').getArray(),ids=primitive.getIndices().getArray(),matrix=node.getWorldMatrix();
  const world=v=>[matrix[0]*v[0]+matrix[4]*v[1]+matrix[8]*v[2]+matrix[12],-(matrix[2]*v[0]+matrix[6]*v[1]+matrix[10]*v[2]+matrix[14]),matrix[1]*v[0]+matrix[5]*v[1]+matrix[9]*v[2]+matrix[13]];
  const parent=Array.from({length:pos.length/3},(_,i)=>i),find=i=>parent[i]===i?i:(parent[i]=find(parent[i])),union=(a,b)=>{parent[find(a)]=find(b);},same=new Map();
  for(let i=0;i<pos.length;i+=3){const key=[pos[i],pos[i+1],pos[i+2]].map(v=>Math.round(v*10000)).join(',');if(same.has(key))union(i/3,same.get(key));else same.set(key,i/3);}
  for(let i=0;i<ids.length;i+=3){union(ids[i],ids[i+1]);union(ids[i],ids[i+2]);}
  const components=new Map();
  for(let i=0;i<pos.length;i+=3){const id=find(i/3),c=components.get(id)||{lo:[Infinity,Infinity,Infinity],hi:[-Infinity,-Infinity,-Infinity],cap:[]};world(pos.subarray(i,i+3)).forEach((v,j)=>{c.lo[j]=Math.min(c.lo[j],v);c.hi[j]=Math.max(c.hi[j],v);});components.set(id,c);}
  const semantics=primitive.listSemantics(),sources=semantics.map(s=>primitive.getAttribute(s)),strides=sources.map(s=>s.getElementSize()),arrays=sources.map(s=>s.getArray()),out=semantics.map(()=>[]),positionIndex=semantics.indexOf('POSITION');
  const vertex=i=>arrays.map((a,k)=>Array.from(a.subarray(i*strides[k],(i+1)*strides[k])));
  const append=v=>v.forEach((a,k)=>out[k].push(...a));let clipped=0;
  for(let i=0;i<ids.length;i+=3){const c=components.get(find(ids[i])),selected=c.lo[1]<startY&&(!cedar||(c.hi[0]-c.lo[0]<.12&&c.hi[2]-c.lo[2]>.4));let triangle=[vertex(ids[i]),vertex(ids[i+1]),vertex(ids[i+2])];
   if(selected){const polygon=[];for(let j=0;j<3;j++){const a=triangle[j],b=triangle[(j+1)%3],da=world(a[positionIndex])[1]-startY,db=world(b[positionIndex])[1]-startY;if(da>=0)polygon.push(a);if((da>=0)!==(db>=0)){const t=da/(da-db),v=a.map((values,k)=>values.map((x,l)=>x+(b[k][l]-x)*t));polygon.push(v);c.cap.push(v);}}triangle=polygon;clipped++;}
   for(let j=1;j+1<triangle.length;j++){append(triangle[0]);append(triangle[j]);append(triangle[j+1]);}
  }
  // Close the newly cut ends of each solid rail/post with matching material.
  for(const c of components.values())if(c.cap.length){const points=[...new Map(c.cap.map(v=>[world(v[positionIndex]).map(x=>Math.round(x*10000)).join(','),v])).values()];if(points.length<3)continue;const center=points[0].map((a,k)=>a.map((_,j)=>points.reduce((s,v)=>s+v[k][j],0)/points.length)),wc=world(center[positionIndex]);points.sort((a,b)=>{const wa=world(a[positionIndex]),wb=world(b[positionIndex]);return Math.atan2(wa[2]-wc[2],wa[0]-wc[0])-Math.atan2(wb[2]-wc[2],wb[0]-wc[0]);});const ni=semantics.indexOf('NORMAL');const cap=v=>{const copy=v.map(a=>[...a]);if(ni>=0)copy[ni]=[matrix[2],matrix[6],matrix[10]];return copy;};for(let j=0;j<points.length;j++){append(cap(center));append(cap(points[j]));append(cap(points[(j+1)%points.length]));}}
  if(!clipped)continue;
  semantics.forEach((s,k)=>primitive.setAttribute(s,sources[k].clone().setArray(new Float32Array(out[k]))));primitive.setIndices(doc.createAccessor().setType('SCALAR').setBuffer(doc.getRoot().listBuffers()[0]).setArray(Uint32Array.from({length:out[positionIndex].length/3},(_,i)=>i)));
  changes.push({node:name,material,startY,trianglesBefore:ids.length/3,trianglesAfter:out[positionIndex].length/9});
 }
 return changes;
}
