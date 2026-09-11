import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
reports=[]
for species,filename in [('frog','frog-rig-jump.blend'),('panda','panda-rig.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'worlds/frog/blender/character-motion-originals'/filename))
 mesh=next(o for o in bpy.data.objects if o.type=='MESH');rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 vertices=[v.co.copy() for v in mesh.data.vertices]
 stats={'species':species,'matrix':[list(r) for r in mesh.matrix_world],'bbox':[[min(v[i] for v in vertices) for i in range(3)],[max(v[i] for v in vertices) for i in range(3)]],'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones},'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions]}
 bins=[]
 for z0,z1 in [(0,.08),(.08,.16),(.16,.27),(.27,.4),(.4,.6),(.6,.8),(.8,1.4)]:
  vs=[v for v in vertices if z0<=v.z<z1]
  if vs:bins.append({'z':[z0,z1],'n':len(vs),'x':[min(v.x for v in vs),max(v.x for v in vs)],'y':[min(v.y for v in vs),max(v.y for v in vs)]})
 stats['bins']=bins
 reports.append(stats)
(R/'docs/evidence/character-motion/original-inspection.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
