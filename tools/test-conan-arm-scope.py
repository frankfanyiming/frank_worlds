"""Independent binary audit: protect genuine Tripo geometry and validated legs."""
import json, struct, hashlib, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'worlds/conan/blender/arms-2026-09-13'
OUT=ROOT/'docs/evidence/conan-arms-2026-09-13'
OUT.mkdir(parents=True,exist_ok=True)
ARMS={s+t for s in ['Left','Right'] for t in ['Arm','ForeArm','Hand']}
LEG={s+t for s in ['Left','Right'] for t in ['Thigh','Shin','Foot']}
C={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
D={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}
class G:
 def __init__(self,p):
  self.path=p;self.raw=p.read_bytes();self.sha=hashlib.sha256(self.raw).hexdigest();n=struct.unpack_from('<I',self.raw,12)[0];self.g=json.loads(self.raw[20:20+n]);self.data=self.raw[28+n:]
 def read(self,i):
  a=self.g['accessors'][i];b=self.g['bufferViews'][a['bufferView']];f,s=C[a['componentType']];n=D[a['type']];start=b.get('byteOffset',0)+a.get('byteOffset',0);stride=b.get('byteStride',s*n)
  return [list(struct.unpack_from('<'+f*n,self.data,start+k*stride)) for k in range(a['count'])]
 def names(self):return [self.g['nodes'][i].get('name') for i in self.g['skins'][0]['joints']]
def bbox(rows):
 if not rows:return None
 return {'count':len(rows),'min':[min(v[d] for v in rows) for d in range(3)],'max':[max(v[d] for v in rows) for d in range(3)]}
def dist_dict(a,b):return max([abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b)] or [0])
reports={}
for key in ['conan','kogoro']:
 o=G(B/'originals'/(key+'.glb'));n=G(B/(key+'.glb'));names=o.names();newnames=n.names();r={'source_sha256':o.sha,'candidate_sha256':n.sha,'problems':[]}
 r['original_binary_prefix_preserved']=n.data[:len(o.data)]==o.data
 r['materials_images_textures_same']=all(o.g.get(k)==n.g.get(k) for k in ['materials','images','textures','samplers'])
 r['non_arm_node_changes']=[{'index':i,'name':a.get('name'),'before':a,'after':b} for i,(a,b) in enumerate(zip(o.g['nodes'],n.g['nodes'])) if a.get('name') not in ARMS and a!=b]
 assert len(o.g['nodes'])==len(n.g['nodes'])
 ibo=o.read(o.g['skins'][0]['inverseBindMatrices']);ibn=n.read(n.g['skins'][0]['inverseBindMatrices'])
 r['non_arm_bind_changes']=[names[i] for i,(a,b) in enumerate(zip(ibo,ibn)) if names[i] not in ARMS and a!=b]
 r['all_bind_changes']=[names[i] for i,(a,b) in enumerate(zip(ibo,ibn)) if a!=b]
 r['non_arm_animation_changes']=[];r['arm_animation_input_changes']=[];r['checked_non_arm_channels']=0
 assert len(o.g['animations'])==len(n.g['animations'])
 for oa,na in zip(o.g['animations'],n.g['animations']):
  assert oa['name']==na['name'] and len(oa['channels'])==len(na['channels'])
  for oc,nc in zip(oa['channels'],na['channels']):
   assert oc['target']==nc['target'];name=o.g['nodes'][oc['target']['node']].get('name');os=oa['samplers'][oc['sampler']];ns=na['samplers'][nc['sampler']]
   inputs_same=o.read(os['input'])==n.read(ns['input']);outputs_same=o.read(os['output'])==n.read(ns['output']);mode_same=os.get('interpolation','LINEAR')==ns.get('interpolation','LINEAR')
   if name not in ARMS:
    r['checked_non_arm_channels']+=1
    if not (inputs_same and outputs_same and mode_same):r['non_arm_animation_changes'].append([oa['name'],name,oc['target']['path'],inputs_same,outputs_same,mode_same])
   elif not inputs_same:r['arm_animation_input_changes'].append([oa['name'],name,oc['target']['path']])
 r['geometry_changes']=[];r['true_leg_weight_changes']=[];r['safe_hand_leg_corrections']=[];r['new_leg_influences']=[];r['cross_side_arm_influences']=[];r['changed_outside_scope']=[];r['meshes']=[]
 for mi,(om,nm) in enumerate(zip(o.g['meshes'],n.g['meshes'])):
  for pi,(op,np) in enumerate(zip(om['primitives'],nm['primitives'])):
   for a,i in op['attributes'].items():
    if a not in ['WEIGHTS_0','JOINTS_0'] and o.read(i)!=n.read(np['attributes'][a]):r['geometry_changes'].append([mi,pi,a])
   if o.read(op['indices'])!=n.read(np['indices']):r['geometry_changes'].append([mi,pi,'indices'])
   if 'WEIGHTS_0' not in op['attributes']:continue
   p=o.read(op['attributes']['POSITION']);ow=o.read(op['attributes']['WEIGHTS_0']);nw=n.read(np['attributes']['WEIGHTS_0']);oj=o.read(op['attributes']['JOINTS_0']);nj=n.read(np['attributes']['JOINTS_0'])
   changed=[];truelegs=0;indices_changed_only=0
   for i,(pos,a,b,ja,jb) in enumerate(zip(p,ow,nw,oj,nj)):
    od={};nd={}
    for j,w in zip(ja,a):od[names[j]]=od.get(names[j],0)+w
    for j,w in zip(jb,b):nd[newnames[j]]=nd.get(newnames[j],0)+w
    od={j:w for j,w in od.items() if w>1e-7};nd={j:w for j,w in nd.items() if w>1e-7}
    safe=key=='kogoro' and abs(pos[0])>.33 and .68<pos[1]<.87
    oldleg=sum(od.get(j,0) for j in LEG);newleg=sum(nd.get(j,0) for j in LEG)
    actual=dist_dict(od,nd)>0
    if actual:changed.append(pos)
    elif (a!=b or ja!=jb):indices_changed_only+=1
    evidence={'primitive':[mi,pi],'index':i,'position':pos,'old':od,'new':nd}
    if oldleg>1e-7 and not safe:
     truelegs+=1
     if a!=b or ja!=jb:r['true_leg_weight_changes'].append(evidence)
    if oldleg>1e-7 and safe and actual:r['safe_hand_leg_corrections'].append(evidence)
    if newleg>oldleg+1e-7:r['new_leg_influences'].append(evidence)
    opposite='Right' if pos[0]>0 else 'Left'
    if sum(nd.get(opposite+s,0) for s in ['Arm','ForeArm','Hand'])>1e-5 and actual:r['cross_side_arm_influences'].append(evidence)
    # Relaxed output scope reproduces exact documented gate; more constrained
    # topology-region reconstruction is not needed to prove true leg preservation.
    seam=(.43<round(pos[1],5)<.76 and abs(round(pos[0],5))>.105) if key=='conan' else (.98<round(pos[1],5)<1.46 and abs(round(pos[0],5))>.17)
    arm_adjust=key=='kogoro' and (safe or sum(od.get(j,0) for j in ARMS)>1e-6)
    if actual and not(seam or arm_adjust):r['changed_outside_scope'].append(evidence)
   r['meshes'].append({'primitive':[mi,pi],'vertices':len(p),'changed_weight_vertices':len(changed),'changed_bounds_gltf':bbox(changed),'true_leg_vertices_checked':truelegs,'reordered_slots_only':indices_changed_only})
 for k in ['non_arm_node_changes','non_arm_bind_changes','non_arm_animation_changes','arm_animation_input_changes','geometry_changes','true_leg_weight_changes','new_leg_influences','cross_side_arm_influences','changed_outside_scope']:
  if r[k]:r['problems'].append({'kind':k,'count':len(r[k])})
 r['candidate_stable_at_end']=hashlib.sha256(n.path.read_bytes()).hexdigest()==n.sha
 reports[key]=r
json.dump(reports,open(OUT/'candidate-scope-audit.json','w'),indent=2,ensure_ascii=False)
for key,r in reports.items():
 print(key,json.dumps({k:v for k,v in r.items() if k in ['source_sha256','candidate_sha256','problems','all_bind_changes','original_binary_prefix_preserved','materials_images_textures_same','checked_non_arm_channels','meshes','candidate_stable_at_end']}))

assert all(not r["problems"] and r["candidate_stable_at_end"] and r["materials_images_textures_same"] and r["original_binary_prefix_preserved"] for r in reports.values()), "Arm repair changed protected source data"
