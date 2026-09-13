"""Release22: repair authored doorway sill and remove obsolete riverside fences.

Preserve unrelated geometry, embedded maps, characters and the real tower hole.
The companion site-access.glb supplies the garage apron and retaining structure.
"""
import importlib.util,json,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('glb',Path(__file__).with_name('patch-street-context.py'))
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
BACK=ROOT/'worlds/conan/blender/reference-2026-09/originals/access22';BACK.mkdir(parents=True,exist_ok=True)
reports=[]
for variant in ['source','web-project']:
 base=ROOT/f'worlds/conan/{variant}/assets'
 for name in ['buildings/mouri.glb','street.glb']:
  p=base/name;b=BACK/(variant+'-'+Path(name).name)
  if not b.exists():shutil.copy2(p,b)
  g=lib.GLB(b);count=0
  for n in g.d['nodes']:
   if 'mesh' not in n:continue
   if name.startswith('buildings/') and n.get('name')!='Whole_building_shell':continue
   if name=='street.glb' and n.get('name') not in ['Bridge','Bridge_Collision']:continue
   for prim in g.d['meshes'][n['mesh']]['primitives']:
    pos=g.acc(prim['attributes']['POSITION']);ix=g.acc(prim['indices']).reshape(-1,3)
    if name.startswith('buildings/'):
     region=(pos[:,0]>=1.249)&(pos[:,0]<=4.401)&(abs(pos[:,2])<=.081)&(pos[:,1]>.001)&(pos[:,1]<=.421)
     pos[region,1]*=.16/.42;count+=int(region.sum())
     if region.any():prim['attributes']['POSITION']=g.add(pos,'VEC3')
    else:
     # Clip old quay/bridge fence geometry against the rebuilt garage plot,
     # including long triangles that cross its boundary. No centroid deletion.
     poly=[(73.1,-18.3),(79.3,-18.3),(79.3,-6.8),(73.1,-6.8)]
     tris=pos[ix];candidate=(tris[:,:,0].max(1)>73.1)&(tris[:,:,0].min(1)<79.3)&(tris[:,:,2].max(1)>-18.3)&(tris[:,:,2].min(1)<-6.8)
     if not candidate.any():continue
     keys=['POSITION']+[k for k in prim['attributes'] if k!='POSITION'];attrs={k:g.acc(prim['attributes'][k]) for k in keys};slices={};cursor=0
     for k in keys:slices[k]=slice(cursor,cursor+attrs[k].shape[1]);cursor+=attrs[k].shape[1]
     packed=np.concatenate([attrs[k] for k in keys],1);extra=[]
     for i in np.where(candidate)[0]:
      pending=list(packed[ix[i]]);outside=[]
      for a,b in zip(poly,poly[1:]+poly[:1]):
       if len(pending)<3:break
       pending,part=lib.split(pending,a,b)
       if len(part)>=3:outside.append(part)
      for part in outside:
       for j in range(1,len(part)-1):extra.extend([part[0],part[j],part[j+1]])
     extra=np.array(extra).reshape(-1,cursor)
     for k in keys:
      arr=np.concatenate([attrs[k],extra[:,slices[k]]]);acc=g.d['accessors'][prim['attributes'][k]]
      if k=='NORMAL':arr/=np.maximum(np.linalg.norm(arr,axis=1,keepdims=True),1e-9)
      prim['attributes'][k]=g.add(arr,acc['type'],acc['componentType'])
     idx=np.concatenate([ix[~candidate],np.arange(len(pos),len(pos)+len(extra)).reshape(-1,3)])
     prim['indices']=g.add(idx.reshape(-1,1),'SCALAR',5125);count+=int(candidate.sum())
  g.save(p);reports.append({'variant':variant,'asset':name,'repaired_vertices_or_triangles':count})
 p=base/'buildings/mouri.json';d=json.loads(p.read_text())
 for c in d['colliders']:
  if abs(c['p'][0]-2.825)<.001 and abs(c['p'][1]-.21)<.001 and abs(c['p'][2])<.001:
   c['p'][1]=.08;c['s'][1]=.16
 d.setdefault('notes',{})['entrance_sill22']='Continuous 0.16m threshold, 25mm above the real pavement; former 0.42m wall across the doorway removed.'
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(json.dumps(reports))
(BACK.parent.parent/'access-repair22.json').write_text(json.dumps(reports,indent=2))
