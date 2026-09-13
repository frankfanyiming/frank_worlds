// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Plugin } from 'vite';

// Public build information only. Never embed credentials, host paths or env dumps.
export function buildProvenance(): Plugin {
  const root = resolve('../../..');
  const origin = JSON.parse(readFileSync(resolve(root, 'SOURCE.json'), 'utf8'));
  const git = (...args: string[]) => {
    try { return execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); }
    catch { return ''; }
  };
  const commit = git('rev-parse', '--verify', 'HEAD') || null;
  const remote = git('remote', 'get-url', 'origin');
  // Accept only a plain GitHub owner/repo pair; never publish a credentialed URL.
  const match = remote.match(/^(?:https:\/\/github\.com\/|git@github\.com:)([\w.-]+)\/([\w.-]+?)(?:\.git)?$/);
  const repository = match ? `https://github.com/${match[1]}/${match[2]}` : null;
  const trackedSourceModified = !!git('diff', '--name-only', 'HEAD', '--', 'worlds', 'tools', 'SOURCE.json', 'NOTICE', 'LICENSE', 'CREDITS.md');
  const build = { repository, commit, trackedSourceModified };
  const banner = `/*! XLands build provenance | ${origin.projectId} | Frank / @FrankFYM001\n * Upstream: ${origin.repository}\n * Build: ${repository || 'unidentified checkout'} @ ${commit || 'unversioned'}${trackedSourceModified ? ' (modified)' : ''}\n * Original code: MIT. Third-party code retains its own licenses. See NOTICE.txt.\n */`;
  const notices = {
    'SOURCE.json': JSON.stringify(origin, null, 2) + '\n',
    'LICENSE.txt': readFileSync(resolve(root, 'LICENSE'), 'utf8'),
    'NOTICE.txt': readFileSync(resolve(root, 'NOTICE'), 'utf8'),
  };
  return {
    name: 'xlands-public-provenance',
    apply: 'build',
    outputOptions(options) {
      const previous = options.banner;
      return { ...options, banner: async chunk => banner + '\n' + (typeof previous === 'function' ? await previous(chunk) : previous || '') };
    },
    transformIndexHtml: {
      order: 'post',
      handler: () => [
        { tag: 'meta', attrs: { name: 'xlands-project', content: origin.projectId }, injectTo: 'head' },
        { tag: 'meta', attrs: { name: 'xlands-source-commit', content: commit || 'unversioned' }, injectTo: 'head' },
        { tag: 'link', attrs: { rel: 'author', href: origin.repository }, injectTo: 'head' },
      ],
    },
    generateBundle(_options, bundle) {
      const files: { path: string; bytes: number; sha256: string }[] = [];
      const record = (path: string, value: string | Uint8Array) => {
        const bytes = typeof value === 'string' ? Buffer.from(value) : value;
        files.push({ path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
      };
      for (const item of Object.values(bundle)) {
        if (/\.(js|css|html)$/.test(item.fileName)) record(item.fileName, item.type === 'chunk' ? item.code : item.source);
      }
      for (const [fileName, source] of Object.entries(notices)) {
        this.emitFile({ type: 'asset', fileName, source });
        record(fileName, source);
      }
      this.emitFile({ type: 'asset', fileName: 'provenance.json', source: JSON.stringify({
        schemaVersion: 1, origin, build,
        scope: 'Frontend bundle and included notices; model, engine and texture packs keep separate release manifests.',
        files: files.sort((a, b) => a.path.localeCompare(b.path)),
      }, null, 2) + '\n' });
    },
  };
}
