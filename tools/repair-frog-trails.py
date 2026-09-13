"""Correct downward trail faces while preserving every unrelated GLB buffer.

Run with Blender's Python (numpy). No change to terrain/collision/house assets.
"""
import sys, importlib.util, json, shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('glb',ROOT/'tools/conan/patch-street-context.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
path=ROOT/'worlds/frog/source/assets/woodland.glb'
backup=ROOT/'worlds/frog/blender/woodland-before-trail22.glb'
if not backup.exists():shutil.copy2(path,backup)
g=lib.GLB(backup);report=[]
for node in g.d['nodes']:
 if node.get('name') not in ['Landscape_Soft_sand_footpath','PandaTrail']:continue
 for prim in g.d['meshes'][node['mesh']]['primitives']:
  pos=g.acc(prim['attributes']['POSITION']);ix=g.acc(prim['indices']).reshape(-1,3)
  normals=np.cross(pos[ix[:,1]]-pos[ix[:,0]],pos[ix[:,2]]-pos[ix[:,0]])
  down=normals[:,1]<0;ix[down]=ix[down][:,[0,2,1]]
  normals=np.cross(pos[ix[:,1]]-pos[ix[:,0]],pos[ix[:,2]]-pos[ix[:,0]])
  # Weld only the normal calculation, preserving UV seams and the existing indices.
  keys=[tuple(np.round(v,5)) for v in pos];acc={k:np.zeros(3) for k in keys}
  for tri,n in zip(ix,normals):
   for i in tri:acc[keys[i]]+=n
  ns=np.array([acc[k] for k in keys]);ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-9)
  prim['indices']=g.add(ix.reshape(-1,1),'SCALAR',5125)
  old=g.acc(prim['attributes']['NORMAL']);prim['attributes']['NORMAL']=g.add(ns,'VEC3')
  if 'TANGENT' in prim['attributes']:
   ts=g.acc(prim['attributes']['TANGENT']);ts[:,3]*=np.where((old*ns).sum(1)<0,-1,1)
   ts[:,:3]-=ns*(ts[:,:3]*ns).sum(1)[:,None];ts[:,:3]/=np.maximum(np.linalg.norm(ts[:,:3],axis=1,keepdims=True),1e-9)
   prim['attributes']['TANGENT']=g.add(ts,'VEC4')
  report.append({'node':node['name'],'faces':len(ix),'reversed_faces':int(down.sum()),'upward_normals':bool((ns[:,1]>0).all())})
g.save(path)
(backup.parent/'trail-repair22.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
