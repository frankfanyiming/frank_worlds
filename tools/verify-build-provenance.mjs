#!/usr/bin/env node
// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, sep } from 'node:path';
import assert from 'node:assert/strict';

const directory = resolve(process.argv[2] || 'worlds/doraemon/web/dist-pages');
const manifest = JSON.parse(await readFile(resolve(directory, 'provenance.json'), 'utf8'));
assert.equal(manifest.origin.projectId, 'xlands-frankfym001');
assert.equal(manifest.origin.repository, 'https://github.com/frankfanyiming/frank_worlds');
assert.match(manifest.build.commit || '', /^[a-f0-9]{40}$/);
assert.equal(new Set(manifest.files.map(file => file.path)).size, manifest.files.length);
assert.ok(manifest.files.some(file => file.path === 'LICENSE.txt'));
assert.ok(manifest.files.some(file => file.path === 'NOTICE.txt'));
assert.ok(manifest.files.some(file => file.path.endsWith('.js')));
for (const file of manifest.files) {
  const path = resolve(directory, file.path);
  assert.ok(path.startsWith(directory + sep), 'Path outside build directory');
  const bytes = await readFile(path);
  assert.equal(bytes.length, file.bytes, `${file.path}: size`);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), file.sha256, `${file.path}: hash`);
  if (file.path.endsWith('.js')) {
    // Vite may put its preload helper before the retained provenance comment.
    assert.ok(bytes.toString().includes('/*! XLands build provenance | xlands-frankfym001'), `${file.path}: missing retained banner`);
    assert.ok(bytes.toString().includes(manifest.build.commit), `${file.path}: missing commit`);
  }
}
console.log(`PASS: ${manifest.files.length} source-attributed build files, commit ${manifest.build.commit}.`);
