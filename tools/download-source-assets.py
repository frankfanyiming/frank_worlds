#!/usr/bin/env python3
"""Download, verify and unpack Frank's Godot or Blender source archive. Python 3.12+."""
import argparse,concurrent.futures,hashlib,json,pathlib,tarfile,urllib.request,time
BASE='https://github.com/frankfanyiming/frank_worlds/releases/download/doraemon-v1.0.0/'
def fetch(url,target):
 for attempt in range(3):
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'frank-worlds-source-downloader'})
   with urllib.request.urlopen(request,timeout=90) as response,target.with_suffix(target.suffix+'.download').open('wb') as out:
    while chunk:=response.read(1024*1024):out.write(chunk)
   target.with_suffix(target.suffix+'.download').replace(target);return
  except Exception:
   if attempt==2:raise
   time.sleep(2)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description='下载完整 Godot / Blender 工程，自动拼接分卷并校验。')
 ap.add_argument('kind',choices=['godot','blender']);ap.add_argument('--output',default='frank-worlds-source');ap.add_argument('--local-parts');ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
 out=pathlib.Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest_path=pathlib.Path(__file__).with_name('source-archives.json')
 if not manifest_path.exists():manifest_path=out/'source-archives.json';fetch(BASE+'source-archives.json',manifest_path)
 package=json.loads(manifest_path.read_text())[args.kind];parts=pathlib.Path(args.local_parts).resolve() if args.local_parts else out/'parts';parts.mkdir(parents=True,exist_ok=True)
 def piece(spec):
  path=parts/spec['name']
  if not path.exists() or sha(path)!=spec['sha256']:
   if args.local_parts:raise ValueError('Missing or damaged local piece: '+str(path))
   fetch(BASE+spec['name'],path)
  if sha(path)!=spec['sha256']:raise ValueError('Checksum mismatch: '+spec['name'])
  print('Verified',spec['name'],flush=True);return path
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:paths=list(pool.map(piece,package['parts']))
 h=hashlib.sha256();archive=out/package['archive'];destination=None if args.verify_only else archive.open('wb')
 try:
  for path in paths:
   with path.open('rb') as f:
    while chunk:=f.read(1024*1024):
     h.update(chunk)
     if destination:destination.write(chunk)
 finally:
  if destination:destination.close()
 if h.hexdigest()!=package['sha256']:raise ValueError('Full archive checksum mismatch')
 print('Full archive SHA-256 verified:',package['sha256'])
 if not args.verify_only:
  with tarfile.open(archive) as tar:tar.extractall(out,filter='data')
  print('Ready:',out)
if __name__=='__main__':main()
