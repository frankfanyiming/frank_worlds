"""Read-only verification of the homepage release and retained world manifests."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='https://frankfanyiming.github.io/frank_worlds/')
parser.add_argument('--revision', type=int, default=25)
parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parents[1] / 'docs/evidence/homepage-revision25')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'publish-files.json').read_text())
nonce = str(int(time.time()))


def fetch(path):
    request = urllib.request.Request(args.base.rstrip('/') + '/' + path + '?verify=' + nonce,
                                     headers={'User-Agent': 'XLands-Homepage-Verification'})
    with urllib.request.urlopen(request, timeout=45) as response:
        assert response.status == 200, path
        return response.read()


release = json.loads(fetch('release.json'))
assert release['revision'] == args.revision
assert release['sourceCommit'] == manifest['sourceCommit']


def check_file(item):
    raw = fetch(item['path'])
    assert len(raw) == item['bytes'], item['path']
    assert hashlib.sha256(raw).hexdigest() == item['sha256'], item['path']
    return {'path': item['path'], 'bytes': len(raw), 'sha256': item['sha256'], 'status': 200}


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    checked = list(pool.map(check_file, manifest['files']))

worlds = []
for world in ('frog', 'conan'):
    for mobile in (False, True):
        path = f'worlds/{world}/' + ('mobile/' if mobile else '') + 'world-pack.json'
        pack = json.loads(fetch(path))
        expected = release['nativeMobilePacks' if mobile else 'nativePacks'][world]
        assert pack['sha256'] == expected['sha256'], path
        worlds.append({'path': path, 'sha256': pack['sha256']})

report = {'revision': args.revision, 'base': args.base, 'sourceCommit': release['sourceCommit'],
          'files': checked, 'retainedWorldManifests': worlds, 'passed': True,
          'scope': 'HTTP status, release identity and exact asset bytes; not a browser or load test.'}
(args.evidence / 'public-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: revision {args.revision}, {len(checked)} homepage assets and {len(worlds)} retained world manifests.')
