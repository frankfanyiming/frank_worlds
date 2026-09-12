"""Stage verified local character assets; this does not export or publish a site."""
from pathlib import Path
import argparse,hashlib,json,shutil
from configure_conan_import import configure_conan_import
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--godot',default='godot');args=parser.parse_args()
R=Path(__file__).resolve().parents[1];B=R/'worlds/conan/blender/character-v2';E=R/'docs/evidence/conan-character'
previous_path=R/'docs/conan-character-source.json'
previous_provenance=json.loads(previous_path.read_text()) if previous_path.exists() else {}
tasks={'conan':{'generation':'f856fc5a-20c2-4029-9f2a-b851b941c30a','conversion':'b287f046-e162-4fb9-b4c5-5594cf3b4d46','previous':'103dec1e-af57-4f44-9c00-b6e6c0dbcd6e'},'agasa':{'generation':'6384b71d-63d5-428e-be6d-94f243972fce','conversion':'5db7a64b-184e-4d40-9a71-894d1232db84','previous':'0ab52d1c-e1b8-4d61-b5d1-5034297fd660'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def portable(p):return str(p.relative_to(R))
motion={'version':2,'units':'meters and seconds','root_motion':'in_place','playback':'Use horizontal speed measured from displacement after collisions divided by clip reference speed.'}
provenance={'status':'Model and Blender validation complete; engine playback and web release are validated separately.','model':'Tripo v3.1','scenario':'game-mobile','rigging':'Blender custom 20-bone skin, maximum four influences (actual maximum two).','characters':{}}
for key,ids in tasks.items():
 report=json.loads((E/key/'motion-check.json').read_text());asset=B/(key+'.glb');assert sha(asset)==report['runtime_sha256']
 old=B/'originals'/(key+'.glb');fbx=next((B/('tripo-'+key)).glob('tripo-out/*/model.fbx'))
 motion[key]={'height':report['height'],'forward':'Godot +Z','walk_speed':report['clips']['Walk']['reference_speed'],'run_speed':report['clips']['Run']['reference_speed'],'cycles':{n:{'seconds':v['duration'],'fps':30,'frames':round(v['duration']*30)} for n,v in report['clips'].items()},'runtime_sha256':sha(asset)}
 for project in ['source','web-project']:
  dst=R/'worlds/conan'/project/'assets';dst.mkdir(parents=True,exist_ok=True);shutil.copy2(asset,dst/asset.name)
 provenance['characters'][key]={'source':'Tripo','generation_task_id':ids['generation'],'conversion_task_id':ids['conversion'],'previous_tripo_task_id':ids['previous'],'previous_runtime_backup':portable(old),'previous_runtime_sha256':sha(old),'reference_images':[portable(B/'reference'/(key+'-front.png')),portable(B/'reference'/(key+'-turnaround.png'))],'immutable_input':portable(fbx),'immutable_input_sha256':sha(fbx),'editable_blend':portable(B/(key+'-rig.blend')),'runtime_asset':f'worlds/conan/web-project/assets/{key}.glb','runtime_bytes':asset.stat().st_size,'runtime_sha256':sha(asset),'faces':report['faces'],'height':report['height'],'bones':report['bones'],'max_vertex_weights':report['max_weights'],'animations':list(report['clips']),'motion_evidence':portable(E/key/'motion-check.json'),'actual_glb_renders':f'docs/evidence/conan-character/{key}-final/','engine_playback':{'status':'pending runtime integration'}}
 # Preserve a recorded result only for the same model and controller revision.
 previous=previous_provenance.get('characters',{}).get(key,{})
 playback=previous.get('engine_playback',{})
 if previous.get('runtime_sha256')==sha(asset) and playback.get('world_sha256')==sha(R/'worlds/conan/web-project/world.gd'):
  provenance['characters'][key]['engine_playback']=playback
for project in ['source','web-project']:(R/'worlds/conan'/project/'assets/character-motion.json').write_text(json.dumps(motion,ensure_ascii=False,indent=2)+'\n')
(R/'docs/conan-character-source.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
(E/'character-motion.json').write_text(json.dumps(motion,ensure_ascii=False,indent=2)+'\n')
for project in ['source','web-project']:
 p=R/'worlds/conan'/project
 if shutil.which(args.godot) and all((p/'assets'/(key+'.glb.import')).exists() for key in tasks):configure_conan_import(p,args.godot)
 else:print('Import settings will be configured automatically by tools/export-native-web.py after its first import:',portable(p))
print(json.dumps(motion,ensure_ascii=False,indent=2))
