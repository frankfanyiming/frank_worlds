"""Fetch the exact CC0 source files recorded in open-assets-manifest.json.

No account or API key is required. Downloads are build inputs, never a client
dependency. Existing files are reused only after size and checksum validation.
"""
import concurrent.futures, hashlib, json, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=json.loads(Path(__file__).with_name('open-assets-manifest.json').read_text())
DEST=(ROOT/'work/open-assets-r22').resolve()
def valid(path,entry):
    return path.is_file() and path.stat().st_size==entry['size'] and hashlib.md5(path.read_bytes()).hexdigest()==entry['md5']
def fetch(job):
    relative,entry=job;path=(DEST/relative).resolve()
    if DEST not in path.parents:raise ValueError('Source path outside asset directory')
    if valid(path,entry):return str(relative)+' verified'
    path.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(4):
        try:
            request=urllib.request.Request(entry['url'],headers={'User-Agent':'FrankWorlds-CC0-Furniture/1.0'})
            with urllib.request.urlopen(request,timeout=40) as response:data=response.read()
            if len(data)!=entry['size'] or hashlib.md5(data).hexdigest()!=entry['md5']:
                raise ValueError('Source checksum mismatch: '+str(relative))
            temporary=path.with_suffix(path.suffix+'.part');temporary.write_bytes(data);temporary.replace(path)
            return str(relative)+' downloaded'
        except Exception:
            if attempt==3:raise
            time.sleep(1+attempt)
jobs=[]
for asset in MANIFEST['assets']:
    item=asset['download'];key=asset['id']
    jobs.append((Path(key)/(key+'_1k.gltf'),item))
    jobs.extend((Path(key)/name,entry) for name,entry in item.get('include',{}).items())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    for result in executor.map(fetch,jobs):print(result,flush=True)
print('CC0_SOURCE_FILES_VERIFIED',len(jobs))
