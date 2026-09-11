import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';

const source = await readFile(new URL('./native-loader.js', import.meta.url), 'utf8');
const functions = source.slice(0, source.lastIndexOf('load().catch(fail);'));
const raw = Buffer.from('Verified world bytes. '.repeat(300));
const encoded = gzipSync(raw), sha256 = createHash('sha256').update(raw).digest('hex');
const chunk = {file: 'world-000.bin.gz', bytes: encoded.length, rawBytes: raw.length, sha256};
const elements = new Map();
const context = {
  URLSearchParams, Uint8Array, Response, ReadableStream, DecompressionStream, AbortController, crypto,
  setTimeout: (fn, ms) => setTimeout(fn, ms >= 20000 ? 15 : ms), clearTimeout,
  config: {}, console, location: {search: ''}, parent: {postMessage() {}},
  window: {addEventListener() {}},
  document: {documentElement: {}, querySelector: id => {if (!elements.has(id)) elements.set(id, {}); return elements.get(id);}, querySelectorAll: () => []},
  chunk,
};
let requests = 0;
const seenProgress = [];
context.onProgress = n => seenProgress.push(n);
context.fetch = async (url, options) => {
  assert(url.includes(sha256));
  if (++requests === 1) {
    return new Response(new ReadableStream({
      start(controller) {controller.enqueue(encoded.subarray(0, 12));},
      pull(controller) {controller.error(Error('Connection interrupted'));},
    }));
  }
  assert.equal(options.headers.Range, 'bytes=12-');
  return new Response(encoded.subarray(12), {status: 206, headers: {'Content-Range': `bytes 12-${encoded.length - 1}/${encoded.length}`}});
};
const bytes = await runInNewContext(functions + '\ndownloadChunk(chunk, onProgress)', {...context});
assert.deepEqual(Buffer.from(bytes), raw);
assert(seenProgress.includes(12), 'Show progress before the whole chunk completes');
assert.equal(requests, 2);

// Servers that ignore Range must restart from zero instead of concatenating duplicate bytes.
requests = 0;
context.fetch = async () => ++requests === 1 ? new Response(encoded.subarray(0, 12)) : new Response(encoded);
assert.deepEqual(Buffer.from(await runInNewContext(functions + '\ndownloadChunk(chunk, onProgress)', {...context})), raw);
assert.equal(requests, 2);

let aborted = 0;
context.fetch = async (_, options) => new Promise((_, reject) => options.signal.addEventListener('abort', () => {
  aborted++; reject(new DOMException('Aborted', 'AbortError'));
}));
await assert.rejects(runInNewContext(functions + '\ndownloadChunk(chunk, onProgress)', {...context}));
assert.equal(aborted, 3, 'Stop and abort stalled requests after bounded retries');
console.log('PASS: interrupted stream resumes, progress before completion, Range fallback and bounded timeout');
