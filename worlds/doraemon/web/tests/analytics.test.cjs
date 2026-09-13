const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
const base = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(base, 'public/analytics.js'), 'utf8');
const configured = {enabled: true, websiteId: '12345678-1234-1234-1234-123456789abc', scriptUrl: 'https://cloud.umami.is/script.js', domains: ['frankfanyiming.github.io']};
const flush = () => new Promise(resolve => setImmediate(resolve));
function environment(options = {}) {
  const handlers = {}, scripts = [], received = [], requests = [], timers = new Map();
  let nextTimer = 0;
  const location = new URL(options.url || 'https://frankfanyiming.github.io/frank_worlds/?v=28&utm_source=x&email=secret#');
  const window = {addEventListener: (name, fn) => handlers[name] = fn, removeEventListener: name => delete handlers[name], matchMedia: () => ({matches: false}), __xlandsAnalyticsEvents: options.pending || []};
  window.parent = options.iframe ? {} : window;
  const context = {window, location, navigator: {userAgent: 'desktop', doNotTrack: options.dnt ? '1' : '0'},
    localStorage: {getItem: () => options.exclude ? '1' : null}, URL, URLSearchParams, AbortController, Set, Promise,
    setTimeout: fn => {timers.set(++nextTimer, fn); return nextTimer;}, clearTimeout: id => timers.delete(id),
    document: {currentScript: {src: 'https://frankfanyiming.github.io/frank_worlds/analytics.js'}, referrer: 'https://x.com/private/path?token=secret', createElement: () => ({dataset: {}}), head: {appendChild: script => scripts.push(script)}},
    fetch: async (...args) => {requests.push(args); if (options.reject) throw Error('offline'); return {ok: true, json: async () => options.config || configured};},
  };
  vm.runInNewContext(source, context);
  function loadTracker() {
    assert.equal(scripts.length, 1);
    window.umami = {track: fn => {received.push(fn({website: configured.websiteId, url: location.href, referrer: 'private', language: 'zh-CN'})); return Promise.resolve();}};
    scripts[0].onload();
  }
  return {window, location, context, handlers, scripts, received, requests, timers, loadTracker};
}
(async () => {
  const e = environment(); await flush();
  e.location.hash = '#world/conan'; e.handlers.hashchange();
  e.window.xlandsAnalytics.event('world_enter', {world: 'conan', email: 'private'});
  e.loadTracker();
  assert.deepEqual(e.received.map(p => p.url), ['/frank_worlds/', '/frank_worlds/world/conan', '/frank_worlds/world/conan']);
  assert.equal(e.received[2].name, 'world_enter');
  assert.equal(e.received[0].data.source, 'x');
  assert.equal(e.received[0].referrer, 'https://x.com');
  assert.ok(!JSON.stringify(e.received).includes('secret'));
  assert.ok(!JSON.stringify(e.received).includes('email'));
  assert.equal(e.scripts[0].dataset.autoTrack, 'false');
  e.handlers.hashchange(); assert.equal(e.received.length, 3, 'repeat hash event is not another view');
  e.location.hash = '#branch/frog/private-id'; e.handlers.hashchange();
  e.window.xlandsAnalytics.event('other', {world: 'frog'});
  assert.equal(e.received.length, 3, 'private routes and arbitrary events are ignored');
  e.location.hash = '#'; e.handlers.hashchange();
  assert.equal(e.received.length, 4, 'returning to the homepage is a new view');
  for (const options of [{dnt: true}, {exclude: true}, {iframe: true}]) {
    const skip = environment(options); await flush(); assert.equal(skip.requests.length, 0); assert.equal(skip.scripts.length, 0);
  }
  for (const options of [{reject: true}, {config: {...configured, enabled: false}}, {config: {...configured, websiteId: ''}}, {config: {...configured, domains: ['localhost']}}, {config: {...configured, scriptUrl: 'http://unsafe.test/script.js'}}]) {
    const skip = environment(options); await flush(); assert.equal(skip.scripts.length, 0);
  }
  const timed = environment(); await flush(); [...timed.timers.values()].forEach(fn => fn()); timed.loadTracker(); assert.equal(timed.received.length, 0, 'late tracker cannot flush after deadline');
  const standalone = environment({url: 'https://frankfanyiming.github.io/frank_worlds/worlds/frog/index.html', pending: [{name: 'world_enter', data: {world: 'frog'}}]});
  await flush(); standalone.loadTracker(); assert.equal(standalone.received.length, 2); assert.equal(standalone.received[0].url, '/frank_worlds/world/frog');

  const module = {exports: {}}; const records = [];
  const compiled = ts.transpileModule(fs.readFileSync(path.join(base, 'lib/community/analytics.ts'), 'utf8'), {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText;
  vm.runInNewContext(compiled, {exports: module.exports, window: {xlandsAnalytics: {event: (name, data) => records.push({name, data})}}, Date});
  const attempt = module.exports.beginWorldLoad('conan'); attempt.ready(); attempt.ready(); attempt.error('engine'); attempt.error('engine');
  const aborted = module.exports.beginWorldLoad('frog'); aborted.dispose(); aborted.ready(); aborted.error();
  const failed = module.exports.beginWorldLoad('doraemon'); failed.error('download'); failed.ready();
  assert.deepEqual(records.map(r => r.name), ['world_enter', 'world_ready', 'world_runtime_error', 'world_enter', 'world_enter', 'world_load_error']);
  console.log('PASS: hash pageviews, deferred events, source privacy, iframe deduplication, disabled/offline/timeout behavior, load attempts and stale callbacks');
})();
