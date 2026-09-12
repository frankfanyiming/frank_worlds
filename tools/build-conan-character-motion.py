"""Bind fresh reference-driven Tripo characters; keep input FBXs immutable.

Blender forward -Y becomes Godot +Z. Clips are in-place, velocity contract
is derived from the actual stance travel, and evaluation samples real soles.
"""
from pathlib import Path
import bpy, math, json, sys, hashlib, struct
from mathutils import Vector, Matrix, Quaternion

R=Path(__file__).resolve().parents[1];B=R/'worlds/conan/blender/character-v2';E=R/'docs/evidence/conan-character';FPS=30
only=sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else ''
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def mix(w,n,v):
 if v>1e-8:w[n]=w.get(n,0)+v
settings={'conan':{'height':1.05,'hip':.43,'knee':.266,'ankle':.111,'neck':.704,'shoulder':.650,'shoulder_x':.119,'elbow':(.176,-.007,.537),'wrist':(.230,-.010,.414),'tip':(.259,-.010,.365),'hip_x':.066,'ankle_x':.087,'walk_speed':.70,'walk_frames':24,'run_speed':1.50,'run_frames':18},
 'agasa':{'height':1.56,'hip':.384,'knee':.235,'ankle':.061,'neck':.755,'shoulder':.682,'shoulder_x':.202,'elbow':(.282,-.003,.547),'wrist':(.346,-.010,.421),'tip':(.362,-.020,.369),'hip_x':.112,'ankle_x':.136,'walk_speed':.58,'walk_frames':36,'run_speed':1.05,'run_frames':28}}
for key,c in settings.items():
 if only and only!=key:continue
 H=c['height'];out=E/key;out.mkdir(parents=True,exist_ok=True)
 source=next((B/('tripo-'+key)).glob('tripo-out/*/model.fbx'))
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(source))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)))
 tr=Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Scale(H/(hi.z-lo.z),4)@Matrix.Translation(Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z)))
 for o in meshes:
  xf=tr@o.matrix_world;o.parent=None;o.matrix_world=Matrix.Identity(4)
  for v in o.data.vertices:v.co=xf@v.co
  o.vertex_groups.clear()
  for mod in list(o.modifiers):o.modifiers.remove(mod)
  for face in o.data.polygons:face.use_smooth=True
 for o in list(bpy.context.scene.objects):
  if o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 # Keep the generated UV/color image. Material tuning is restrained and neutral.
 for m in bpy.data.materials:
  m.name='Tripo_'+key+'_reference_v2'
  if not m.use_nodes:continue
  p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if not p:continue
  for socket,value in [('Roughness',.68),('Metallic',0),('Specular IOR Level',.25)]:
   for link in list(p.inputs[socket].links):m.node_tree.links.remove(link)
   p.inputs[socket].default_value=value
  for n in m.node_tree.nodes:
   if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.22
 if key=='conan':
  for o in meshes:
   base=o.data.materials[0];p=next(n for n in base.node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=p.inputs['Base Color'].links[0].from_node.image;pix=list(im.pixels);iw,ih=im.size
   for label,factor in [('BlackHair',(.34,.37,.42,1)),('CobaltBlazer',(.58,.70,.95,1))]:
    m=base.copy();m.name='Tripo_Conan_'+label;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');original=p.inputs['Base Color'].links[0].from_socket
    mixnode=m.node_tree.nodes.new('ShaderNodeMixRGB');mixnode.blend_type='MULTIPLY';mixnode.inputs[0].default_value=1;mixnode.inputs[2].default_value=factor;m.node_tree.links.new(original,mixnode.inputs[1]);m.node_tree.links.new(mixnode.outputs[0],p.inputs['Base Color']);o.data.materials.append(m)
   for face in o.data.polygons:
    center=sum((o.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)/H;rgb=Vector()
    for idx in face.loop_indices:
     uv=o.data.uv_layers.active.data[idx].uv;j=(int(uv.y*ih)%ih*iw+int(uv.x*iw)%iw)*4;rgb+=Vector(pix[j:j+3])
    rgb/=len(face.loop_indices)
    if center.z>.72 and sum(rgb)/3<.42 and max(rgb)-min(rgb)<.17:face.material_index=1
    elif .40<center.z<.71 and rgb.z>rgb.x*1.3 and rgb.z>rgb.y*1.12:face.material_index=2
 # Region-aware joints follow the actual short limbs. Neck keeps head shape rigid.
 data=bpy.data.armatures.new(key+'_skeleton');rig=bpy.data.objects.new(key+'_rig',data);bpy.context.collection.objects.link(rig)
 bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 defs={}
 def bone(n,a,b,parent=None):
  e=data.edit_bones.new(n);e.head=Vector(a)*H;e.tail=Vector(b)*H
  if parent:e.parent=data.edit_bones[parent]
  defs[n]=(e.head.copy(),e.tail.copy())
 bone('Root',(0,0,.01),(0,0,.10));bone('Hips',(0,0,c['hip']),(0,0,c['hip']+.075),'Root')
 bone('Spine',(0,0,c['hip']+.075),(0,0,.60 if key=='conan' else .63),'Hips')
 bone('Chest',(0,0,.60 if key=='conan' else .63),(0,0,c['neck']-.03),'Spine')
 bone('Neck',(0,0,c['neck']-.03),(0,0,c['neck']+.015),'Chest')
 bone('Head',(0,0,c['neck']+.015),(0,0,.95),'Neck')
 for side,sg in [('Left',1),('Right',-1)]:
  def mirror(p):return (p[0]*sg,p[1],p[2])
  shoulder=(sg*c['shoulder_x'],0,c['shoulder']);elbow=mirror(c['elbow']);wrist=mirror(c['wrist']);tip=mirror(c['tip'])
  bone(side+'Clavicle',(sg*.035,0,c['shoulder']),shoulder,'Chest')
  bone(side+'Arm',shoulder,elbow,side+'Clavicle');bone(side+'ForeArm',elbow,wrist,side+'Arm');bone(side+'Hand',wrist,tip,side+'ForeArm')
  bone(side+'Thigh',(sg*c['hip_x'],0,c['hip']),(sg*(c['hip_x']+.01),-.005,c['knee']),'Hips')
  bone(side+'Shin',(sg*(c['hip_x']+.01),-.005,c['knee']),(sg*c['ankle_x'],.018,c['ankle']),side+'Thigh')
  bone(side+'Foot',(sg*c['ankle_x'],.018,c['ankle']),(sg*c['ankle_x'],-.070,c['ankle']),side+'Shin')
 bpy.ops.object.mode_set(mode='OBJECT')
 def segdist(p,a,b):
  d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-(a+d*t)).length
 # Sample base color only to distinguish white coat from dark trouser at the
 # same height; UV seam duplicates are reconciled spatially below.
 colors={}
 if key=='agasa':
  for o in meshes:
   m=o.data.materials[0];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');node=p.inputs['Base Color'].links[0].from_node if p.inputs['Base Color'].links else None
   im=node.image if node and node.type=='TEX_IMAGE' else None
   if im and o.data.uv_layers.active:
    pix=list(im.pixels);iw,ih=im.size;cs={}
    for lp in o.data.loops:
     uv=o.data.uv_layers.active.data[lp.index].uv;u=int(uv.x*iw)%iw;v=int(uv.y*ih)%ih;idx=(v*iw+u)*4;rgb=pix[idx:idx+3];cs.setdefault(lp.vertex_index,[]).append(sum(rgb)/3)
    colors[o.name]={i:sum(v)/len(v) for i,v in cs.items()}
 seam_groups={};weighted={};shoe_ids={s:[] for s in ['Left','Right']};hand_ids=[]
 for o in meshes:
  groups={n:o.vertex_groups.new(name=n) for n in defs}
  for v in o.data.vertices:
   p=v.co/H;x,y,z=p;s='Left' if x>0 else 'Right';w={}
   armline=c['shoulder_x']+(c['wrist'][0]-c['shoulder_x'])*max(0,min(1,(c['shoulder']-z)/(c['shoulder']-c['wrist'][2])))
   arm_region=z<c['neck']-.01 and z>c['tip'][2]-.04 and abs(x)>max(c['shoulder_x']*.78,armline-.046)
   coat=(key=='agasa' and z>.19 and z<.54 and abs(x)<.32 and colors.get(o.name,{}).get(v.index,0)>.47)
   if z>c['neck']+.004:w={'Head':1}
   elif arm_region:
    # Rigid fingers/hand, continuous wrist/elbow transitions.
    if z<c['wrist'][2]-.012:w={s+'Hand':1};hand_ids.append((o.name,v.index))
    else:
     candidates=[s+'Arm',s+'ForeArm',s+'Hand',s+'Clavicle'];ds=sorted((segdist(v.co,*defs[n]),n) for n in candidates)[:2]
     weights=[1/(d+.012*H)**5 for d,n in ds];total=sum(weights);w={n:a/total for a,(_,n) in zip(weights,ds)}
   elif coat:
    w={'Hips':1}
   elif z<c['hip']+.01:
    foot_limit=.086 if key=='conan' else .053
    if z<=foot_limit:w={s+'Foot':1};shoe_ids[s].append((o.name,v.index))
    elif z<c['ankle']+.045:
     t=smooth(foot_limit,c['ankle']+.045,z);w={s+'Foot':1-t,s+'Shin':t}
    elif z<c['knee']+.043:
     t=smooth(c['knee']-.042,c['knee']+.043,z);w={s+'Shin':1-t,s+'Thigh':t}
    else:
     t=smooth(c['hip']-.075,c['hip']+.005,z);center=smooth(.012,.043,abs(x));w={s+'Thigh':(1-t)*center,'Hips':1-(1-t)*center}
   else:
    if z<c['hip']+.095:
     t=smooth(c['hip']+.005,c['hip']+.095,z);w={'Hips':1-t,'Spine':t}
    elif z<c['neck']-.075:
     t=smooth(c['hip']+.12,c['neck']-.075,z);w={'Spine':1-t,'Chest':t}
    else:
     t=smooth(c['neck']-.035,c['neck']+.004,z);w={'Chest':1-t,'Head':t}
   weighted[(o.name,v.index)]={n:ww for n,ww in w.items() if ww>1e-8}
   pos=tuple(round(a,5) for a in v.co);seam_groups.setdefault(pos,[]).append((o.name,v.index))
  o.parent=rig;mod=o.modifiers.new('Reference character skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
 # Identical weights at coincident UV seams, at most four normalized influences.
 for members in seam_groups.values():
  avg={}
  for vi in members:
   for n,w in weighted[vi].items():mix(avg,n,w/len(members))
  avg=dict(sorted(avg.items(),key=lambda x:-x[1])[:4]);total=sum(avg.values());avg={n:w/total for n,w in avg.items()}
  for vi in members:weighted[vi]=avg
 for o in meshes:
  for v in o.data.vertices:
   for n,w in weighted[o.name,v.index].items():o.vertex_groups[n].add([v.index],w,'REPLACE')
 byname={o.name:o for o in meshes};shoe_points={s:[byname[n].data.vertices[i].co.copy() for n,i in ids] for s,ids in shoe_ids.items()}
 scene=bpy.context.scene;scene.render.fps=FPS
 def rotate(n,axis,angle):
  p=rig.pose.bones[n];q=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=p.rotation_quaternion@q.inverted()@Quaternion(axis,angle)@q
 def setbone(n,head,tail):
  p=rig.pose.bones[n];b=p.bone;q=(b.tail_local-b.head_local).rotation_difference(tail-head)@b.matrix_local.to_quaternion();p.matrix=Matrix.LocRotScale(head,q,Vector((1,1,1)));bpy.context.view_layer.update()
 def foot_target(side,phase,run):
  duration=c['run_frames' if run else 'walk_frames']/FPS;speed=c['run_speed' if run else 'walk_speed'];duty=.44 if run else .60;amp=speed*duration*duty/2
  if phase<duty:y=-amp+2*amp*phase/duty;z=0;pitch=0
  else:
   t=(phase-duty)/(1-duty);y=amp*math.cos(math.pi*t);z=(.072 if run else .042)*H*math.sin(math.pi*t)**1.35;pitch=-.18*math.sin(math.tau*t)
  b=rig.data.bones[side+'Foot'];rest=b.head_local.copy();q=Quaternion((1,0,0),pitch);minimum=min((q@(p-rest)).z for p in shoe_points[side]);ankle=rest+Vector((0,y,z));ankle.z=z-minimum+.001
  return ankle,q,z
 def animate_leg(s,ankle,q):
  hip=rig.pose.bones['Hips'].matrix@rig.data.bones['Hips'].matrix_local.inverted()@rig.data.bones[s+'Thigh'].head_local
  l1=rig.data.bones[s+'Thigh'].length;l2=rig.data.bones[s+'Shin'].length;axis=ankle-hip;d=axis.length
  if d>=l1+l2:raise RuntimeError(f'{key} unreachable {s}: {d} >= {l1+l2}')
  axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);lift=math.sqrt(max(0,l1*l1-along*along));pole=Vector((0,-1,0));pole=(pole-axis*pole.dot(axis)).normalized();knee=hip+axis*along+pole*lift
  setbone(s+'Thigh',hip,knee);setbone(s+'Shin',knee,ankle);b=rig.data.bones[s+'Foot'];rig.pose.bones[s+'Foot'].matrix=Matrix.LocRotScale(ankle,q@b.matrix_local.to_quaternion(),Vector((1,1,1)));bpy.context.view_layer.update()
 report={'character':key,'source':'New reference-driven Tripo v3.1 mesh, custom Blender rig','input_fbx_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'height':H,'forward':'Godot +Z','faces':sum(len(o.data.polygons) for o in meshes),'bones':len(data.bones),'max_weights':max(len(w) for w in weighted.values()),'clips':{},'foot_samples':{}}
 for name,frames in [('Idle',90),('Walk',c['walk_frames']),('Run',c['run_frames']),('Wave',60),('Talk',72),('Read',90),('Sit',90)]:
  rig.animation_data_create();act=bpy.data.actions.new(name);rig.animation_data.action=act
  for f in range(frames+1):
   t=f/frames;scene.frame_set(f)
   for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=Vector();p.scale=(1,1,1)
   # Lower the A-pose arms into a comfortable relaxed stance; preserve elbows.
   for s,sg in [('Left',1),('Right',-1)]:rotate(s+'Arm',(0,1,0),sg*.24)
   rotate('Head',(0,0,1),.010*math.sin(t*math.tau));rotate('Chest',(1,0,0),.004*math.sin(t*math.tau))
   if name in ['Walk','Run']:
    run=name=='Run';targets={s:foot_target(s,(t+off)%1,run) for s,off in [('Left',0),('Right',.5)]}
    # Rise at midstance instead of permanently crouching. Each leg limits hip
    # height only as much as reach requires, while planted feet remain fixed.
    maxz=c['hip']*H-.003
    for s,(ankle,q,z) in targets.items():
     hiprest=data.bones[s+'Thigh'].head_local;length=(data.bones[s+'Thigh'].length+data.bones[s+'Shin'].length)*.985
     horiz=(ankle.x-hiprest.x)**2+(ankle.y-hiprest.y)**2
     maxz=min(maxz,ankle.z+math.sqrt(max(.001,length*length-horiz)))
    drop=maxz-c['hip']*H;rig.pose.bones['Hips'].location=data.bones['Hips'].matrix_local.to_quaternion().inverted()@Vector((0,0,drop));bpy.context.view_layer.update()
    rotate('Chest',(1,0,0),.075 if run else .008)
    for s,off in [('Left',0),('Right',.5)]:
     phase=(t+off)%1;animate_leg(s,targets[s][0],targets[s][1]);rotate(s+'Arm',(1,0,0),-math.cos(phase*math.tau)*(.40 if run else .23));rotate(s+'ForeArm',(1,0,0),.65 if run else .16)
   elif name in ['Wave','Talk']:
    rotate('RightArm',(0,1,0),.60 if name=='Wave' else .10);rotate('RightForeArm',(1,0,0),.55 if name=='Wave' else .40);rotate('RightHand',(0,0,1),.12*math.sin(t*math.tau*2))
   elif name in ['Read','Sit']:
    for s in ['Left','Right']:rotate(s+'Arm',(1,0,0),.32);rotate(s+'ForeArm',(1,0,0),1.05)
    if name=='Sit':
     for s in ['Left','Right']:rotate(s+'Thigh',(1,0,0),1.25);rotate(s+'Shin',(1,0,0),-1.30)
   for p in rig.pose.bones:p.keyframe_insert('rotation_quaternion',frame=f);p.keyframe_insert('location',frame=f)
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for point in fc.keyframe_points:point.interpolation='LINEAR'
  track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,0,act);track.mute=True
  report['clips'][name]={'duration':frames/FPS}
  if name in ['Walk','Run']:report['clips'][name]['reference_speed']=c['walk_speed' if name=='Walk' else 'run_speed']
 # Evaluate actual vertices at subframes; support drift includes forward travel.
 for name in ['Walk','Run']:
  frames=c['walk_frames' if name=='Walk' else 'run_frames'];speed=c['walk_speed' if name=='Walk' else 'run_speed'];duty=.60 if name=='Walk' else .44;rig.animation_data.action=bpy.data.actions[name]
  rows=[];bycycle={};minz=10;rigid_error=0;seam_error=0
  for i in range(97):
   frame=frames*i/96;scene.frame_set(int(frame),subframe=frame-int(frame));dg=bpy.context.evaluated_depsgraph_get();evaluated={o.name:o.evaluated_get(dg).to_mesh() for o in meshes}
   row={'time':frame/FPS,'feet':{}}
   for s,off in [('Left',0),('Right',.5)]:
    ids=shoe_ids[s];coords=[evaluated[n].vertices[idx].co.copy() for n,idx in ids];bottom=min(p.z for p in coords);center=sum(coords,Vector())/len(coords);phase=(i/96+off)%1
    transform=rig.pose.bones[s+'Foot'].matrix@data.bones[s+'Foot'].matrix_local.inverted()
    for (n,idx),p in zip(ids,coords):rigid_error=max(rigid_error,(p-transform@byname[n].data.vertices[idx].co).length)
    row['feet'][s]={'sole_z':bottom,'center_y':center.y,'phase':phase,'stance':phase<duty};minz=min(minz,bottom)
    if .025<phase<duty-.025:
     cycle=math.floor(i/96+off);bycycle.setdefault((s,cycle),[]).append(center.y-speed*frame/FPS)
   for members in seam_groups.values():
    if len(members)<2:continue
    points=[evaluated[n].vertices[idx].co for n,idx in members];seam_error=max(seam_error,max((p-points[0]).length for p in points))
   for o in meshes:o.evaluated_get(dg).to_mesh_clear()
   rows.append(row)
  drift=max(max(a)-min(a) for a in bycycle.values() if len(a)>1)
  report['clips'][name].update({'minimum_sole_z':minz,'max_rigid_shoe_error':rigid_error,'stance_world_drift':drift,'max_uv_seam_opening':seam_error,'max_lift':{s:max(row['feet'][s]['sole_z'] for row in rows) for s in shoe_ids}})
  report['foot_samples'][name]=rows
  if minz<=-.004 or rigid_error>=.004 or drift>=.005 or seam_error>=.00008:(out/'motion-check-draft.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
  assert minz>-.004,(key,name,'sole penetration',minz)
  assert rigid_error<.004,(key,name,'shoe deformation',rigid_error)
  assert drift<.005,(key,name,'support sliding',drift)
  assert seam_error<.00008,(key,name,'UV seam',seam_error)
 rig.animation_data.action=None;scene.frame_set(0)
 for p in rig.pose.bones:p.rotation_quaternion=Quaternion();p.location=Vector()
 for im in bpy.data.images:
  if im.has_data:im.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(B/(key+'-rig.blend')))
 target=B/(key+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_nla_strips=True,export_tangents=True)
 if key=='conan':
  # Blender's glTF exporter ignores this MixRGB multiply when gathering a
  # shared image. Store the equivalent standard baseColorFactor explicitly.
  raw=target.read_bytes();json_size=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+json_size]);tail=raw[20+json_size:]
  for material in gltf['materials']:
   factors={'Tripo_Conan_BlackHair':[.34,.37,.42,1],'Tripo_Conan_CobaltBlazer':[.58,.70,.95,1]}
   if material['name'] in factors:material['pbrMetallicRoughness']['baseColorFactor']=factors[material['name']]
  payload=json.dumps(gltf,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4)
  target.write_bytes(struct.pack('<III',0x46546c67,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4e4f534a)+payload+tail)
 report['runtime_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();report['runtime_bytes']=target.stat().st_size
 (out/'motion-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('CHARACTER_READY',key,json.dumps({k:v for k,v in report.items() if k!='foot_samples'}),flush=True)
