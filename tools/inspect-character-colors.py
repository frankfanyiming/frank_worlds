import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for species,file in [('frog','frog-rig-jump.blend'),('panda','panda-rig.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'worlds/frog/blender/character-motion-originals'/file));mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');mat=mesh.data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');print('LINKS',species,[(l.from_node.name,l.from_node.type) for l in bs.inputs['Base Color'].links])
 node=bs.inputs['Base Color'].links[0].from_node;im=node.image;w,h=im.size;pixels=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4);colors={}
 for l in mesh.data.loops:
  if l.vertex_index in colors:continue
  uv=mesh.data.uv_layers.active.data[l.index].uv;colors[l.vertex_index]=pixels[int(uv.y*h)%h,int(uv.x*w)%w,:3]
 rows=[]
 for name,fn in [('sole',lambda p:p.z<.07),('lowleg',lambda p:.10<p.z<.18 and abs(p.x)>.16),('belly',lambda p:.22<p.z<.36 and abs(p.x)<.18),('outerlow',lambda p:.22<p.z<.36 and abs(p.x)>.30),('head',lambda p:.8<p.z<1.0)]:
  a=np.array([colors[v.index] for v in mesh.data.vertices if fn(v.co)])
  rows.append({'name':name,'n':len(a),'q10':np.quantile(a,.1,axis=0).tolist(),'median':np.median(a,axis=0).tolist(),'q90':np.quantile(a,.9,axis=0).tolist()})
 print('COLORS',species,json.dumps(rows))
