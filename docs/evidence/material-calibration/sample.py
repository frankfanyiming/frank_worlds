"""Read rendered PNGs and the exported GLB; never color-convert the evidence."""
from pathlib import Path
import json, struct, io
from PIL import Image, ImageStat
out=Path(__file__).resolve().parent
experiment=json.loads((out/'experiment.json').read_text());result={}
for name in ['01-original-principled.png','02-original-emission.png','03-glb-roundtrip-principled.png']:
 im=Image.open(out/name);stats=[]
 for patch in experiment['patches']:
  x=patch['render_sample_x'];s=ImageStat.Stat(im.crop((x-24,104,x+24,152)))
  stats.append({'name':patch['name'],'mean_rgb':s.mean[:3],'minmax_rgb':s.extrema[:3]})
 result[name]=stats
raw=(out/'calibration.glb').read_bytes();length=struct.unpack_from('<I',raw,12)[0]
gltf=json.loads(raw[20:20+length]);binary_start=28+length
result['glb_materials']=gltf['materials'];result['embedded_images']=[]
for item in gltf['images']:
 view=gltf['bufferViews'][item['bufferView']];start=binary_start+view.get('byteOffset',0)
 embedded=raw[start:start+view['byteLength']];im=Image.open(io.BytesIO(embedded));name=item.get('name','image')
 (out/(name+'.png')).write_bytes(embedded)
 result['embedded_images'].append({'name':name,'mode':im.mode,'center_pixel':im.getpixel((4,4))})
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
