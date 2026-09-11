"""Render real rigged Tripo meshes and their evaluated walk/jump contacts."""
from pathlib import Path
import bpy,math,json,sys
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];B=R/'worlds/frog/blender';E=R/'docs/evidence/character-motion';FPS=30
only=sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else ''
video='--video' in sys.argv
quick='--quick' in sys.argv
for species,file,forward in [('frog','frog-rig-jump.blend',1),('panda','panda-rig.blend',-1)]:
 if only and only!=species:continue
 if '--air-check' in sys.argv and species!='frog':continue
 bpy.ops.wm.open_mainfile(filepath=str(B/file));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
 for track in rig.animation_data.nla_tracks:track.mute=True
 s.render.engine='CYCLES';s.cycles.samples=12 if video else 20;s.cycles.use_denoising=True;s.render.resolution_x=1000 if not video else 960;s.render.resolution_y=800 if not video else 720;s.render.resolution_percentage=70 if quick else 100;s.render.fps=FPS
 s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.20,.19,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;s.view_settings.view_transform='AgX';s.view_settings.exposure=.2
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));floor=bpy.context.object;floor.name='Render-only checker ground';mat=bpy.data.materials.new('Foot contact grid');mat.use_nodes=True;nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tex=nt.nodes.new('ShaderNodeTexChecker');tex.inputs['Color1'].default_value=(.16,.20,.19,1);tex.inputs['Color2'].default_value=(.23,.28,.26,1);tex.inputs['Scale'].default_value=2.5;coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector']);nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.87;floor.data.materials.append(mat)
 lights=[]
 for pos,power,size in [((2,forward*3,4),450,4),((-3,forward*1,2.5),180,3),((0,-forward*3,3),240,3)]:
  bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
 bpy.ops.object.camera_add(location=(2.5,forward*3,.95));camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=2.1;s.camera=camera
 def view(label='quarter',follow=Vector()):
  positions={'front':Vector((0,forward*4,.78)),'side':Vector((4,0,.82)),'quarter':Vector((2.4,forward*3,1.1))}
  camera.location=positions[label]+follow;camera.rotation_euler=(Vector((0,0,.62))+follow-camera.location).to_track_quat('-Z','Y').to_euler()
 def pose(name,frame):
  rig.animation_data.action=bpy.data.actions[name];s.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 if '--air-check' in sys.argv:
  for seconds in [0.0,.2,.4]:
   for label in ['side','front']:
    pose('JumpAir',1+seconds*FPS);view(label);s.render.filepath=str(E/f'frog-jumpair-revised-{seconds:.1f}s-{label}.png');bpy.ops.render.render(write_still=True)
  continue
 if not video:
  for name,frame,label in [('Idle',1,'front'),('Idle',1,'quarter'),('Sit',1,'quarter'),('Walk',1,'quarter'),('Walk',6 if species=='frog' else 8,'quarter'),('Walk',16 if species=='frog' else 20,'side')]:
   if quick and name=='Idle':continue
   pose(name,frame);view(label);s.render.filepath=str(E/f'{species}-after-{name.lower()}-{frame}-{label}.png');bpy.ops.render.render(write_still=True)
  if species=='frog' and not quick:
   for name,frame in [('JumpStart',5),('JumpAir',8),('Land',5)]:
    pose(name,frame);view();s.render.filepath=str(E/f'{species}-after-{name.lower()}-{frame}.png');bpy.ops.render.render(write_still=True)
 else:
  folder=E/(species+'-walk-frames');folder.mkdir(exist_ok=True);cycles=3;duration=20 if species=='frog' else 24;speed=1.18 if species=='frog' else .68
  for i in range(duration*cycles):
   pose('Walk',i%duration+1);follow=Vector((0,forward*speed*i/FPS,0));rig.location=follow;view('quarter' if i<duration*2 else 'side',follow)
   # Lighting follows the character; the world grid stays fixed and proves foot lock.
   if i:
    for light in lights:light.location.y+=forward*speed/FPS
   s.render.filepath=str(folder/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
  if species=='frog':
   folder=E/'frog-jump-frames';folder.mkdir(exist_ok=True);rig.location=Vector();
   for i in range(48):
    seconds=i/FPS
    if seconds<.12:pose('JumpStart',1+seconds*FPS);z=0
    elif seconds<.84:
     elapsed=seconds-.12;z=max(0,6.4*elapsed-9*elapsed*elapsed)
     if seconds<.25:pose('JumpStart',1+seconds*FPS)
     else:pose('JumpAir',1+((seconds-.25)*FPS)%30)
    elif seconds<1.173:pose('Land',1+(seconds-.84)*FPS);z=0
    else:pose('Idle',1);z=0
    rig.location=Vector((0,0,z));view('side',Vector((0,0,z*.40)));camera.data.ortho_scale=2.7;s.render.filepath=str(folder/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
