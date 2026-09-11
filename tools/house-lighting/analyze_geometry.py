from pathlib import Path
import numpy as np,json,hashlib
from itertools import permutations
p=Path(__file__).parent/'geometry-dumps';report=[]
perms=np.array(list(permutations(range(3))))
for f in sorted(p.glob('baseline*.bin')):
 q=p/f.name.replace('baseline','runtime',1)
 if not q.exists():continue
 a=np.fromfile(f,dtype=np.float32).reshape(-1,3,3);b=np.fromfile(q,dtype=np.float32).reshape(-1,3,3)
 area=lambda x:np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)
 aa=area(a);bb=area(b);av=a[aa>1e-8];bv=b[bb>1e-8]
 row={'node':f.stem.removeprefix('baseline__'),'source_triangles':len(a),'runtime_triangles':len(b),'source_zero_area_triangles':int((aa<=1e-8).sum()),'runtime_zero_area_triangles':int((bb<=1e-8).sum())}
 for label,x,y in [('source_to_runtime',av,bv),('runtime_to_source',bv,av)]:
  def canonical(t):
   t=np.rint(t*100000).astype(np.int64);order=np.lexsort((t[:,:,2],t[:,:,1],t[:,:,0]),axis=1);t=np.take_along_axis(t,order[:,:,None],1)
   return np.ascontiguousarray(t).reshape(-1,9).view(np.dtype((np.void,72))).ravel()
  xc=canonical(x);yc=canonical(y);missing=np.where(~np.isin(xc,yc))[0];dist=np.zeros(len(x))
  grid={}
  for i,c in enumerate(np.floor(y.mean(1)/.001).astype(int)):
   grid.setdefault(tuple(c),[]).append(i)
  from itertools import product
  offsets=list(product([-1,0,1],repeat=3))
  for i in missing:
   c=np.floor(x[i].mean(0)/.001).astype(int);candidates=[]
   for o in offsets:candidates.extend(grid.get(tuple(c+o),[]))
   if not candidates:dist[i]=999.;continue
   selected=y[candidates]
   dist[i]=np.linalg.norm(x[i][None,None,:,:]-selected[:,perms,:],axis=-1).max(-1).min()
  row[label+'_max_triangle_vertex_distance']=float(dist.max())
  row[label+'_mismatches_above_0_001m']=int((dist>.001).sum())
  ar=area(x)[dist>.001]*.5
  row[label+'_unmatched_area_sum_m2']=float(ar.sum())
  row[label+'_unmatched_area_max_m2']=float(ar.max()) if len(ar) else 0
  row[label+'_unmatched_areas']=ar.tolist()
 row['same_visible_surface_within_1mm']=row['source_to_runtime_mismatches_above_0_001m']==row['runtime_to_source_mismatches_above_0_001m']==0
 report.append(row)
 print(row['node'],row['same_visible_surface_within_1mm'],row['source_to_runtime_max_triangle_vertex_distance'],row['runtime_to_source_max_triangle_vertex_distance'])
(Path(__file__).parent/'geometry-surface-proof.json').write_text(json.dumps({'passed':all(r['same_visible_surface_within_1mm'] for r in report),'method':'Every nonzero-area triangle matched by three vertex coordinates, ignoring winding and duplicate/zero-area triangles. 1 mm tolerance; source original Godot imported GLB cache before UV2 vs runtime SCN.','meshes':report},indent=2))
