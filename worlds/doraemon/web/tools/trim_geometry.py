import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'public/models'
for name,ratio in [('surface-v11',.16),('streets-v7',.45),('vegetation-v3',.5),('details/connector-v9',.30),('expansion/expansion-groundcover',.35)]:
 if (p/(name+'-lite.glb')).exists():continue
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 optimized={}
 bpy.ops.import_scene.gltf(filepath=str(p/(name+'.glb')))
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and len(o.data.polygons)>3000:
   original=o.data.name
   if original in optimized:o.data=optimized[original];continue
   o.data=o.data.copy();bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('web visible-detail budget','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name);optimized[original]=o.data
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(p/(name+'-lite.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_position_quantization=16)
 print('OPTIMIZED',name,flush=True)
