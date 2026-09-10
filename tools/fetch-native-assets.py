#!/usr/bin/env python3
"""Fetch immutable native project assets, verify the archive, then extract safely."""
import sys,json,hashlib,urllib.request,zipfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
name=sys.argv[1] if len(sys.argv)>1 else ''
if name not in ['frog','conan','conan-web']:raise SystemExit('Usage: python3 tools/fetch-native-assets.py frog|conan|conan-web')
world='conan' if name.startswith('conan') else name
manifest=json.loads((ROOT/'worlds'/world/'asset-manifest.json').read_text())
if manifest.get('availability')=='pending-publication':raise SystemExit('The full native source archives await publication approval; code and browser builds are available in this repository.')
entry=next(e for e in manifest['archives'] if e['id']==name)
target=ROOT/entry['extractTo'];target.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as temporary:
 archive=Path(temporary)/'source.zip';digest=hashlib.sha256()
 print('Downloading',entry['name'])
 with urllib.request.urlopen(entry['url']) as stream,archive.open('wb') as out:
  while chunk:=stream.read(1024*1024):out.write(chunk);digest.update(chunk)
 if digest.hexdigest()!=entry['sha256']:raise SystemExit('Checksum mismatch; no assets were installed')
 with zipfile.ZipFile(archive) as z:
  for info in z.infolist():
   destination=(target/info.filename).resolve()
   if not destination.is_relative_to(target.resolve()):raise SystemExit('Unsafe archive path')
   if (info.external_attr>>16)&0o170000==0o120000:raise SystemExit('Symlinks are not accepted')
  skipped=0
  for info in z.infolist():
   destination=target/info.filename
   if destination.exists():
    skipped+=1
    continue
   z.extract(info,target)
 print('Verified and installed:',target,'; existing files preserved:',skipped)
