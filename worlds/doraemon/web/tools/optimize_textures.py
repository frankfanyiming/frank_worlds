"""Resize embedded glTF textures in place, preserving geometry/rigs and buffer alignment."""
from PIL import Image
from pathlib import Path
import json,struct,io,sys
root=Path(sys.argv[1]);report=[]
for path in sorted(root.rglob('*.glb')):
 blob=path.read_bytes();n=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+n]);binary=blob[28+n:];images={i['bufferView']:i for i in doc.get('images',[]) if 'bufferView' in i};chunks=[];offset=0
 for idx,v in enumerate(doc.get('bufferViews',[])):
  data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
  if idx in images:
   im=Image.open(io.BytesIO(data));im.thumbnail((512,512),Image.Resampling.LANCZOS);buf=io.BytesIO()
   alpha='A' in im.getbands() and im.getextrema()[-1][0]<255
   if alpha:im.save(buf,format='PNG',optimize=True);mime='image/png'
   else:im.convert('RGB').save(buf,format='JPEG',quality=82,optimize=True);mime='image/jpeg'
   data=buf.getvalue();images[idx]['mimeType']=mime
  v['byteOffset']=offset;v['byteLength']=len(data);chunks.append(data+b'\0'*((-len(data))%4));offset+=len(chunks[-1])
 doc['buffers']=[{'byteLength':offset}];doc['asset']['generator']=doc['asset'].get('generator','')+'; frank_worlds web textures 512px'
 binary=b''.join(chunks);j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4)
 result=struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
 path.write_bytes(result);report.append({'asset':str(path.relative_to(root)),'before':len(blob),'after':len(result)})
print(json.dumps(report,indent=2))
