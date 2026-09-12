"""Surgical facade fix: preserve geometry/images except old lettering indices.

The accompanying Blender-authored mouri-details.glb supplies the bold signs.
Rebuilding from saved originals makes repeated execution idempotent.
"""
import json,struct,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'worlds/conan/blender/reference-2026-09'
BACK=OUT/'originals/facade-release20';BACK.mkdir(parents=True,exist_ok=True)
def rgb(h):
 def f(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
 return [f(int(h[i:i+2],16)/255)for i in [0,2,4]]
def read(p):
 b=p.read_bytes();l=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+l]);return j,bytearray(b[l+28:])
def accessor(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC3':3}[a['type']];f={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];size=struct.calcsize('<'+f*n);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from('<'+f*n,b,offset+k*v.get('byteStride',size))for k in range(a['count'])]
def write(p,j,b):
 j['buffers'][0]['byteLength']=len(b);js=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();js+=b' '*((-len(js))%4);b+=b'\0'*((-len(b))%4)
 p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
def mesh_digest(j,b,collision_only=False):
 h=hashlib.sha256()
 for m in j['meshes']:
  if collision_only and '_Collision'not in m.get('name',''):continue
  for p in m['primitives']:
   for ai in list(p['attributes'].values())+[p['indices']]:
    a=j['accessors'][ai];v=j['bufferViews'][a['bufferView']];h.update(bytes(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]))
 return h.hexdigest()
reports=[]
for variant in ['source','web-project']:
 target=ROOT/f'worlds/conan/{variant}/assets/buildings/mouri.glb';original=BACK/(variant+'-mouri.glb')
 if not original.exists():shutil.copy2(target,original)
 j,b=read(original);collision_before=mesh_digest(j,b,True);image_before=[hashlib.sha256(bytes(b[j['bufferViews'][i['bufferView']].get('byteOffset',0):j['bufferViews'][i['bufferView']].get('byteOffset',0)+j['bufferViews'][i['bufferView']]['byteLength']])).hexdigest()for i in j.get('images',[]) if 'bufferView'in i]
 changed=[]
 for m in j['materials']:
  if m.get('name','').startswith('M_Exterior_warm_stucco'):
   m['name']='Mouri reference pale blue facade';pbr=m['pbrMetallicRoughness'];pbr.pop('baseColorTexture',None);pbr['baseColorFactor']=rgb('acb9c9')+[1];pbr['roughnessFactor']=.88
   if 'normalTexture'in m:m['normalTexture']['scale']=.14
   changed.append('Pale gray-blue stucco replaces the baked orange albedo; normal and roughness images preserved.')
 removed=0
 for m in j['meshes']:
  if m.get('name')!='Facade_Detail':continue
  for p in m['primitives']:
   name=j['materials'][p.get('material',0)]['name'];pos=accessor(j,b,p['attributes']['POSITION']);idx=[x[0]for x in accessor(j,b,p['indices'])];keep=[]
   for k in range(0,len(idx),3):
    vv=[pos[i]for i in idx[k:k+3]]
    horizontal=name.startswith('M_Cream_painted_wood') and all(-4.3<v[0]<.2 and 4.45<v[1]<5.20 and .080<v[2]<.096 for v in vv)
    vertical=name.startswith('M_Ink') and all(-4.70<v[0]<-4.30 and 4.0<v[1]<6.35 and .54<v[2]<.58 for v in vv)
    cafe=name.startswith(('M_Poirot_Deep_red_canvas','M_Brass_aged')) and all(-2.8<v[0]<1.15 and 1.1<v[1]<2.5 and .092<v[2]<.097 for v in vv)
    if horizontal or vertical or cafe:removed+=1
    else:keep.extend(idx[k:k+3])
   if len(keep)==len(idx):continue
   # Keep an empty primitive legal by removing it after this pass.
   if not keep:p['_remove']=True;continue
   b+=b'\0'*((-len(b))%4);start=len(b);packed=struct.pack('<'+'I'*len(keep),*keep);b+=packed
   vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(packed),'target':34963})
   ai=len(j['accessors']);j['accessors'].append({'bufferView':vi,'componentType':5125,'count':len(keep),'type':'SCALAR','min':[min(keep)],'max':[max(keep)]});p['indices']=ai
  m['primitives']=[p for p in m['primitives']if not p.pop('_remove',False)]
 assert 500<removed<90000,(variant,removed)
 assert collision_before==mesh_digest(j,b,True),'Facade patch changed physical colliders'
 image_after=[hashlib.sha256(bytes(b[j['bufferViews'][i['bufferView']].get('byteOffset',0):j['bufferViews'][i['bufferView']].get('byteOffset',0)+j['bufferViews'][i['bufferView']]['byteLength']])).hexdigest()for i in j.get('images',[]) if 'bufferView'in i]
 assert image_before==image_after,'Facade patch changed embedded image buffers'
 write(target,j,b)
 reports.append({'variant':variant,'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'removed_old_lettering_triangles':removed,'collision_sha256':collision_before,'embedded_images_preserved':len(image_before),'changes':changed})
(OUT/'mouri-facade-2026-09-13.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2));print(json.dumps(reports,ensure_ascii=False,indent=2))
