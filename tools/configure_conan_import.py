"""Preserve embedded maps and foot-lock keys after Godot's initial scene import."""
from pathlib import Path
import argparse,json,subprocess

def configure_conan_import(project:Path,godot:str='godot')->bool:
 script=Path(__file__).with_name('configure-conan-import.gd')
 result=subprocess.run([godot,'--headless','--path',str(project.resolve()),'--script',str(script)],check=True,text=True,capture_output=True)
 prefix='CONAN_IMPORT_CONFIGURATION '
 rows=[line[len(prefix):] for line in result.stdout.splitlines() if line.startswith(prefix)]
 if len(rows)!=1:raise RuntimeError('Missing import configuration result: '+result.stdout+result.stderr)
 data=json.loads(rows[0])
 if data['changed']:print('Configured character imports:',', '.join(data['files']))
 return data['changed']

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path);parser.add_argument('--godot',default='godot');args=parser.parse_args()
 print(json.dumps({'changed':configure_conan_import(args.project,args.godot)}))
