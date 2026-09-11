"""Compare actual glTF data to prove only JumpAir changed between exports."""
from pathlib import Path
import json,struct,hashlib,sys
R=Path(__file__).resolve().parents[1]
def read(path):
 raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
 return json.loads(raw[20:20+length]),raw[28+length:],hashlib.sha256(raw).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def accessor(document,binary,index):
 a=document['accessors'][index];view=document['bufferViews'][a['bufferView']]
 element={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a['componentType']]*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 stride=view.get('byteStride',element);offset=view.get('byteOffset',0)+a.get('byteOffset',0)
 return sha(b''.join(binary[offset+i*stride:offset+i*stride+element] for i in range(a['count'])))
def summarize(document,binary):
 meshes=[]
 for mesh in document['meshes']:
  primitives=[]
  for p in mesh['primitives']:primitives.append({'attributes':{k:accessor(document,binary,v) for k,v in p['attributes'].items()},'indices':accessor(document,binary,p['indices'])})
  meshes.append(primitives)
 skins=[{'joints':[document['nodes'][i]['name'] for i in skin['joints']],'binds':accessor(document,binary,skin['inverseBindMatrices'])} for skin in document['skins']]
 images=[]
 for image in document['images']:
  v=document['bufferViews'][image['bufferView']];o=v.get('byteOffset',0);images.append(sha(binary[o:o+v['byteLength']]))
 actions={}
 for action in document['animations']:
  rows=[]
  for channel in action['channels']:
   sampler=action['samplers'][channel['sampler']]
   rows.append([document['nodes'][channel['target']['node']]['name'],channel['target']['path'],sampler.get('interpolation','LINEAR'),accessor(document,binary,sampler['input']),accessor(document,binary,sampler['output'])])
  actions[action['name']]=sorted(rows)
 return {'mesh_buffers':meshes,'skins':skins,'images':images,'materials':document['materials'],'nodes':document['nodes'],'animations':actions}
before=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/private/tmp/frog-before-jumpair-fix.glb')
after=R/'worlds/frog/source/assets/frog.glb'
old,oldbin,oldsha=read(before);new,newbin,newsha=read(after)
a=summarize(old,oldbin);b=summarize(new,newbin)
unchanged={key:a[key]==b[key] for key in ['mesh_buffers','skins','images','materials','nodes']}
clips={name:a['animations'][name]==b['animations'][name] for name in a['animations']}
report={'before_sha256':oldsha,'after_sha256':newsha,'bytes':after.stat().st_size,'unchanged_static_data':unchanged,'unchanged_clips':clips,'only_changed_clip':'JumpAir'}
assert all(unchanged.values()),report
assert all(same for name,same in clips.items() if name!='JumpAir') and not clips['JumpAir'],report
(R/'docs/evidence/character-motion/jumpair-only-change.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
