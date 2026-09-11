const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (module, file) => module._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
}).outputText, file);
global.document = {documentElement: {dataset: {assetBase: '/frank_worlds/'}}};
global.location = {origin: 'https://frankfanyiming.github.io'};
global.localStorage = {getItem: () => '', removeItem() {}};
const realFetch = global.fetch, realTimeout = global.setTimeout;
const file = require.resolve('../lib/community/client.ts');
function client() { delete require.cache[file]; return require(file); }
const config = () => Response.json({apiOrigin: 'https://community.example'});
(async () => {
  try {
    // Failed configuration must not poison subsequent retries or send API calls to GitHub Pages.
    let attempts = 0;
    global.fetch = async () => ++attempts === 1 ? Response.json({}, {status: 503}) : config();
    let c = client();
    await assert.rejects(c.apiBase(), e => e.code === 'NETWORK');
    assert.equal(await c.apiBase(), 'https://community.example');
    // Public reads are simple requests: no unnecessary CORS preflight.
    const requests = [];
    global.fetch = async (url, options) => {
      requests.push({url, options});
      return url.endsWith('community-config.json') ? config() : Response.json({notes: []});
    };
    c = client(); assert.deepEqual(await c.api('notes'), {notes: []});
    assert.deepEqual(requests[1].options.headers, {});
    // Upstream HTML errors are connectivity failures, not successful empty data or missing configuration.
    global.fetch = async url => url.endsWith('community-config.json') ? config() : new Response('<html>Blocked</html>', {status: 403});
    c = client(); await assert.rejects(c.api('notes'), e => e.code === 'NETWORK' && e.status === 403);
    // Bound both response-header and response-body stalls. Abort without an endless spinner.
    global.setTimeout = (fn, ms, ...args) => realTimeout(fn, ms === 12000 ? 10 : ms, ...args);
    global.fetch = async (url, options) => url.endsWith('community-config.json') ? config() : new Promise((_, reject) => {
      options.signal.addEventListener('abort', () => reject(new DOMException('Timed out', 'AbortError')));
    });
    c = client(); await assert.rejects(c.api('notes'), e => e.code === 'NETWORK');
    console.log('PASS: API config retry, simple public requests, upstream HTML errors and stalled connections');
  } finally { global.fetch = realFetch; global.setTimeout = realTimeout; }
})().catch(e => {console.error(e); process.exitCode = 1;});
