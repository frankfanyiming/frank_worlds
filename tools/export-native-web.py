#!/usr/bin/env python3
"""Export an installed native world with Godot 4.7.2 and package verified chunks."""
from pathlib import Path
import argparse,gzip,hashlib,json,re,struct,subprocess
from configure_conan_import import configure_conan_import

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('world',choices=['frog','conan'])
parser.add_argument('output',type=Path,help='Dedicated output directory for this world')
parser.add_argument('--godot',default='godot',help='Godot 4.7.2 executable')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
project=root/'worlds'/args.world/('source' if args.world=='frog' else 'web-project')
if not (project/'ui-font.otf').exists():
 raise SystemExit('Install assets first: tools/fetch-native-assets.py '+('frog' if args.world=='frog' else 'conan-web'))
output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
subprocess.run([args.godot,'--headless','--path',str(project),'--editor','--import'],check=True)
if args.world=='conan' and configure_conan_import(project,args.godot):
 # Fresh runtime archives may have no .import sidecars. Configure after the
 # first import, then reimport only when the embedded-map/key settings changed.
 subprocess.run([args.godot,'--headless','--path',str(project),'--editor','--import'],check=True)
# Baked rooms contain the same geometry with UV2 and share the extracted images.
# Keep original GLBs locally, and preserve the non-baked fallback for developers.
# Only exclude their duplicate runtime copies when both replacement scenes exist.
preset_path=project/'export_presets.cfg'
preset_original=preset_path.read_text()
preset_export=preset_original
if args.world=='frog' and all((project/'assets/house-lighting'/f'{name}-room.scn').exists() for name in ('frog','panda')):
 duplicates='assets/home-enclosure.glb,assets/home-furnishings.glb,assets/panda-home.glb'
 preset_export,count=re.subn(r'^exclude_filter="([^"]*)"$',lambda m:'exclude_filter="'+m.group(1)+','+duplicates+'"',preset_original,count=1,flags=re.M)
 if count!=1:raise SystemExit('Cannot safely apply baked-room export exclusions.')
if args.world=='conan':
 # The repaired Kogoro retains the original maps inside its GLB. all_resources
 # otherwise includes the old extracted JPGs a second time. Keep source files;
 # exclude only these exact legacy maps after checking installed references.
 legacy=[p for p in (project/'assets').glob('kogoro_*_efc231ac-2159-4fe1-9eab-8c3db4e88534.jpg')
         if p.name.split('_')[1] in ('Color','NormalGL','ORM')]
 def glb_json(path):
  with path.open('rb') as f:
   header=f.read(20)
   if len(header)!=20 or header[:4]!=b'glTF':raise ValueError('Not a GLB: '+str(path))
   return json.loads(f.read(struct.unpack_from('<I',header,12)[0]))
 embedded=all('bufferView' in im and 'uri' not in im for im in glb_json(project/'assets/kogoro.glb').get('images',[]))
 names={p.name for p in legacy}
 referenced=any(any(name in str(im.get('uri','')) for name in names)
                for path in (project/'assets').rglob('*.glb') for im in glb_json(path).get('images',[]))
 for path in project.rglob('*'):
  if path.suffix in ('.gd','.gdshader','.tscn','.tres','.json') and '.godot' not in path.parts:
   if any(name in path.read_text(errors='replace') for name in names):referenced=True
 if legacy and embedded and not referenced:
  duplicates=','.join(str(p.relative_to(project)) for p in sorted(legacy))
  preset_export,count=re.subn(r'^exclude_filter="([^"]*)"$',lambda m:'exclude_filter="'+m.group(1)+','+duplicates+'"',preset_export,count=1,flags=re.M)
  if count!=1:raise SystemExit('Cannot safely exclude duplicate embedded textures.')
  print('EXPORT_ONLY_LEGACY_TEXTURE_EXCLUSIONS '+duplicates)
try:
 if preset_export!=preset_original:preset_path.write_text(preset_export)
 subprocess.run([args.godot,'--headless','--path',str(project),'--export-release','Web',str(output/'index.html')],check=True)
finally:
 if preset_export!=preset_original and preset_path.read_text()==preset_export:preset_path.write_text(preset_original)
html=(output/'index.html').read_text()
match=re.search(r'const GODOT_CONFIG = (\{.*?\});',html)
if not match:raise SystemExit('Unsupported Godot export shell; generated files were preserved.')
config=json.loads(match.group(1));source=output/'index.pck';raw=source.read_bytes();chunks=[]
for i,start in enumerate(range(0,len(raw),16*1024*1024)):
 data=raw[start:start+16*1024*1024]
 encoded=gzip.compress(data,compresslevel=8,mtime=0)
 name=f'world-{i:03}.bin.gz';(output/name).write_bytes(encoded)
 chunks.append(dict(file=name,offset=start,rawBytes=len(data),bytes=len(encoded),sha256=hashlib.sha256(data).hexdigest()))
for stale in output.glob('world-*.bin.gz'):
 if stale.name not in {c['file'] for c in chunks}:stale.unlink()
(output/'world-pack.json').write_text(json.dumps(dict(totalBytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),chunks=chunks),indent=2)+'\n')
shell=(root/'tools/native-world-shell.html').read_text()
shell=shell.replace('CONFIG_JSON',json.dumps(config)).replace('NATIVE_LOADER_JS',(root/'tools/native-loader.js').read_text()).replace('JUMP_BUTTON','<button data-action="jump" aria-label="Jump">↑</button>' if args.world=='frog' else '')
(output/'index.html').write_text(shell)
# This pack was generated by the export above; the checked source project remains intact.
source.unlink()
(output/'OFL.txt').write_bytes((project/'OFL.txt').read_bytes())
(output/'FONT-SOURCE.md').write_bytes((project/'FONT-SOURCE.md').read_bytes())
print(json.dumps(dict(world=args.world,directory=str(output),downloadBytes=sum(c['bytes'] for c in chunks),chunks=len(chunks))))
