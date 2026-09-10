"""Copy the accepted room's texture bytes and provenance unchanged.
Usage: python3 tools/copy_bedroom_materials.py /path/to/Godot/project/assets
"""
import sys,json,shutil,hashlib
from pathlib import Path
src=Path(sys.argv[1]);out=Path(__file__).resolve().parents[1]/'public/bedroom-materials';out.mkdir(parents=True,exist_ok=True)
pbr=json.loads((src/'refinement/pbr/manifest.json').read_text());families=['painted_plaster_wall','fine_grained_wood','japanese_cedar_planks','rough_linen','tatami_mat','oak_veneer_02']
manifest={'scans':{},'materials':{},'license':pbr['license']}
for key in families:
 item=pbr['assets'][key];manifest['scans'][key]=item
 for channel,m in item['maps'].items():
  if key=='rough_linen' and channel=='albedo':continue
  dest=out/m['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src/'refinement/pbr'/m['file'],dest)
source_materials=json.loads((src/'materials/manifest.json').read_text())['materials']
for key,item in source_materials.items():
 manifest['materials'][key]=item
 for m in item['maps'].values():shutil.copyfile(src/'materials'/m['file'],out/m['file'])
manifest['files']=[{'file':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in out.rglob('*')if p.is_file() and p.name!='manifest.json']
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(len(manifest['files']),sum(x['bytes']for x in manifest['files'])/1e6)
