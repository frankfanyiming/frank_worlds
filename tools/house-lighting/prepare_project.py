"""Create a reproducible, isolated Godot lightmap bake project; never edit source assets."""
import argparse,re,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Output must be a new directory to avoid stale cached bakes')
a.output.mkdir(parents=True);assets=a.output/'assets';assets.mkdir();(assets/'house-lighting').mkdir();(a.output/'baseline').mkdir();(a.output/'geometry-dumps').mkdir()
for name in ['home-enclosure','home-furnishings','panda-home','frog','panda']:
 shutil.copy2(a.source/'assets'/f'{name}.glb',assets/f'{name}.glb')
 imp=a.source/'assets'/f'{name}.glb.import'
 if imp.exists():
  text=imp.read_text()
  if name in ['home-enclosure','home-furnishings','panda-home']:
   match=re.search(r'^path="res://([^"]+)"',text,re.M)
   if match and (a.source/match[1]).exists():shutil.copy2(a.source/match[1],a.output/'baseline'/f'{name}.scn')
  if name in ['home-enclosure','home-furnishings','panda-home']:
   text=re.sub(r'meshes/light_baking=\d+','meshes/light_baking=2',text)
   text=re.sub(r'meshes/lightmap_texel_size=[\d.]+','meshes/lightmap_texel_size=0.1',text)
  (assets/imp.name).write_text(text)
for name in ['home-layout.json','panda-home.json']:shutil.copy2(a.source/'assets'/name,assets/name)
for f in Path(__file__).parent.glob('*.gd'):
 if f.name!='bake_editor_plugin.gd':shutil.copy2(f,a.output/f.name)
plugin=a.output/'addons/bake_probe';plugin.mkdir(parents=True)
shutil.copy2(Path(__file__).parent/'bake_editor_plugin.gd',plugin/'plugin.gd')
(plugin/'plugin.cfg').write_text('[plugin]\nname="House Lightmap Bake"\ndescription="Isolated native editor bake"\nauthor="XLands"\nversion="1.0"\nscript="plugin.gd"\n')
(a.output/'project.godot').write_text('config_version=5\n[application]\nconfig/name="House lighting — isolated"\n[display]\nwindow/size/viewport_width=1200\nwindow/size/viewport_height=800\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\n')
print(a.output.resolve())
