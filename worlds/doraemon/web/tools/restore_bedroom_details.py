"""Import the accepted detailed room without geometry or texture reduction.
Run with Blender: --python tools/restore_bedroom_details.py -- /path/to/room.glb
The resulting portable GLB is committed; source scenes are never modified.
"""
import bpy,sys
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[sys.argv.index('--')+1])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];groups={}
for name in ['hero_floor','hero_props','hero_closet','hero_shell','hero_front','hero_ceiling']:
 o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);groups[name]=o
shift=Matrix.Translation(Vector((-10.775,3.3,3.15)))
for o in objects:
 name=o.name;o.data.transform(shift@o.matrix_world);o.parent=None;o.matrix_world=Matrix.Identity(4)
 if name=='Interaction_Drawer':bpy.data.objects.remove(o,do_unlink=True);continue
 if name=='Closet_Sliding_Door':o.name='v12_closet_slide';continue
 group='hero_props'
 if name=='Floor':group='hero_floor'
 elif name=='Ceiling':group='hero_ceiling'
 elif name.startswith(('Closet_','Alcove')):group='hero_closet'
 elif name.startswith(('Wall_','Window_','Glass_','Curtain_')):group='hero_front' if 'Front' in name or 'Curtain_' in name else 'hero_shell'
 o.parent=groups[group]
for o in list(bpy.context.scene.objects):
 if o.type=='EMPTY' and o.name not in groups:bpy.data.objects.remove(o,do_unlink=True)
wood=bpy.data.materials['V10_Cedar'];paper=bpy.data.materials['WashiUV'];pieces=[]
def box(name,pos,dims,mat,moving=True):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if moving:pieces.append(o)
 return o
box('fusuma paper',(-12.585,5.35,4.13),(.055,.78,1.92),paper)
for y in [4.947,5.753]:box('fusuma upright',(-12.585,y,4.13),(.065,.034,1.97),wood)
for z in [3.16,5.10]:box('fusuma crossbar',(-12.585,5.35,z),(.065,.84,.035),wood)
box('recessed pull',(-12.550,5.64,4.12),(.01,.044,.14),wood)
for z in [3.15,5.12]:box('v12_entry_rail_'+str(z),(-12.585,5.79,z),(.12,1.75,.025),wood,False)
bpy.ops.object.select_all(action='DESELECT')
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();o=bpy.context.object;o.name='v12_nobita_slide'
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/bedroom-v12.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_image_format='AUTO',export_draco_mesh_compression_enable=True,export_draco_position_quantization=16,export_draco_texcoord_quantization=16)
print('DETAILED_BEDROOM_RESTORED',flush=True)
