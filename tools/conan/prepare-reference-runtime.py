"""Create native + web derivatives from new architecture source; preserve collider geometry."""
import bpy,sys,math,json,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'worlds/conan/blender/reference-2026-09';BACK=OUT/'originals';BACK.mkdir(parents=True,exist_ok=True)
reports=[]
for name in ['agasa','street-block']:
 source=OUT/(name+'.glb');native=ROOT/'worlds/conan/source/assets/buildings'/(name+'.glb');web=ROOT/'worlds/conan/web-project/assets/buildings'/(name+'.glb')
 for target in [native,web]:
  backup=BACK/(target.parents[2].name+'-'+name+'.glb')
  if target.exists() and not backup.exists():shutil.copy2(target,backup)
 shutil.copy2(source,native)
 for version in ['source','web-project']:shutil.copy2(OUT/(name+'.json'),ROOT/f'worlds/conan/{version}/assets/buildings'/(name+'.json'))
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];changes=[]
 for im in bpy.data.images:
  if max(im.size[:])>768:
   before=list(im.size[:]);ratio=768/max(before);im.scale(max(1,round(before[0]*ratio)),max(1,round(before[1]*ratio)));im.pack();changes.append({'texture':im.name,'before':before,'after':list(im.size[:])})
 decimated=[]
 for o in objs:
  if '_Collision' in o.name:continue
  ratio=.40 if 'Lab_instruments' in o.name else .72 if name=='street-block' else 1.0
  if ratio<1.0:
   mod=o.modifiers.new('Web-only small detail reduction','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;decimated.append({'node':o.name,'ratio':ratio})
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(web),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=True)
 reports.append({'name':name,'native':{'bytes':native.stat().st_size,'sha256':hashlib.sha256(native.read_bytes()).hexdigest()},'web':{'bytes':web.stat().st_size,'sha256':hashlib.sha256(web.read_bytes()).hexdigest()},'image_resizes':changes,'visual_only_decimation':decimated,'collision_nodes_not_decimated':True})
(OUT/'architecture-runtime-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2));print('REFERENCE_RUNTIME_READY',reports,flush=True)
