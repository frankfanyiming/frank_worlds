"""Disable bake plugin and force EXR lossless reimport inside an isolated project."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('project',type=Path);a=p.parse_args();root=a.project
project=root/'project.godot';project.write_text(project.read_text().split('[editor_plugins]')[0])
for f in (root/'assets/house-lighting').glob('*.exr.import'):
 text=re.sub(r'compress/mode=\d+','compress/mode=0',f.read_text());text=re.sub(r'compress/hdr_compression=\d+','compress/hdr_compression=0',text);f.write_text(text)
 for cache in (root/'.godot/imported').glob(f.name.removesuffix('.import')+'-*'):cache.unlink()
