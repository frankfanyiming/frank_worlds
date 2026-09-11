import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(R/'worlds/frog/blender/panda-tripo/panda-20k-source.glb'))
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(v) for v in o.bound_box]
  print('PANDA_INSPECT',json.dumps({'name':o.name,'matrix':[list(x) for x in o.matrix_world],'faces':len(o.data.polygons),'bbox_min':[min(p[i] for p in pts) for i in range(3)],'bbox_max':[max(p[i] for p in pts) for i in range(3)],'materials':[m.name for m in o.data.materials]},ensure_ascii=False))
for im in bpy.data.images:print('IMAGE',im.name,list(im.size),im.colorspace_settings.name)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=450;s.render.resolution_y=450;s.render.resolution_percentage=100;s.world.color=(.2,.2,.2)
bpy.ops.object.light_add(type='AREA',location=(2,-3,4));l=bpy.context.object;l.data.energy=400;l.data.size=5;l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
for name,pos in [('plusx',(2,0,.25)),('minusy',(0,-2,.25))]:
 bpy.ops.object.camera_add(location=pos);c=bpy.context.object;c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.2;s.camera=c;s.render.filepath=str(R/'docs/evidence/panda-home'/('panda-orientation-'+name+'.png'));bpy.ops.render.render(write_still=True)
