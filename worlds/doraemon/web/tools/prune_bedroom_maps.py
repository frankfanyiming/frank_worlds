"""Remove only unreachable/overridden GLB image payloads; never edit pixels.
The replacement textures are separate files, preserving their exact bytes.
"""
import json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def prune(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
 manifest=json.loads((ROOT/'public/bedroom-materials/manifest.json').read_text());mapped={x for v in manifest['materials'].values()for x in v['replace_source_materials']}
 for mat in doc['materials']:
  name=mat['name'];scan=name in ['V10_Plaster','Plaster','WashiUV','V10_GreenLinen','V10_BlueLinen','V10_Canvas','V10_Cedar','V10_Tatami','V10_Desktop','V10_Drawer','Timber.001','F7_Wood'] or any(x in name.lower()for x in ['walnut','oak'])
  if not scan and name not in mapped:continue
  p=mat.get('pbrMetallicRoughness',{})
  if name in mapped or name!='V10_Canvas':p.pop('baseColorTexture',None)
  p.pop('metallicRoughnessTexture',None);mat.pop('normalTexture',None);mat.pop('occlusionTexture',None)
 refs=[]
 def visit(value):
  if isinstance(value,dict):
   for key,v in value.items():
    if key.endswith('Texture') and isinstance(v,dict) and 'index'in v:refs.append(v)
    else:visit(v)
  elif isinstance(value,list):
   for v in value:visit(v)
 visit(doc['materials']);indices=sorted({v['index']for v in refs});lookup={old:new for new,old in enumerate(indices)}
 for ref in refs:ref['index']=lookup[ref['index']]
 doc['textures']=[doc['textures'][i]for i in indices];indices=sorted({t['source']for t in doc['textures']});lookup={old:new for new,old in enumerate(indices)}
 for texture in doc['textures']:texture['source']=lookup[texture['source']]
 doc['images']=[doc['images'][i]for i in indices]
 refs=[]
 def views(value):
  if isinstance(value,dict):
   for k,v in value.items():
    if k=='bufferView':refs.append(value)
    else:views(v)
  elif isinstance(value,list):
   for v in value:views(v)
 views(doc);indices=sorted({r['bufferView']for r in refs});lookup={old:new for new,old in enumerate(indices)};chunks=[];offset=0;newviews=[]
 for i in indices:
  v=doc['bufferViews'][i].copy();chunk=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];v['byteOffset']=offset;chunk+=b'\0'*((-len(chunk))%4);chunks.append(chunk);offset+=len(chunk);newviews.append(v)
 for ref in refs:ref['bufferView']=lookup[ref['bufferView']]
 doc['bufferViews']=newviews;doc['buffers'][0]['byteLength']=offset
 raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob=b''.join(chunks);result=struct.pack('<III',0x46546c67,2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob;path.write_bytes(result);print('Removed duplicated maps:',len(data),'->',len(result))
if __name__=='__main__':prune(ROOT/'public/models/bedroom-v12.glb')
