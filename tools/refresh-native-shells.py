#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
# SPDX-License-Identifier: MIT
# XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
"""Refresh existing native HTML wrappers only; retain every pack/engine file."""
import argparse
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('release_directory', type=Path)
args = parser.parse_args()
commit = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD'], cwd=root, text=True).strip()
template = (root / 'tools/native-world-shell.html').read_text()
loader = (root / 'tools/native-loader.js').read_text()
outputs = []
for world in ('frog', 'conan'):
    path = args.release_directory / 'worlds' / world / 'index.html'
    previous = path.read_text()
    config = re.search(r'const config=(\{[^\n]*\});', previous)
    if not config:
        raise SystemExit(f'Cannot safely recover engine config: {path}')
    # Parse before writing either file, and carry the exact engine configuration forward.
    json.loads(config[1])
    result = template.replace('CONFIG_JSON', config[1]).replace('NATIVE_LOADER_JS', loader)
    result = result.replace('JUMP_BUTTON', '<button data-action="jump" aria-label="Jump">↑</button>' if world == 'frog' else '')
    result = result.replace('</head>', f'<meta name="xlands-source-commit" content="{commit}"></head>', 1)
    assert all(token not in result for token in ('CONFIG_JSON', 'NATIVE_LOADER_JS', 'JUMP_BUTTON'))
    outputs.append((path, result))
for path, text in outputs:
    path.write_text(text)
    for source_name, public_name in [('SOURCE.json', 'SOURCE.json'), ('LICENSE', 'LICENSE.txt'), ('NOTICE', 'NOTICE.txt')]:
        (path.parent / public_name).write_bytes((root / source_name).read_bytes())
print(f'Updated {len(outputs)} HTML wrappers at {commit}; engine and world packs untouched.')
