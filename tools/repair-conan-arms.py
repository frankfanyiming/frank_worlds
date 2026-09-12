"""Repair only arm skin/animation channels in immutable Tripo GLBs.

Run with Blender --background --python tools/repair-conan-arms.py [-- --only conan].
No geometry, material, leg bind, leg animation, clip duration or foot changes.
Kogoro arm pivots use the original Tripo-fitted joints, replacing guessed pivots.
"""
import copy, hashlib, json, math, struct, sys
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

R=Path(__file__).resolve().parents[1]
B=R/'worlds/conan/blender/arms-2026-09-13'
E=R/'docs/evidence/conan-arms-2026-09-13'
ARMS={s+n for s in ('Left','Right') for n in ('Arm','ForeArm','Hand')}
COMP={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
DIMS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

class GLB:
 def __init__(self,path):
  raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
  self.g=json.loads(raw[20:20+size]);self.data=bytearray(raw[28+size:]);self.original_sha=hashlib.sha256(raw).hexdigest()
 def read(self,index):
  a=self.g['accessors'][index];v=self.g['bufferViews'][a['bufferView']];fmt,bs=COMP[a['componentType']];dim=DIMS[a['type']]
  off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',bs*dim)
  return [list(struct.unpack_from('<'+fmt*dim,self.data,off+i*stride)) for i in range(a['count'])]
 def append(self,rows,kind,component=5126):
  while len(self.data)%4:self.data.append(0)
  start=len(self.data);fmt=COMP[component][0];dim=DIMS[kind]
  for row in rows:self.data.extend(struct.pack('<'+fmt*dim,*row))
  self.g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(self.data)-start})
  self.g['accessors'].append({'bufferView':len(self.g['bufferViews'])-1,'componentType':component,'count':len(rows),'type':kind})
  return len(self.g['accessors'])-1
 def save(self,path):
  while len(self.data)%4:self.data.append(0)
  self.g['buffers'][0]['byteLength']=len(self.data)
  text=json.dumps(self.g,separators=(',',':')).encode();text+=b' '*(-len(text)%4)
  path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(self.data))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(self.data),0x004e4942)+self.data)

def quat(row):return Quaternion((row[3],row[0],row[1],row[2]))
def qrow(q):q.normalize();return [q.x,q.y,q.z,q.w]
def trs(n):
 if 'matrix' in n:return Matrix([n['matrix'][i:i+4] for i in range(0,16,4)]).transposed()
 return Matrix.LocRotScale(Vector(n.get('translation',[0,0,0])),quat(n.get('rotation',[0,0,0,1])),Vector(n.get('scale',[1,1,1])))
def parents(g):return {child:i for i,n in enumerate(g['nodes']) for child in n.get('children',[])}
def worlds(g,overrides=None):
 parent=parents(g);cache={}
 def visit(i):
  if i not in cache:cache[i]=(visit(parent[i]) if i in parent else Matrix.Identity(4))@trs((overrides or {}).get(i,g['nodes'][i]))
  return cache[i]
 for i in range(len(g['nodes'])):visit(i)
 return cache
def sample(glb,animation,t):
 overrides={}
 for channel in animation['channels']:
  target=channel['target'];i=target['node'];path=target['path'];s=animation['samplers'][channel['sampler']]
  times=[v[0] for v in glb.read(s['input'])];rows=glb.read(s['output'])
  k=0
  while k+1<len(times) and times[k+1]<=t+1e-7:k+=1
  value=rows[k]
  if k+1<len(times) and s.get('interpolation','LINEAR')!='STEP':
   f=max(0,min(1,(t-times[k])/(times[k+1]-times[k])))
   value=qrow(quat(rows[k]).slerp(quat(rows[k+1]),f)) if path=='rotation' else [(1-f)*a+f*b for a,b in zip(rows[k],rows[k+1])]
  overrides.setdefault(i,copy.deepcopy(glb.g['nodes'][i]))[path]=value
 return overrides
def distance(p,a,b):
 d=b-a;u=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-a-u*d).length
def smooth(a,b,x):t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def native(p):return Vector((p[0],p[2],-p[1])) # Blender Z-up/-Y forward -> glTF Y-up/+Z forward.

def repair(key):
 source=B/'originals'/(key+'.glb');asset=GLB(source);old=GLB(source);g=asset.g
 names={n.get('name',''):i for i,n in enumerate(g['nodes'])};parent=parents(g);before=worlds(g)
 joints={};skin=g['skins'][0];joint_index={g['nodes'][n]['name']:i for i,n in enumerate(skin['joints'])}
 for side in ('Left','Right'):
  for suffix,next_suffix in [('Arm','ForeArm'),('ForeArm','Hand')]:
   n=side+suffix;joints[n]=[before[names[n]].translation.copy(),before[names[side+next_suffix]].translation.copy()]
  n=side+'Hand';p=before[names[n]].translation.copy();d=(p-joints[side+'ForeArm'][0]).normalized();joints[n]=[p,p+d*.14]
 if key=='kogoro':
  # Native Tripo-fitted arm joints measured from the preserved original rig.
  fitted={'Left':[(.185073,.082861,1.381668),(.311067,.082861,1.113930),(.397688,.043488,.885567)],
          'Right':[(-.177160,.082861,1.381668),(-.303154,.082861,1.113931),(-.397649,.043488,.885566)]}
  for side,points in fitted.items():
   p=[native(v) for v in points];tip=p[2]+(p[2]-p[1]).normalized()*.14
   for suffix,a,b in zip(('Arm','ForeArm','Hand'),p,p[1:]+[tip]):
    n=side+suffix;old_dir=joints[n][1]-joints[n][0];rotation=old_dir.rotation_difference(b-a)@before[names[n]].to_quaternion()
    matrix=Matrix.LocRotScale(a,rotation,Vector((1,1,1)));rest_parent=worlds(g)[parent[names[n]]]
    local=rest_parent.inverted()@matrix;node=g['nodes'][names[n]];node['translation']=list(local.translation);node['rotation']=qrow(local.to_quaternion());node.pop('matrix',None)
    joints[n]=[a,b]
  rest=worlds(g);ibm=asset.read(skin['inverseBindMatrices'])
  mesh_node=next(i for i,n in enumerate(g['nodes']) if n.get('skin')==0 and 'mesh' in n);mesh_matrix=rest[mesh_node]
  for n in ARMS:
   matrix=rest[names[n]].inverted()@mesh_matrix;ibm[joint_index[n]]=[v for col in matrix.transposed() for v in col]
  skin['inverseBindMatrices']=asset.append(ibm,'MAT4')
 else:rest=worlds(g)
 weight_changes=[]
 if key=='kogoro':
  for mi,mesh in enumerate(g['meshes']):
   for pi,primitive in enumerate(mesh['primitives']):
    a=primitive['attributes'];positions=asset.read(a['POSITION']);weights=asset.read(a['WEIGHTS_0']);indices=asset.read(a['JOINTS_0'])
    for i,(position,ws,ids) in enumerate(zip(positions,weights,indices)):
     p=Vector(position);x,z=p.x,p.y;side='Left' if x>0 else 'Right'
     old_weights={g['nodes'][skin['joints'][idx]]['name']:w for idx,w in zip(ids,ws) if w>1e-7}
     amount=sum(w for n,w in old_weights.items() if n in ARMS)
     safe_hand=abs(x)>.33 and .68<z<.87
     if amount<1e-6 and not safe_hand:continue
     # Preserve body-side blend at the shoulder; replace only arm influences.
     other={n:w for n,w in old_weights.items() if n not in ARMS}
     if safe_hand:amount=1;other={}
     if abs(x)>.33 and z<.91:
      wrist=smooth(.855,.925,z);new={side+'Hand':1-wrist,side+'ForeArm':wrist}
     else:
      ds=sorted((distance(p,*joints[side+n]),side+n) for n in ('Arm','ForeArm','Hand'))[:2]
      values=[1/(d+.025)**5 for d,n in ds];total=sum(values);new={n:w/total for w,(_,n) in zip(values,ds)}
     final=dict(other)
     for n,w in new.items():final[n]=final.get(n,0)+w*amount
     final={n:w for n,w in sorted(final.items(),key=lambda item:-item[1])[:4] if w>1e-7};total=sum(final.values());final={n:w/total for n,w in final.items()}
     indices[i]=[joint_index[n] for n in final]+[0]*(4-len(final));weights[i]=list(final.values())+[0.]*(4-len(final))
     weight_changes.append({'primitive':[mi,pi],'index':i,'safe_hand_corrected_from_leg':safe_hand and any('Thigh' in n or 'Shin' in n for n in old_weights)})
    a['JOINTS_0']=asset.append(indices,'VEC4',asset.g['accessors'][a['JOINTS_0']]['componentType']);a['WEIGHTS_0']=asset.append(weights,'VEC4')
 # Smooth only the sewn sleeve/body transition. The original spatial classifier
 # creates one-edge jumps from Hips/Spine to ForeArm at the inner sleeve. Keep
 # actual legs/feet and arm interiors fixed, weld coincident UV vertices first.
 seam_changes=0
 for mesh in g['meshes']:
  for primitive in mesh['primitives']:
   a=primitive['attributes'];positions=asset.read(a['POSITION']);weights=asset.read(a['WEIGHTS_0']);indices=asset.read(a['JOINTS_0'])
   packed=asset.read(primitive['indices']);tri=[v[0] for v in packed]
   groups={};vkey=[]
   for i,p in enumerate(positions):
    k=tuple(round(v,5) for v in p);groups.setdefault(k,[]).append(i);vkey.append(k)
   adjacency={k:set() for k in groups};base={}
   for k,vs in groups.items():
    d={}
    for i in vs:
     for idx,w in zip(indices[i],weights[i]):
      if w>1e-7:d[idx]=d.get(idx,0)+w/len(vs)
    base[k]=d
   for j in range(0,len(tri),3):
    for i1,i2 in ((tri[j],tri[j+1]),(tri[j+1],tri[j+2]),(tri[j+2],tri[j])):
     k1,k2=vkey[i1],vkey[i2]
     if k1!=k2:adjacency[k1].add(k2);adjacency[k2].add(k1)
   def eligible(k):
    z=k[1];minimum=.43 if key=='conan' else .98
    return minimum<z<( .76 if key=='conan' else 1.46 ) and abs(k[0])>(.105 if key=='conan' else .17) and not any(('Thigh' in g['nodes'][skin['joints'][i]]['name'] or 'Shin' in g['nodes'][skin['joints'][i]]['name'] or 'Foot' in g['nodes'][skin['joints'][i]]['name']) and w>1e-7 for i,w in base[k].items())
   amount={k:sum(w for i,w in d.items() if g['nodes'][skin['joints'][i]]['name'] in ARMS) for k,d in base.items()}
   boundary={k for k in groups if eligible(k) and any(eligible(n) and abs(amount[k]-amount[n])>.48 for n in adjacency[k])}
   region=set(boundary)
   for _ in range(4):region|={n for k in region for n in adjacency[k] if eligible(n)}
   current=copy.deepcopy(base)
   for _ in range(14):
    nxt=dict(current)
    for k in region:
     neighbours=adjacency[k];summed={};total=0
     for n in neighbours:
      if any(('Thigh' in g['nodes'][skin['joints'][j]]['name'] or 'Shin' in g['nodes'][skin['joints'][j]]['name'] or 'Foot' in g['nodes'][skin['joints'][j]]['name']) and w>1e-7 for j,w in current[n].items()):continue
      d=math.dist(k,n);factor=1/max(d,.003);total+=factor
      for j,w in current[n].items():summed[j]=summed.get(j,0)+factor*w
     if not total:continue
     nxt[k]={j:.40*current[k].get(j,0)+.60*summed.get(j,0)/total for j in current[k].keys()|summed.keys()}
    current=nxt
   for k in region:
    d={j:w for j,w in sorted(current[k].items(),key=lambda x:-x[1])[:4] if w>1e-7};total=sum(d.values());d={j:w/total for j,w in d.items()}
    for i in groups[k]:
     indices[i]=list(d)+[0]*(4-len(d));weights[i]=list(d.values())+[0.]*(4-len(d));seam_changes+=1
   a['JOINTS_0']=asset.append(indices,'VEC4',asset.g['accessors'][a['JOINTS_0']]['componentType']);a['WEIGHTS_0']=asset.append(weights,'VEC4')
 # Generate anatomically forward elbow bends and contralateral swing.
 arm_samples={};edited=[]
 for ai,animation in enumerate(g.get('animations',[])):
  original_animation=old.g['animations'][ai];clip=animation['name'];duration=max(v[0] for s in original_animation['samplers'] for v in old.read(s['input']))
  relevant=[c for c in animation['channels'] if g['nodes'][c['target']['node']].get('name') in ARMS]
  all_times=sorted({v[0] for c in relevant for v in asset.read(animation['samplers'][c['sampler']]['input'])})
  poses={};arm_samples[clip]=[]
  for t in all_times:
   override=sample(old,original_animation,t)
   for n in ARMS:override[names[n]]=copy.deepcopy(g['nodes'][names[n]])
   chest_world=worlds(g,override)[names['Chest']];chest_delta=chest_world.to_quaternion()@rest[names['Chest']].to_quaternion().inverted()
   phase=t/max(duration,.001);row={'time':t,'hands':{}}
   for side,sg,offset in [('Left',1,0),('Right',-1,.5)]:
    cycle=(phase+offset)%1;swing=0.;bend=.13;splay=.18 if key=='conan' else .22
    if clip=='Walk':swing=-math.cos(cycle*math.tau)*.25;bend=.24+.035*math.cos(cycle*math.tau)
    elif clip=='Run':swing=-math.cos(cycle*math.tau)*.44;bend=1.02+.06*math.cos(cycle*math.tau)
    elif clip in ('Read','Sit'):swing=.08;bend=1.13;splay=.10
    elif clip=='Talk' and side=='Right':swing=.13+.035*math.sin(phase*math.tau);bend=.53+.08*math.sin(phase*math.tau)
    elif clip=='Wave' and side=='Right':swing=2.1;bend=-.35;splay=.50
    def direction(angle,lateral):return Vector((sg*lateral,-math.cos(angle),math.sin(angle))).normalized()
    desired={'Arm':direction(swing,splay),'ForeArm':direction(swing+bend,.08 if clip not in ('Read','Sit') else -.12),'Hand':direction(swing+bend-.035,.09 if clip not in ('Read','Sit') else -.14)}
    for suffix in ('Arm','ForeArm','Hand'):
     n=side+suffix;index=names[n];rest_dir=(joints[n][1]-joints[n][0]).normalized()
     world_q=chest_delta@rest_dir.rotation_difference(desired[suffix])@rest[index].to_quaternion()
     current=worlds(g,override);local_q=current[parent[index]].to_quaternion().inverted()@world_q
     override[index]['rotation']=qrow(local_q)
    current=worlds(g,override);row['hands'][side]=list(current[names[side+'Hand']].translation)
   poses[t]=override;arm_samples[clip].append(row)
  for channel in relevant:
   path=channel['target']['path'];node=channel['target']['node'];s=animation['samplers'][channel['sampler']];times=[v[0] for v in asset.read(s['input'])]
   # New pivots need matching constant translation tracks. Other channels retain bytes.
   if path=='rotation' or (key=='kogoro' and path=='translation'):
    rows=[poses[t][node].get(path,[0,0,0]) for t in times];s['output']=asset.append(rows,'VEC4' if path=='rotation' else 'VEC3');s['interpolation']='LINEAR';edited.append([clip,g['nodes'][node]['name'],path])
 # Exact preservation assertions include all legs, materials and mesh appearance.
 geometry_unchanged=True;unedited_tracks=0
 for old_mesh,new_mesh in zip(old.g['meshes'],g['meshes']):
  for op,np in zip(old_mesh['primitives'],new_mesh['primitives']):
   for a,idx in op['attributes'].items():
    if a not in ('JOINTS_0','WEIGHTS_0'):assert old.read(idx)==asset.read(np['attributes'][a]),a
   assert old.read(op['indices'])==asset.read(np['indices'])
 for oa,na in zip(old.g['animations'],g['animations']):
  for oc,nc in zip(oa['channels'],na['channels']):
   if old.g['nodes'][oc['target']['node']].get('name') not in ARMS:
    os=oa['samplers'][oc['sampler']];ns=na['samplers'][nc['sampler']];assert old.read(os['input'])==asset.read(ns['input']);assert old.read(os['output'])==asset.read(ns['output']);unedited_tracks+=1
 assert g.get('materials')==old.g.get('materials') and g.get('images')==old.g.get('images')
 target=B/(key+'.glb');asset.save(target);E.mkdir(parents=True,exist_ok=True)
 report={'character':key,'source_sha256':old.original_sha,'runtime_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'runtime_bytes':target.stat().st_size,'geometry_materials_uvs_indices_unchanged':True,'non_arm_animation_channels_preserved_exactly':unedited_tracks,'edited_channels':edited,'arm_weight_vertices_changed':len(weight_changes),'sleeve_transition_vertices_smoothed':seam_changes,'incorrect_hand_vertices_previously_bound_to_legs':sum(x['safe_hand_corrected_from_leg'] for x in weight_changes),'rest_arm_joints_gltf':{n:[list(a),list(b)] for n,(a,b) in joints.items()},'arm_samples':arm_samples,'scope':'Arm channels, local sewn sleeve/body weight transitions, and Kogoro arm pivots/skin only; leg positions/weights/curves unchanged except 40 mislabeled hand vertices corrected away from leg bones.'}
 (E/(key+'-arm-repair.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('ARM_REPAIR_READY',key,target,report['runtime_sha256'],report['runtime_bytes'],flush=True)

only=sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else ''
for key in ('conan','kogoro'):
 if not only or key==only:repair(key)
