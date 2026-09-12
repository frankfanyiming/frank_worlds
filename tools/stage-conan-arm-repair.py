"""Stage the arm-only postprocess after stage-conan-characters.py.

The immutable inputs live in the private local/source archive. Production
export calls configure_conan_import again after the initial editor import.
"""
import argparse, hashlib, json, shutil
from pathlib import Path
from configure_conan_import import configure_conan_import
R=Path(__file__).resolve().parents[1]
B=R/'worlds/conan/blender/arms-2026-09-13'
E=R/'docs/evidence/conan-arms-2026-09-13'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--godot',default='godot')
args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
provenance=json.loads((R/'docs/conan-character-source.json').read_text())
for key in ('conan','kogoro'):
 report=json.loads((E/(key+'-arm-repair.json')).read_text());asset=B/(key+'.glb')
 assert sha(asset)==report['runtime_sha256']
 assert sha(B/'originals'/(key+'.glb'))==report['source_sha256']
 for project in ('source','web-project'):
  folder=R/'worlds/conan'/project/'assets';shutil.copy2(asset,folder/asset.name)
  motion_path=folder/'character-motion.json';motion=json.loads(motion_path.read_text())
  if key in motion:motion[key]['runtime_sha256']=sha(asset)
  write(motion_path,motion)
 character=provenance['characters'].setdefault(key,{
  'source':'Tripo','generation_task_id':'efc231ac-2159-4fe1-9eab-8c3db4e88534',
  'rigging_task_id':'395a6b44-7d4a-489e-b7c6-5457dca89321',
  'height':1.81,'bones':17,'animations':['Idle','Walk','Run','Wave','Talk','Read','Sit'],
  'runtime_asset':'worlds/conan/web-project/assets/kogoro.glb'})
 previous_sha=character.get('runtime_sha256')
 character.update({'runtime_sha256':sha(asset),'runtime_bytes':asset.stat().st_size,
  'max_vertex_weights':4,'arm_repair':{'script':'tools/repair-conan-arms.py',
   'input_backup':str((B/'originals'/(key+'.glb')).relative_to(R)),
   'input_sha256':report['source_sha256'],
   'evidence':str((E/(key+'-arm-repair.json')).relative_to(R)),
   'changes':'Anatomically forward elbow bend, relaxed wrists and contralateral swing; sleeve transition smoothing.'+( ' Native Tripo-fitted arm pivots restored; 40 hand vertices detached from wrong leg bones.' if key=='kogoro' else ''),
   'preserved':'Tripo mesh, textures, triangles and all non-arm animation channels; genuine leg/foot skin unchanged.'}})
 if previous_sha!=sha(asset):character['engine_playback']={'status':'pending final arm-repair runtime verification'}
write(R/'docs/conan-character-source.json',provenance)
for project in ('source','web-project'):
 p=R/'worlds/conan'/project
 if shutil.which(args.godot) and all((p/'assets'/(key+'.glb.import')).exists() for key in ('conan','agasa','kogoro')):configure_conan_import(p,args.godot)
 else:print('Importer will be configured after first editor import:',p)
print('ARM_ASSETS_STAGED; export/publish not performed')
