"""Render and measure the actual character assets, never concept images."""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
source=Path(args[0]) if args else ROOT/'worlds/conan/blender/character-v2/originals/conan.glb'
out=Path(args[1]) if len(args)>1 else ROOT/'docs/evidence/conan-character/before-conan'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
if source.suffix=='.blend':bpy.ops.wm.open_mainfile(filepath=str(source))
elif source.suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(source))
else:bpy.ops.import_scene.gltf(filepath=str(source))
s=bpy.context.scene
rigs=[o for o in s.objects if o.type=='ARMATURE']
meshes=[o for o in s.objects if o.type=='MESH' and (not rigs or len(o.vertex_groups)>0)]
if source.suffix=='.fbx':
 for o in meshes:o.matrix_world=Matrix.Rotation(-math.pi/2,4,'Z')@o.matrix_world
dg=bpy.context.evaluated_depsgraph_get()
points=[o.evaluated_get(dg).matrix_world@v.co for o in meshes for v in o.evaluated_get(dg).data.vertices]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)));height=hi.z-lo.z
center=(lo+hi)*.5
data={'source':str(source),'bounds':[list(lo),list(hi)],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'materials':[m.name for m in o.data.materials if m]} for o in meshes],'bones':{r.name:[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local)} for b in r.data.bones] for r in rigs},'actions':[a.name for a in bpy.data.actions]}
(out/'inspection.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
for rig in rigs:
 if rig.animation_data:
  for track in rig.animation_data.nla_tracks:track.mute=True
  if bpy.data.actions.get('Idle'):rig.animation_data.action=bpy.data.actions['Idle']
s.frame_set(1)
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=900;s.render.resolution_y=1050;s.render.resolution_percentage=80
s.world=bpy.data.worlds.new('Neutral world');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.27,.30,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
s.view_settings.view_transform='AgX'
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,lo.z-.005));floor=bpy.context.object
mat=bpy.data.materials.new('Render ground');mat.diffuse_color=(.32,.35,.36,1);floor.data.materials.append(mat)
for xyz,power,size in [((2,-3,4),450,4),((-3,-1,2),160,3),((0,3,3),220,3)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(xyz)*height)
 light=bpy.context.object;light.data.energy=power*height*height;light.data.size=size*height;light.rotation_euler=(Vector((0,0,height*.5))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=height*1.30
angles=['front','side','back','quarter'] if '--all' in args else ['front','side','quarter']
for view in angles:
 for action,frame in ([('Idle',1),('Walk',8),('Run',6),('Read',18),('Talk',14)] if '--arm-focus' in args else [('Idle',1),('Walk',8)]) if rigs else [('Rest',1)]:
  if action=='Walk' and view=='front':continue
  if action=='Walk' and not bpy.data.actions.get('Walk'):continue
  for rig in rigs:
   if bpy.data.actions.get(action):rig.animation_data.action=bpy.data.actions[action]
  s.frame_set(frame)
  xyz={'front':(0,-4,.6),'side':(4,0,.6),'back':(0,4,.6),'quarter':(2.8,-4,.8)}[view]
  camera.location=Vector(xyz)*height+Vector((center.x,center.y,lo.z));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(out/f'{source.stem}-{action.lower()}-{view}.png');bpy.ops.render.render(write_still=True)
if '--contacts' in args:
 for action in ['Walk','Run','Talk','Wave']:
  if not bpy.data.actions.get(action):continue
  duration=bpy.data.actions[action].frame_range[1]-bpy.data.actions[action].frame_range[0]
  for t in ([0,.25,.5,.75] if action in ['Walk','Run'] else [.2]):
   for rig in rigs:rig.animation_data.action=bpy.data.actions[action]
   frame=t*duration;s.frame_set(int(frame),subframe=frame-int(frame))
   camera.location=Vector((2.8,-4,.8))*height+Vector((center.x,center.y,lo.z));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
   s.render.filepath=str(out/f'{source.stem}-{action.lower()}-{t:.2f}-contact.png');bpy.ops.render.render(write_still=True)
