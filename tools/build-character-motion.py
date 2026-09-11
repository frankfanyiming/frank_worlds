"""Re-skin the existing Tripo meshes and author measurable in-place locomotion.

Input backups are immutable Tripo-derived rigs. No generated primitive replaces
either animal. Animation speeds describe the linear support-foot velocity, so a
controller can scale playback by measured displacement instead of desired input.
"""
from pathlib import Path
import bpy, math, json, hashlib, sys, numpy as np
from mathutils import Vector, Matrix, Quaternion

R=Path(__file__).resolve().parents[1];B=R/'worlds/frog/blender';A=R/'worlds/frog/source/assets';E=R/'docs/evidence/character-motion'
FPS=30;TAU=math.tau
E.mkdir(parents=True,exist_ok=True)
META={
 'frog':{'walk_speed':1.18,'run_speed':2.45,'jump_prepare':.12,'jump_takeoff':.13,'land_duration':10/30,'walk_cycle':20/30,'run_cycle':14/30,'walk_support_fraction':.5,'run_support_fraction':.40,'forward':'Godot -Z / Blender +Y','walk_lift':.13,'run_lift':.18},
 'panda':{'walk_speed':.68,'walk_cycle':24/30,'walk_support_fraction':.58,'forward':'Godot +Z / Blender -Y','walk_lift':.10},
 'fps':FPS,'root_motion':'In place. Match playback speed to actual displacement / reference speed; support feet have constant backward velocity.',
 'version':'2026-09-12-visible-footfall-v1'
}

def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def distance(p,a,b):
 d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return(p-a-t*d).length
def reset(rig):
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0);p.scale=(1,1,1)

reports={}
for species,filename,forward in [('frog','frog-rig-jump.blend',1),('panda','panda-rig.blend',-1)]:
 if '--only' in sys.argv and species!=sys.argv[sys.argv.index('--only')+1]:continue
 bpy.ops.wm.open_mainfile(filepath=str(B/'character-motion-originals'/filename))
 mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');oldrig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 oldrig.animation_data_clear();reset(oldrig);oldbones={b.name:(b.head_local.copy(),b.tail_local.copy(),b.parent.name if b.parent else None) for b in oldrig.data.bones}
 mesh.parent=None;mesh.matrix_world=Matrix.Identity(4)
 for mod in list(mesh.modifiers):
  if mod.type=='ARMATURE':mesh.modifiers.remove(mod)
 mesh.vertex_groups.clear()
 for o in list(bpy.context.scene.objects):
  if o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
 for action in list(bpy.data.actions):bpy.data.actions.remove(action)

 # Gentle rest-shape edits retain every source face, UV and texture. Shorten the
 # panda's long torso; narrow the frog's splayed haunch silhouette slightly.
 def sculpt(p):
  x,y,z=p
  if species=='frog':
   haunch=smooth(.08,.17,z)*(1-smooth(.34,.50,z));x*=1-.07*haunch
   if y<0:y*=1-.07*haunch
   head=smooth(.58,.74,z);x*=1+.015*head
   # Shorter, rounder-looking fingers retain the original webbed source mesh.
   hand=smooth(.43,.50,abs(x))*(1-smooth(.30,.40,z))*smooth(.14,.24,y)
   x*=1-.045*hand
  else:
   z-=.075*smooth(.38,.78,z)
   # Keep height1.35 while enlarging the head-to-torso ratio, not the whole NPC.
   scale=1.35/1.275;x*=scale;y*=scale;z*=scale
   paw=1-smooth(.085,.165,z)
   center=.21 if x>=0 else -.21;x+=(x-center)*.12*paw;y-=.020*paw
  return Vector((x,y,z))
 for v in mesh.data.vertices:v.co=sculpt(v.co)
 for p in mesh.data.polygons:p.use_smooth=True
 # Original color and normal maps remain. Low-strength micro normals retain the
 # soft toy-like reference shape instead of adding gritty surface highlights.
 for material in mesh.data.materials:
  if not material.use_nodes:continue
  for n in material.node_tree.nodes:
   if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.35
   if n.type=='BSDF_PRINCIPLED':
    n.inputs['Metallic'].default_value=0
    if not n.inputs['Roughness'].is_linked:n.inputs['Roughness'].default_value=.78

 # Semantic skin regions come from the existing Tripo UV texture: cream belly
 # and brown satchel are rigid torso regions, not fragments of a leg or arm.
 base=next(n for n in mesh.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 image=base.inputs['Base Color'].links[0].from_node.image;tw,th=image.size
 pixels=np.array(image.pixels[:],dtype=np.float32).reshape(th,tw,4);colors={}
 for loop in mesh.data.loops:
  if loop.vertex_index in colors:continue
  uv=mesh.data.uv_layers.active.data[loop.index].uv;colors[loop.vertex_index]=pixels[int(uv.y*th)%th,int(uv.x*tw)%tw,:3]
 del pixels
 # UV-seam duplicate vertices must receive identical region classifications.
 # Averaging by geometric position prevents the same surface splitting at UV seams.
 welded={}
 for v in mesh.data.vertices:welded.setdefault(tuple(round(c,5) for c in v.co),[]).append(v.index)
 for indices in welded.values():
  if len(indices)>1:
   color=sum((colors[i] for i in indices))/len(indices)
   for i in indices:colors[i]=color
 if species=='panda':
  for material in mesh.data.materials:
   for n in material.node_tree.nodes:
    if n.type=='BSDF_PRINCIPLED':
     for l in list(n.inputs['Normal'].links):material.node_tree.links.remove(l)
     for l in list(n.inputs['Roughness'].links):material.node_tree.links.remove(l)
     n.inputs['Roughness'].default_value=.86

 arm=bpy.data.armatures.new(species.title()+' visible-step skeleton');rig=bpy.data.objects.new(species.title()+'Rig',arm);bpy.context.collection.objects.link(rig);rig.show_in_front=True
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bones={}
 for name,(a,b,parent) in oldbones.items():
  a=sculpt(a);b=sculpt(b)
  if name.startswith(('thigh.','shin.','foot.')):
   s=1 if name.endswith('.L') else -1
   if species=='frog':
    hip=Vector((s*.235,-.14,.39));knee=Vector((s*.415,-.24,.225));ankle=Vector((s*.335,-.045,.067));toe=ankle+Vector((0,.225,-.018))
   else:
    hip=Vector((s*.18,.03,.335));knee=Vector((s*.235,-.13,.20));ankle=Vector((s*.215,-.035,.063));toe=ankle+Vector((0,-.145,-.018))
   a,b={'thigh':(hip,knee),'shin':(knee,ankle),'foot':(ankle,toe)}[name.split('.')[0]]
  e=arm.edit_bones.new(name);e.head=a;e.tail=b
  if parent:e.parent=arm.edit_bones[parent]
  e.align_roll(Vector((0,forward,0)));bones[name]=(a.copy(),b.copy())
 bpy.ops.object.mode_set(mode='OBJECT');mesh.parent=rig;mod=mesh.modifiers.new('Four-weight anatomical skin','ARMATURE');mod.object=rig
 groups={n:mesh.vertex_groups.new(name=n) for n in bones}
 for v in mesh.data.vertices:
  x,y,z=v.co;ax=abs(x);side='L' if x>=0 else 'R'
  if species=='frog':
   head=smooth(.63,.73,z);sp=smooth(.38,.53,z);w={'hips':1-sp,'spine':sp}
   legs=(1-smooth(.355,.47,z))*smooth(.18,.285,ax);foot=1-smooth(.065,.095,z);shin=1-smooth(.075,.105,z)
   ar=smooth(.305,.375,ax)*smooth(.27,.33,z)*(1-smooth(.59,.68,z))*smooth(.04,.14,y)
   color=colors[v.index];chroma=(max(color)-min(color))/max(.01,max(color));green=smooth(.20,.34,chroma)
   legs*=1 if z<.075 else green
  else:
   head=smooth(.685,.765,z);sp=smooth(.31,.56,z);w={'hips':1-sp,'spine':sp}
   legs=(1-smooth(.215,.32,z))*smooth(.085,.145,ax);foot=1-smooth(.08,.135,z);shin=1-smooth(.145,.235,z)
   ar=smooth(.333,.388,ax)*smooth(.30,.38,z)*(1-smooth(.66,.745,z))
   color=colors[v.index];black=1-smooth(.48,.68,max(color))
   legs*=(1-smooth(.31,.37,ax))*(1 if z<.075 else black*(1-smooth(.16,.25,-y)))
   ar*=1-smooth(.20,.30,-y)
  if legs>.00001:
   w={n:a*(1-legs) for n,a in w.items()};w['foot.'+side]=legs*foot;w['shin.'+side]=legs*(1-foot)*shin;w['thigh.'+side]=legs*(1-foot)*(1-shin)
  if ar>.00001:
   ns=['upper_arm.'+side,'forearm.'+side,'hand.'+side];ds=[1/max(.025,distance(v.co,*bones[n]))**4 for n in ns];total=sum(ds);w={n:a*(1-ar) for n,a in w.items()}
   for n,d in zip(ns,ds):w[n]=ar*d/total
  w={n:a*(1-head) for n,a in w.items()};w['head']=head
  weights=sorted([(n,a) for n,a in w.items() if a>.000001],key=lambda t:-t[1])[:4];total=sum(a for _,a in weights)
  for n,a in weights:groups[n].add([v.index],a/total,'REPLACE')


 rest={n:b.matrix_local.to_quaternion() for n,b in arm.bones.items()}
 def rotate(n,x=0,y=0,z=0):
  q=rest[n];r=Quaternion((0,0,1),z)@Quaternion((0,1,0),y)@Quaternion((1,0,0),x);rig.pose.bones[n].rotation_quaternion=q.inverted()@r@q
 def leg(side,dy,lift,drop,toe_pitch=0):
  tn='thigh.'+side;sn='shin.'+side;fn='foot.'+side
  hip=arm.bones[tn].head_local+Vector((0,0,drop));ankle=arm.bones[sn].tail_local+Vector((0,forward*dy,lift));delta=ankle-hip;D=delta.length;L1=arm.bones[tn].length;L2=arm.bones[sn].length
  assert D<L1+L2-.0001,(species,side,'unreachable',D,L1+L2,dy,lift,drop)
  dire=delta.normalized();aa=(L1*L1-L2*L2+D*D)/(2*D);bend=math.sqrt(max(0,L1*L1-aa*aa))
  rest_axis=(arm.bones[sn].tail_local-arm.bones[tn].head_local).normalized();rest_knee=arm.bones[tn].tail_local-arm.bones[tn].head_local;pole=rest_knee-rest_axis*rest_knee.dot(rest_axis);perp=(pole-dire*pole.dot(dire)).normalized();knee=hip+dire*aa+perp*bend
  q1=(arm.bones[tn].tail_local-arm.bones[tn].head_local).rotation_difference(knee-hip);q2=(arm.bones[sn].tail_local-arm.bones[sn].head_local).rotation_difference(ankle-knee)
  rig.pose.bones[tn].rotation_quaternion=rest[tn].inverted()@q1@rest[tn]
  rig.pose.bones[sn].rotation_quaternion=rest[sn].inverted()@q1.inverted()@q2@rest[sn]
  qfoot=Quaternion((1,0,0),forward*toe_pitch)
  rig.pose.bones[fn].rotation_quaternion=rest[fn].inverted()@q2.inverted()@qfoot@rest[fn]

 def footpath(u,speed,cycle,support,lift):
  half=speed*cycle*support/2
  if u<support:return half-speed*cycle*u,0,0
  v=(u-support)/(1-support)
  # Eased swing moves forward while support is strictly linear for foot lock.
  dy=-half+2*half*(v*v*(3-2*v));h=lift*math.sin(math.pi*v)
  return dy,h,.18*math.sin(math.pi*v)

 actions={};specs=[('Idle',90),('Walk',20 if species=='frog' else 24),('Sit',90),('Greet',60)]
 if species=='frog':specs += [('Run',14),('JumpStart',8),('JumpAir',30),('Land',10)]
 else:specs += [('Turn',24),('Stand',18)]
 rig.animation_data_create()
 for name,frames in specs:
  action=bpy.data.actions.new(name);rig.animation_data.action=action
  for frame in range(1,frames+2):
   t=(frame-1)/frames;phase=t*TAU;reset(rig);drop=0
   if name in ['Walk','Run','Turn']:
    isrun=name=='Run';cycle=frames/FPS;speed=META[species]['run_speed' if isrun else 'walk_speed'];support=META[species]['run_support_fraction' if isrun else 'walk_support_fraction'];lift=META[species]['run_lift' if isrun else 'walk_lift']
    drop=(-.033 if species=='frog' else -.025)+(.016 if species=='frog' else .013)*math.cos(phase*2)
    rig.pose.bones['root'].location=rest['root'].inverted()@Vector((0,0,drop))
    for side,off in [('L',0),('R',.5)]:
     dy,h,pitch=footpath((t+off)%1,speed,cycle,support,lift)
     if name=='Turn':dy*=.3
     leg(side,dy,h,drop,pitch);sign=1 if side=='L' else -1
     rotate('upper_arm.'+side,x=forward*(.26 if species=='frog' else .23)*sign*math.sin(phase),y=sign*.10)
     rotate('forearm.'+side,x=forward*(.15+.06*math.sin(phase+off*TAU)))
    rotate('spine',x=forward*(.07 if isrun else .025),z=.025*math.sin(phase));rotate('head',x=-forward*.02,z=-.018*math.sin(phase))
   elif name in ['Sit','Stand']:
    amount=1 if name=='Sit' else 1-smooth(0,1,t);drop=(-.082 if species=='frog' else -.115)*amount
    rig.pose.bones['root'].location=rest['root'].inverted()@Vector((0,0,drop))
    for side,s in [('L',1),('R',-1)]:
     leg(side,.045*amount,0,drop);rotate('upper_arm.'+side,x=forward*.20*amount,y=s*.25*amount);rotate('forearm.'+side,x=forward*.60*amount)
    rotate('head',x=-forward*.04*amount,z=.012*math.sin(phase))
   elif name=='JumpStart':
    seconds=t*8/30
    if seconds<=.12:drop=-.10*smooth(0,.12,seconds);dy=.035;lift=0
    else:
     push=smooth(.12,.25,seconds);drop=-.10*(1-push)+.015*push;dy=.035*(1-push)-.04*push;lift=.025*push
    rig.pose.bones['root'].location=rest['root'].inverted()@Vector((0,0,drop))
    for side,s in [('L',1),('R',-1)]:leg(side,dy,lift,drop);rotate('upper_arm.'+side,x=.30*math.sin(math.pi*t),y=-s*.10)
    rotate('spine',x=.07*math.sin(math.pi*t))
   elif name=='JumpAir':
    # The controller supplies airborne height. Keep the toes below the bulky
    # haunches instead of pulling the feet through them to simulate a jump.
    drop=.012;rig.pose.bones['root'].location=rest['root'].inverted()@Vector((0,0,drop))
    for side,s in [('L',1),('R',-1)]:leg(side,.015,.003+.002*math.sin(phase),drop,-.035);rotate('upper_arm.'+side,x=-.14,y=-s*.23);rotate('forearm.'+side,x=.30)
   elif name=='Land':
    drop=-.095*math.sin(math.pi*t)*(1-t*.45);rig.pose.bones['root'].location=rest['root'].inverted()@Vector((0,0,drop))
    for side,s in [('L',1),('R',-1)]:leg(side,.025*(1-t),0,drop);rotate('upper_arm.'+side,x=.10*(1-t),y=-s*.08)
   else:
    # A relaxed arm pose avoids the old spread-finger T stance at idle.
    for side,s in [('L',1),('R',-1)]:
     rotate('upper_arm.'+side,y=s*.10,x=forward*.04)
     rotate('forearm.'+side,x=forward*.15)
    rotate('spine',x=.008*math.sin(phase));rotate('head',x=.009*math.sin(phase+.7),z=.014*math.sin(phase))
    if name=='Greet':
     amplitude=math.sin(math.pi*t)**2;rotate('head',x=forward*.06*amplitude);rotate('upper_arm.L',x=forward*.28*amplitude,y=-.32*amplitude);rotate('forearm.L',x=forward*.60*amplitude,z=.08*math.sin(phase*2)*amplitude)
   for p in rig.pose.bones:
    p.keyframe_insert('rotation_quaternion',frame=frame,group=p.name)
    if p.name=='root':p.keyframe_insert('location',frame=frame,group=p.name)
  action.use_fake_user=True;actions[name]=action
  track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,1,action);strip.name=name;track.mute=True

 # Sample the evaluated skinned mesh, not merely IK target coordinates. Foot
 # sole vertices are selected by their immutable rest position and >95% weight.
 soles={}
 for side in ['L','R']:
  group=groups['foot.'+side].index
  soles[side]=[v.index for v in mesh.data.vertices if v.co.z<.028 and any(g.group==group and g.weight>.95 for g in v.groups)]
  assert len(soles[side])>20,(species,side,'missing real sole vertices',len(soles[side]))
 qa={'species':species,'faces':len(mesh.data.polygons),'vertices':len(mesh.data.vertices),'height':max(v.co.z for v in mesh.data.vertices),'bones':len(arm.bones),'sole_vertex_counts':{s:len(i) for s,i in soles.items()},'clips':{},'all_weights_normalized':all(abs(sum(g.weight for g in v.groups)-1)<.00001 and len(v.groups)<=4 for v in mesh.data.vertices)}
 for name,frames in specs:
  rig.animation_data.action=actions[name];samples=[];max_seam_gap=0.0
  for frame in range(1,frames+2):
   bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());em=evaluated.to_mesh()
   feet={}
   for side,indices in soles.items():
    pts=[em.vertices[i].co.copy() for i in indices];feet[side]={'sole_min_z':round(min(p.z for p in pts),6),'center_forward':round(sum(p.y*forward for p in pts)/len(pts),6),'center_x':round(sum(p.x for p in pts)/len(pts),6)}
   for indices in welded.values():
    if len(indices)>1:
     p=em.vertices[indices[0]].co
     max_seam_gap=max(max_seam_gap,max((em.vertices[i].co-p).length for i in indices[1:]))
   samples.append({'frame':frame,'t':round((frame-1)/FPS,6),'feet':feet});evaluated.to_mesh_clear()
  summary={}
  for side in ['L','R']:
   zs=[s['feet'][side]['sole_min_z'] for s in samples];ys=[s['feet'][side]['center_forward'] for s in samples]
   summary[side]={'min_z':min(zs),'max_lift':max(zs),'forward_travel':max(ys)-min(ys)}
  qa['clips'][name]={'duration':frames/FPS,'summary':summary,'samples':samples,'max_duplicate_vertex_seam_gap':round(max_seam_gap,7)}
  assert max_seam_gap<.0001,(species,name,'UV seam separated',max_seam_gap)
  if name in ['Walk','Run']:
   speed=META[species]['run_speed' if name=='Run' else 'walk_speed'];support=META[species]['run_support_fraction' if name=='Run' else 'walk_support_fraction'];duration=frames/FPS
   for side,offset in [('L',0),('R',.5)]:
    intervals=[];locked=[]
    for sample in samples[:-1]:
     t=sample['t']/duration;u=(t+offset)%1
     if u<support-1e-4:
      foot=sample['feet'][side];locked.append(foot['center_forward']+speed*sample['t'])
      intervals.append({'t':sample['t'],'u':u,'z':foot['sole_min_z'],'lock':locked[-1]})
    # Right support straddles cycle boundary; compare each contiguous segment.
    segments=[];current=[];prev=None
    for row in intervals:
     if prev is not None and row['t']-prev>1.01/FPS:
      if current:segments.append(current)
      current=[]
     current.append(row);prev=row['t']
    if current:segments.append(current)
    drift=max(max(r['lock'] for r in ss)-min(r['lock'] for r in ss) for ss in segments)
    summary[side]['stance_world_drift']=round(drift,6)
    summary[side]['stance_ground_error']=round(max(abs(r['z']) for r in intervals),6)
    assert drift<.002,(species,name,side,'sliding',drift)
    assert summary[side]['stance_ground_error']<.008,(species,name,side,'sole not grounded',summary[side])
    assert summary[side]['max_lift']>(.075 if species=='panda' else .09),(species,name,side,'foot does not lift')
  print('CLIP',species,name,json.dumps(summary),flush=True)
 reports[species]=qa;(E/(species+'-motion-check.json')).write_text(json.dumps(qa,ensure_ascii=False,indent=2))
 rig.animation_data.action=None;reset(rig);bpy.context.scene.frame_set(1);bpy.context.scene.render.fps=FPS
 for im in bpy.data.images:
  if im.type=='IMAGE' and im.size[0]>0:
   try:im.pack()
   except RuntimeError:pass
 bpy.ops.wm.save_as_mainfile(filepath=str(B/filename))
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(A/(species+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_action_filter=False,export_cameras=False,export_lights=False)
 qa['runtime_sha256']=hashlib.sha256((A/(species+'.glb')).read_bytes()).hexdigest();qa['runtime_bytes']=(A/(species+'.glb')).stat().st_size
 (E/(species+'-motion-check.json')).write_text(json.dumps(qa,ensure_ascii=False,indent=2))
 print('CHARACTER_BUILT',species,qa['runtime_bytes'],qa['runtime_sha256'],flush=True)

(A/'locomotion.json').write_text(json.dumps(META,ensure_ascii=False,indent=2))
(E/'locomotion-contract.json').write_text(json.dumps(META,ensure_ascii=False,indent=2))
import runpy
runpy.run_path(str(R/'tools/update-character-provenance.py'),run_name='__main__')
