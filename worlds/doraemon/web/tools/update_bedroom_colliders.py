"""Merge the restored bedroom and rebuilt staircase collision data."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'public/models';d=json.loads((p/'world.json').read_text());n=json.loads((p/'neighborhood-v12.json').read_text());old=json.loads((ROOT/'tools/legacy-bedroom-colliders.json').read_text());d['colliders']=[c for c in d['colliders'] if not c['group'].startswith(('v11_','hero_','v12_'))]+n['colliders']+old;d['revision']=12;(p/'world.json').write_text(json.dumps(d,separators=(',',':')))
