"""Read-only checks of native/web collider topology and surgical original street edits."""
import sys,importlib.util,json,math,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'worlds/conan/blender/reference-2026-09';spec=importlib.util.spec_from_file_location('patch',Path(__file__).with_name('patch-street-context.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);GLB=p.GLB

def triangles(glb,pattern):
 result={}
 for n in glb.d['nodes']:
  if 'mesh' not in n or not pattern(n.get('name','')):continue
  assert not any(k in n for k in ['matrix','translation','scale','rotation']),n
  vv=[]
  for pr in glb.d['meshes'][n['mesh']]['primitives']:vs=glb.acc(pr['attributes']['POSITION']);ix=glb.acc(pr['indices']).reshape(-1,3);vv.extend(vs[ix])
  result[n['name']]=np.asarray(vv)
 return result

def canonical(tris):
 a=np.round(tris*1e5).astype(np.int64);ts=sorted(tuple(sorted(tuple(p) for p in t)) for t in a);return hashlib.sha256(repr(ts).encode()).hexdigest()
def ray_y(ts,x,z):
 a,b,c=ts[:,0],ts[:,1],ts[:,2];d=(b[:,2]-c[:,2])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,2]-c[:,2]);valid=np.abs(d)>1e-8;safe=np.where(valid,d,1)
 u=((b[:,2]-c[:,2])*(x-c[:,0])+(c[:,0]-b[:,0])*(z-c[:,2]))/safe;v=((c[:,2]-a[:,2])*(x-c[:,0])+(a[:,0]-c[:,0])*(z-c[:,2]))/safe;w=1-u-v;y=u*a[:,1]+v*b[:,1]+w*c[:,1];return y[valid&(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(y>-.55)&(y<.35)].tolist()
result={'collider_versions':[],'terrain_checks':[],'visual_detail_revision':[]}
for asset in ['agasa','street-block']:
 native=GLB(ROOT/f'worlds/conan/source/assets/buildings/{asset}.glb');web=GLB(ROOT/f'worlds/conan/web-project/assets/buildings/{asset}.glb');a=triangles(native,lambda n:'_Collision' in n);b=triangles(web,lambda n:'_Collision' in n);assert set(a)==set(b)
 for name in a:
  ha,hb=canonical(a[name]),canonical(b[name]);ok=ha==hb;result['collider_versions'].append({'asset':asset,'node':name,'native_triangles':len(a[name]),'web_triangles':len(b[name]),'same_triangles_at_1e-5m':ok});assert ok,(asset,name)
 # Newly added visual details must leave collider faces unchanged before final stage.
 latest=triangles(GLB(OUT/f'{asset}.glb'),lambda n:'_Collision' in n)
 for name in a:
  ok=canonical(a[name])==canonical(latest[name]);assert ok,(asset,name,'visual revision changed collider');result['visual_detail_revision'].append({'asset':asset,'node':name,'unchanged':ok})
for version in ['source','web-project']:
 current=GLB(ROOT/f'worlds/conan/{version}/assets/street.glb');old=GLB(OUT/f'originals/{version}-street.glb');ts=np.concatenate(list(triangles(current,lambda n:n in ['Terrain','Terrain_Collision']).values()));inside=[];outside=[]
 for r in [0,.5,1.0,1.6,2.10]:
  for i in range(12):
   x,z=64+r*math.cos(i*math.tau/12),-12.9+r*math.sin(i*math.tau/12);hit=ray_y(ts,x,z);inside.append({'p':[x,z],'hit':hit});assert len(hit)==0,(version,'hole blocked',x,z,hit)
 for i in range(12):
  x,z=64+2.30*math.cos(i*math.tau/12),-12.9+2.30*math.sin(i*math.tau/12);hit=ray_y(ts,x,z);outside.append({'p':[x,z],'hit':hit});assert len(hit)>0,(version,'ground outside hole missing',x,z)
 image_hashes=[]
 for i,im in enumerate(old.d.get('images',[])):
  if 'bufferView' not in im:continue
  bv=old.d['bufferViews'][im['bufferView']];cv=current.d['bufferViews'][current.d['images'][i]['bufferView']];a=old.b[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']];b=current.b[cv.get('byteOffset',0):cv.get('byteOffset',0)+cv['byteLength']];assert a==b;image_hashes.append(hashlib.sha256(a).hexdigest())
 dt=np.concatenate(list(triangles(current,lambda n:n.startswith('District')).values()));m=dt.mean(axis=1);left=((m[:,0]>=-.70)&(m[:,0]<=7.12)&(m[:,2]>=-12.92)&(m[:,2]<=-7.30)&(m[:,1]>=-.05)&(m[:,1]<=5.60)).sum();assert left==0
 result['terrain_checks'].append({'version':version,'inside_stair_hole_clear_rays':len(inside),'outside_ground_present_rays':len(outside),'embedded_image_sha256':image_hashes,'remaining_isolated_iroha_triangles':int(left)})
result['passed']=True;target=ROOT/'docs/evidence/conan-architecture/geometry-contract.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2));print('REFERENCE_GEOMETRY_CHECKS_PASSED',len(result['collider_versions']))
