#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
# SPDX-License-Identifier: MIT
# XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
"""Stamp only allowlisted, project-authored code. Never rewrite vendor assets."""
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
web = root / 'worlds/doraemon/web'
folders = [web / 'lib/town', web / 'lib/community', web / 'components/worlds', web / 'build',
           root / 'worlds/frog/source', root / 'worlds/conan/source', root / 'worlds/conan/web-project']
files = {p for folder in folders for p in folder.rglob('*')
         if p.suffix in ('.ts', '.tsx', '.gd') and not {'assets', '.godot', 'addons'}.intersection(p.parts)}
files.update(root / name for name in [
    'tools/native-loader.js', 'tools/export-native-web.py', 'tools/refresh-native-shells.py',
    'tools/stamp-source-provenance.py', 'tools/verify-build-provenance.mjs'])
files.add(web / 'pages-entry.tsx')
lines = ['SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors',
         'SPDX-License-Identifier: MIT',
         'XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds']
missing = []
for path in sorted(files):
    text = path.read_text()
    prefix = '# ' if path.suffix in ('.gd', '.py') else '// '
    header = ''.join(prefix + line + '\n' for line in lines)
    if header in text[:1000]:
        continue
    missing.append(str(path.relative_to(root)))
    if not args.check:
        if text.startswith('#!'):
            shebang, text = text.split('\n', 1)
            text = shebang + '\n' + header + text
        else:
            text = header + text
        path.write_text(text)
if args.check and missing:
    raise SystemExit('Missing source notices:\n' + '\n'.join(missing))
print(f'{"PASS" if args.check else "STAMPED"}: {len(files)} project-authored files; {len(missing)} changed.')
