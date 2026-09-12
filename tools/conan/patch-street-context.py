"""Surgical edits of original Blender GLB triangle buffers; all unrelated bytes/resources preserved.
Removes the obsolete isolated Iroha, plants inside enlarged Agasa footprint, and cuts a real spiral stair opening.
Only runtime/source assets are patched; original backups live under blender/reference-2026-09/originals.
"""
import json,struct,math,hashlib,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'worlds/conan/blender/reference-2026-09';BACK=OUT/'originals';BACK.mkdir(parents=True,exist_ok=True)
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};DIMS={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1}
class GLB:
 def __init__(self,path):
  b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];self.d=json.loads(b[20:20+n]);self.b=bytearray(b[28+n:]);self.before_sha=hashlib.sha256(b).hexdigest()
 def acc(self,i):
  a=self.d['accessors'][i];v=self.d['bufferViews'][a['bufferView']];dt=DT[a['componentType']];dim=DIMS[a['type']];return np.ndarray((a['count'],dim),dtype=dt,buffer=self.b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*dim),np.dtype(dt).itemsize)).copy()
 def add(self,arr,typ,component=5126):
  arr=np.asarray(arr,dtype=DT[component]);pad=(-len(self.b))%4;self.b.extend(b'\0'*pad);view=len(self.d['bufferViews']);self.d['bufferViews'].append({'buffer':0,'byteOffset':len(self.b),'byteLength':arr.nbytes});self.b.extend(arr.tobytes());idx=len(self.d['accessors']);a={'bufferView':view,'componentType':component,'count':len(arr),'type':typ}
  if typ=='VEC3':a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
  self.d['accessors'].append(a);return idx
 def save(self,path):
  self.b.extend(b'\0'*((-len(self.b))%4));self.d['buffers'][0]['byteLength']=len(self.b);j=json.dumps(self.d,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);data=struct.pack('<III',0x46546c67,2,28+len(j)+len(self.b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(self.b),0x004e4942)+self.b;Path(path).write_bytes(data);return hashlib.sha256(data).hexdigest()

# Convex polygon subtraction partitions a triangle into outside polygons without touching outside vertices.
def side(p,a,b):return (b[0]-a[0])*(p[2]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def split(poly,a,b):
 inside=[];outside=[]
 for i,P in enumerate(poly):
  Q=poly[(i+1)%len(poly)];dp,dq=side(P,a,b),side(Q,a,b)
  (inside if dp>=-1e-8 else outside).append(P)
  if (dp>1e-8 and dq<-1e-8) or (dp<-1e-8 and dq>1e-8):
   R=P+(Q-P)*dp/(dp-dq);inside.append(R);outside.append(R)
 return inside,outside

def process(version):
 target=ROOT/f'worlds/conan/{version}/assets/street.glb';backup=BACK/f'{version}-street.glb'
 if not backup.exists():shutil.copy2(target,backup)
 glb=GLB(backup);d=glb.d;changes=[];orig_nodes=json.dumps(d['nodes'],sort_keys=True);orig_images=json.dumps(d.get('images'),sort_keys=True);newtris=0
 for nd in d['nodes']:
  name=nd.get('name','')
  if name not in ['District','District_Collision','District_Glass','Garden_details','Terrain','Terrain_Collision']:continue
  for pi,pr in enumerate(d['meshes'][nd['mesh']]['primitives']):
   vs=glb.acc(pr['attributes']['POSITION']);ix=glb.acc(pr['indices']).reshape(-1,3);tri=vs[ix];mid=tri.mean(axis=1);keep=np.ones(len(ix),dtype=bool)
   if name.startswith('District'):
    # Original Blender facade('いろは寿し',3.2,-10,7,4.6,3.2): bounds include small roof overhang.
    drop=(mid[:,0]>=-.70)&(mid[:,0]<=7.12)&(mid[:,2]>=-12.92)&(mid[:,2]<=-7.30)&(mid[:,1]>=-.05)&(mid[:,1]<=5.60)
    # Face selection must not slice any connected component's crossing triangle.
    keep&=~drop
   elif name=='Garden_details':
    keep&=~((mid[:,0]>=55)&(mid[:,0]<=73)&(mid[:,2]>=-16)&(mid[:,2]<=2.0))
   if not keep.all():
    n=int((~keep).sum());changes.append({'node':name,'primitive':pi,'material':d['materials'][pr['material']]['name'],'operation':'remove obsolete isolated Iroha' if name.startswith('District') else 'remove former Agasa plants and table-top remnants inside enlarged house','removed_triangles':n,'removed_bounds':[tri[~keep].min(axis=(0,1)).tolist(),tri[~keep].max(axis=(0,1)).tolist()]});pr['indices']=glb.add(ix[keep].reshape(-1,1),'SCALAR',5125)
   if name not in ['Terrain','Terrain_Collision']:continue
   # Stair opening center in final shared world coordinates, 64-sided circle radius2.18m.
   cx,cz,r=64,-12.9,2.18;circle=[(cx+r*math.cos(i*math.tau/64),cz+r*math.sin(i*math.tau/64)) for i in range(64)]
   candidate=(tri[:,:,0].max(axis=1)>cx-r)&(tri[:,:,0].min(axis=1)<cx+r)&(tri[:,:,2].max(axis=1)>cz-r)&(tri[:,:,2].min(axis=1)<cz+r)&(tri[:,:,1].max(axis=1)>-.5)&(tri[:,:,1].min(axis=1)<.3)
   if not candidate.any():continue
   attrs={k:glb.acc(v) for k,v in pr['attributes'].items()};keys=list(attrs);slices={};cursor=0
   for k in keys:slices[k]=slice(cursor,cursor+attrs[k].shape[1]);cursor+=attrs[k].shape[1]
   # POSITION must occupy first3 to evaluate cut plane; enforce explicit reordering.
   keys=['POSITION']+[k for k in keys if k!='POSITION'];cursor=0
   for k in keys:slices[k]=slice(cursor,cursor+attrs[k].shape[1]);cursor+=attrs[k].shape[1]
   packed=np.concatenate([attrs[k] for k in keys],axis=1);out=[];count=0
   for idx in np.where(candidate)[0]:
    pending=[p.copy() for p in packed[ix[idx]]];outside=[]
    for a,b in zip(circle,circle[1:]+circle[:1]):
     if len(pending)<3:break
     pending,part=split(pending,a,b)
     if len(part)>=3:outside.append(part)
    for poly in outside:
     for j in range(1,len(poly)-1):
      t=np.array([poly[0],poly[j],poly[j+1]])
      if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-8:out.extend(t)
    count+=1
   if not out:continue
   extra=np.array(out);newpos=[]
   for k in keys:
    arr=np.concatenate([attrs[k],extra[:,slices[k]]])
    if k=='NORMAL':arr/=np.maximum(np.linalg.norm(arr,axis=1,keepdims=True),1e-9)
    typ=d['accessors'][pr['attributes'][k]]['type'];component=d['accessors'][pr['attributes'][k]]['componentType'];pr['attributes'][k]=glb.add(arr,typ,component)
   newix=np.concatenate([ix[~candidate],np.arange(len(vs),len(vs)+len(extra)).reshape(-1,3)]);pr['indices']=glb.add(newix.reshape(-1,1),'SCALAR',5125);changes.append({'node':name,'primitive':pi,'operation':'64-sided true spiral stair hole','center':[cx,0,cz],'radius':r,'replaced_triangles':int(candidate.sum()),'new_triangles':len(extra)//3});newtris+=len(extra)//3
  # glTF primitives must contain at least one indexed triangle.
  mi=nd['mesh'];d['meshes'][mi]['primitives']=[p for p in d['meshes'][mi]['primitives'] if d['accessors'][p['indices']]['count']>0]
 assert json.dumps(d['nodes'],sort_keys=True)==orig_nodes
 assert json.dumps(d.get('images'),sort_keys=True)==orig_images
 sha=glb.save(target);report={'version':version,'original_sha256':glb.before_sha,'patched_sha256':sha,'original_path':str(backup.relative_to(ROOT)),'node_transforms_unchanged':True,'embedded_images_unchanged':True,'car_assets_untouched':True,'changes':changes}
 (OUT/f'{version}-street-patch-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(version,sha,changes,flush=True)
if __name__=='__main__':
 for version in ['web-project','source']:process(version)
