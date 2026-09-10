"""One-off migration of the existing v10 glTF files into v11 assets."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/models'
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def export(path):
 bpy.ops.object.select_all(action='SELECT')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_image_format='AUTO',export_image_quality=82,export_draco_mesh_compression_enable=True,export_draco_position_quantization=16,export_animations=True)
def remove(o):bpy.data.objects.remove(o,do_unlink=True)
footprints=[(-39,-29.2,.0,9.1),(-39.5,-25.4,-23.65,-12.3),(-17.3,-7.7,-22.4,-13.9)]
def inside(x,y):return any(x0<x<x1 and y0<y<y1 for x0,x1,y0,y1 in footprints)
for name in ['world-v3','surface-v7','details/house-v10']:
 clear();bpy.ops.import_scene.gltf(filepath=str(OUT/(name+'.glb')))
 for o in list(bpy.context.scene.objects):
  if o.type!='MESH':continue
  if name=='world-v3' and o.name.startswith(('home_','facade_')):remove(o);continue
  if name=='details/house-v10' and o.name!='v9_garden':remove(o);continue
  if name in ['world-v3','surface-v7'] and o.name in ['town','roof_town','neighborhood_detail','surface_detail']:
   bm=bmesh.new();bm.from_mesh(o.data);faces=[]
   for f in bm.faces:
    c=o.matrix_world@f.calc_center_median()
    if c.z>.22 and inside(c.x,c.y):faces.append(f)
   bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(o.data);bm.free()
  if o.name in ['v9_garden','roof_town','terrain_blades']:
   bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('web polygon budget','DECIMATE');mod.ratio=.30;bpy.ops.object.modifier_apply(modifier=mod.name)
 export(OUT/(name.replace('-v3','-v11').replace('-v7','-v11').replace('-v10','-v11')+'.glb'))
 print('REFINED',name,flush=True)
for name in ['vehicles/kei_hatchback','vehicles/kei_truck']:
 clear();bpy.ops.import_scene.gltf(filepath=str(OUT/(name+'.glb')))
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and len(o.data.polygons)>3000:
   bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('web polygon budget','DECIMATE');mod.ratio=.12;bpy.ops.object.modifier_apply(modifier=mod.name)
 export(OUT/(name+'-v11.glb'));print('VEHICLE_READY',name,flush=True)
# Correct the texture of Doraemon on the back-facing geometry, retaining UVs/rig.
clear();bpy.ops.import_scene.gltf(filepath=str(OUT/'actors/doraemon.glb'))
o=bpy.data.objects.get('doraemon_skin');me=o.data
# Front is Blender -Y (glTF +Z); white is allowed on front face and belly, not rear hemisphere.
blue=bpy.data.materials.new('Doraemon_blue_back');blue.diffuse_color=(.015,.38,.64,1);blue.use_nodes=True
p=next(n for n in blue.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.015,.38,.64,1);p.inputs['Roughness'].default_value=.48;me.materials.append(blue);idx=len(me.materials)-1
count=0
for f in me.polygons:
 c=o.matrix_world@f.center
 if c.y>.015 and .23<c.z<1.30:
  f.material_index=idx;count+=1
# Preserve a red tail protruding from the blue back as an independent simple mesh.
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.059,location=(0,.33,.42));tail=bpy.context.object;tail.name='Doraemon_red_tail';m=bpy.data.materials.new('Doraemon_tail_red');m.diffuse_color=(.75,.035,.015,1);m.use_nodes=True;next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(.75,.035,.015,1);tail.data.materials.append(m);tail.parent=bpy.data.objects.get('actor_doraemon')
# Remove unused Wave animation data from exported character action set.
for a in list(bpy.data.actions):
 if 'Wave' in a.name:bpy.data.actions.remove(a)
export(OUT/'actors/doraemon-v11.glb');print('DORAEMON_BLUE_BACK_FACES',count,flush=True)
