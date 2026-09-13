"""Recover the pre-rebuild house into a separate folder without changing runtime assets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = 'bafe7f3fa6f9aa63a9e02a3729c77432335ef885'
PREFIX = 'worlds/doraemon/web/'
PARTS = ['world-v3', 'interiors-v3', 'furniture-ground-v10', 'furniture-upper-v10',
         'details/house-v10', 'details/life-v10', 'details/stairs-support-v10']
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, default=ROOT.parent / 'doraemon-house-recovery26')
args = parser.parse_args()
sources = ['public/models/' + part + '.glb' for part in PARTS]
sources += ['public/models/world.json', 'lib/town/engine.ts', 'lib/town/weather.ts', 'lib/town/lighting.ts']
records = []
for source in sources:
    raw = subprocess.check_output(['git', 'show', SNAPSHOT + ':' + PREFIX + source], cwd=ROOT)
    output = args.out / 'originals' / source
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.read_bytes() != raw:
        raise SystemExit('Refusing to overwrite a changed recovery file: ' + str(output))
    output.write_bytes(raw)
    records.append({'source': PREFIX + source, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
report = {'snapshot': SNAPSHOT, 'runtimeVersion': '20260907-video10-final',
          'rebuildCommit': '4732f812200b421f9984e36079602a2f14be78d9',
          'files': records, 'productionChanged': False}
(args.out / 'recovery-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'Recovered {len(records)} original files into {args.out}; production files unchanged.')
