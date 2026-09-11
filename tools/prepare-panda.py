"""Prepare the actual Tripo panda for Godot.

The animal is Tripo geometry with its original PBR maps. Blender only normalizes,
This initial ingestion path produced the immutable baseline. Normal invocation
now uses build-character-motion.py so it cannot overwrite the updated Walk/Sit
rig with the old Idle/Greet-only version. --baseline-only is for source recovery.
"""
from pathlib import Path
import bpy, math, json, hashlib
import sys,runpy
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[1];A=R/'worlds/frog/source/assets';B=R/'worlds/frog/blender';E=R/'docs/evidence/panda-home'
SOURCE=B/'panda-tripo/panda-20k-source.glb';HEIGHT=1.35
if '--baseline-only' not in sys.argv:
 if not (B/'character-motion-originals/panda-rig.blend').exists():
  raise RuntimeError('Restore the immutable panda-rig.blend baseline from the source bundle. See docs/character-motion-workflow.md before initial source recovery.')
 sys.argv=[str(R/'tools/build-character-motion.py'),'--','--only','panda']
 runpy.run_path(str(R/'tools/build-character-motion.py'),run_name='__main__')
 raise SystemExit(0)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
mesh=meshes[0];transform=Matrix.Rotation(-math.pi/2,4,'Z')@mesh.matrix_world
for v in mesh.data.vertices:v.co=transform@v.co
mesh.matrix_world=Matrix.Identity(4)
lo=min(v.co.z for v in mesh.data.vertices);hi=max(v.co.z for v in mesh.data.vertices);factor=HEIGHT/(hi-lo)
for v in mesh.data.vertices:v.co=Vector((v.co.x*factor,v.co.y*factor,(v.co.z-lo)*factor))
mesh.name='Tripo_Panda_Skin';mesh.data.name='Tripo panda optimized 22777 faces';mesh['source']='Tripo v3.1';mesh['task_id']='e1d93848-311b-45c4-b298-1cee5a0628d3'
for p in mesh.data.polygons:p.use_smooth=True
for o in list(bpy.context.scene.objects):
 if o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
# Normal map is retained, but the roughness stays matte as in approved concept.
for m in mesh.data.materials:
 for n in m.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':n.inputs['Metallic'].default_value=0

arm=bpy.data.armatures.new('Panda skeleton');rig=bpy.data.objects.new('PandaRig',arm);bpy.context.collection.objects.link(rig);rig.show_in_front=True
bpy.context.view_layer.objects.active=rig;rig.select_set(True);mesh.select_set(False);bpy.ops.object.mode_set(mode='EDIT');bones={}
def bone(n,a,b,parent=None):
 e=arm.edit_bones.new(n);e.head=a;e.tail=b
 if parent:e.parent=arm.edit_bones[parent]
 e.align_roll(Vector((0,-1,0)));bones[n]=(Vector(a),Vector(b))
bone('root',(0,0,0),(0,0,.1));bone('hips',(0,.015,.24),(0,0,.46),'root');bone('spine',(0,0,.46),(0,.005,.72),'hips');bone('head',(0,.005,.72),(0,0,1.26),'spine')
for side,s in [('L',1),('R',-1)]:
 bone('upper_arm.'+side,(s*.32,0,.69),(s*.42,-.035,.48),'spine');bone('forearm.'+side,(s*.42,-.035,.48),(s*.43,-.055,.37),'upper_arm.'+side);bone('hand.'+side,(s*.43,-.055,.37),(s*.43,-.08,.33),'forearm.'+side)
 bone('thigh.'+side,(s*.18,.015,.26),(s*.20,.005,.14),'hips');bone('shin.'+side,(s*.20,.005,.14),(s*.20,-.025,.06),'thigh.'+side);bone('foot.'+side,(s*.20,-.025,.06),(s*.20,-.13,.04),'shin.'+side)
bpy.ops.object.mode_set(mode='OBJECT');mesh.parent=rig;mod=mesh.modifiers.new('Panda four-weight skeletal skin','ARMATURE');mod.object=rig
groups={n:mesh.vertex_groups.new(name=n) for n in bones}
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def distance(p,a,b):
 d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return(p-a-t*d).length
for v in mesh.data.vertices:
 x,y,z=v.co;side='L' if x>=0 else 'R';ax=abs(x);head=smooth(.69,.77,z)
 torso=smooth(.32,.58,z);w={'hips':1-torso,'spine':torso}
 # Short feet stay independently weighted; the body's low belly keeps hip weights.
 if z<.27:
  legs=(1-smooth(.20,.28,z))*smooth(.085,.14,ax);foot=1-smooth(.075,.125,z);shin=1-smooth(.135,.20,z)
  w={n:a*(1-legs) for n,a in w.items()};w['foot.'+side]=legs*foot;w['shin.'+side]=legs*(1-foot)*shin;w['thigh.'+side]=legs*(1-foot)*(1-shin)
 # Only outer limbs enter the arm rig; crossbody satchel remains with the torso.
 ar=smooth(.315,.365,ax)*smooth(.28,.36,z)*(1-smooth(.66,.735,z))
 if ar>.001:
  ns=['upper_arm.'+side,'forearm.'+side,'hand.'+side];ds=[1/max(.025,distance(v.co,*bones[n]))**4 for n in ns];su=sum(ds);w={n:a*(1-ar) for n,a in w.items()}
  for n,d in zip(ns,ds):w[n]=ar*d/su
 w={n:a*(1-head) for n,a in w.items()};w['head']=head;weights=sorted([(n,a) for n,a in w.items() if a>.00001],key=lambda x:-x[1])[:4];total=sum(a for _,a in weights)
 for n,a in weights:groups[n].add([v.index],a/total,'REPLACE')

rest={n:b.matrix_local.to_quaternion() for n,b in arm.bones.items()}
def rotate(n,x=0,y=0,z=0):
 q=rest[n];r=Quaternion((0,0,1),z)@Quaternion((0,1,0),y)@Quaternion((1,0,0),x);rig.pose.bones[n].rotation_quaternion=q.inverted()@r@q
rig.animation_data_create()
for name,frames in [('Idle',120),('Greet',72)]:
 action=bpy.data.actions.new(name);rig.animation_data.action=action
 for frame in range(1,frames+2):
  t=(frame-1)/frames;phase=t*math.tau
  for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0)
  rotate('spine',x=.009*math.sin(phase));rotate('head',x=.009*math.sin(phase+.7),z=.018*math.sin(phase));rotate('upper_arm.L',x=.012*math.sin(phase));rotate('upper_arm.R',x=-.012*math.sin(phase))
  if name=='Greet':
   amplitude=math.sin(math.pi*t)**2;rotate('head',x=.06*amplitude,z=.045*math.sin(phase));rotate('upper_arm.L',x=-.12*amplitude,y=-.18*amplitude);rotate('forearm.L',x=-.28*amplitude,z=.08*math.sin(phase*2)*amplitude)
  for p in rig.pose.bones:p.keyframe_insert('rotation_quaternion',frame=frame,group=p.name)
 action.use_fake_user=True;track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,1,action);track.mute=True
rig.animation_data.action=None
for p in rig.pose.bones:p.rotation_quaternion=Quaternion();p.location=(0,0,0)
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]>0:
  try:im.pack()
  except RuntimeError:pass
bpy.context.scene.render.fps=30
bpy.ops.wm.save_as_mainfile(filepath=str(B/'panda-rig.blend'))
bpy.ops.export_scene.gltf(filepath=str(A/'panda.glb'),export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_cameras=False,export_lights=False,export_action_filter=False)
report={'source':'Tripo','model':'Tripo v3.1','task_id':'e1d93848-311b-45c4-b298-1cee5a0628d3','optimized_task_id':'69379bfb-896b-4a6f-baeb-0eeecedfbee9','conversion_task_id':'2bc04164-f03d-4e19-a2a6-9557c057d114','source_asset':'worlds/frog/blender/panda-tripo/panda-20k-source.glb','source_asset_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'runtime_asset':'worlds/frog/source/assets/panda.glb','runtime_faces':len(mesh.data.polygons),'runtime_vertices':len(mesh.data.vertices),'height':HEIGHT,'forward':'Godot +Z; source Tripo +X rotated -90 degrees in Blender Z','runtime_bytes':(A/'panda.glb').stat().st_size,'rigging':'Manual Blender 16 bone four-weight skin; gentle NPC idle and greeting; feet remain planted','bones':len(arm.bones),'animations':['Idle','Greet'],'native_rig':'worlds/frog/blender/panda-rig.blend','reference':'worlds/frog/blender/panda-front-reference.png','reference_creation':'Built-in imagegen single front derived from approved panda turnaround','reference_prompt':'worlds/frog/blender/panda-front-reference-prompt.txt','environment_source':'Blender authored architecture, bamboo furniture and ceramic objects','role':'Non-player neighbour to visit and share tea. Walking not exposed for this NPC.','validation':{'normalization':True,'weights_max':4,'source_front_verified_by_orthogonal_renders':True,'engine_playback':'pending root integration'}}
(R/'docs/panda-asset-source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PANDA_PREPARED',json.dumps(report),flush=True)
# Real model portrait as evidence, not an imagegen replacement.
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.world.color=(.24,.25,.26);s.view_settings.view_transform='AgX';s.view_settings.exposure=.45
bpy.ops.object.camera_add(location=(1.65,-3.2,1.15));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,.68))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=1.61;s.camera=camera
for pos,power,size in [((-2,-3,4),450,4),((3,-1,2),170,3),((0,3,3),260,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(E/'panda-tripo-rig-blender.png');bpy.ops.render.render(write_still=True)
