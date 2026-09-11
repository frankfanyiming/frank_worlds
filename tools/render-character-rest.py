import bpy, math
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];E=R/'docs/evidence/character-motion'
for species,filename,forward in [('frog','frog-rig-jump.blend',1),('panda','panda-rig.blend',-1)]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'worlds/frog/blender/character-motion-originals'/filename))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear()
 for p in rig.pose.bones:p.rotation_quaternion=Quaternion();p.location=(0,0,0);p.scale=(1,1,1)
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=640;s.render.resolution_y=720;s.render.resolution_percentage=100;s.world.color=(.3,.3,.3)
 for pos,power,size in [((2,forward*3,4),350,4),((-3,forward,2),150,3),((0,-forward*3,3),170,3)]:
  bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
 for label,pos in [('front',(0,forward*4,.7)),('side',(4,0,.7)),('quarter',(2,forward*3,1.0))]:
  bpy.ops.object.camera_add(location=pos);o=bpy.context.object;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=1.6;s.camera=o;s.render.filepath=str(E/(species+'-before-'+label+'.png'));bpy.ops.render.render(write_still=True)
