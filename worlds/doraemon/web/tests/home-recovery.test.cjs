const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
const base = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(base, 'index.html'), 'utf8');
const fallback = html.match(/<div id="root">([\s\S]*?)\n  <script>/)[1];
for (const value of ['covers/doraemon.webp', 'covers/frog.webp', 'covers/conan.webp',
  'https://x.com/FrankFYM001', 'frank001', '150015050', 'resources/xlands-skills.zip']) {
  assert.ok(fallback.includes(value), value);
}
assert.ok(!fallback.includes('douyin.com/user/self'));

function environment() {
  const handlers = {}, timers = [], notice = {hidden: true};
  const root = {innerHTML: fallback};
  return {handlers, timers, notice, root, context: {
    document: {getElementById: id => id === 'root' ? root : notice},
    window: {addEventListener: (type, fn) => (handlers[type] ??= []).push(fn)},
    setTimeout: fn => timers.push(fn),
  }};
}
// The inline guard operates even when the module never downloads.
const guard = html.match(/<script>([\s\S]*?)<\/script>/)[1];
for (const trigger of ['error', 'unhandledrejection', 'timeout']) {
  const e = environment(); vm.runInNewContext(guard, e.context);
  if (trigger === 'timeout') e.timers.shift()(); else e.handlers[trigger][0]({});
  assert.equal(e.notice.hidden, false, trigger);
  assert.equal(e.root.innerHTML, fallback);
}

// Execute the actual entry module against a root adapter. No browser is launched.
const code = ts.transpileModule(fs.readFileSync(path.join(base, 'pages-entry.tsx'), 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022},
}).outputText;
const e = environment(); let unmounts = 0, tree;
class ErrorEvent { constructor(error) {this.error = error;} }
class Component {}
const jsx = (type, props) => ({type, props});
Object.assign(e.context, {exports: {}, ErrorEvent, require: id => {
  if (id === 'react-dom/client') return {createRoot: () => ({render: v => {tree = v;}, unmount: () => unmounts++})};
  if (id === 'react') return {Component};
  if (id === 'react/jsx-runtime') return {jsx, jsxs: jsx};
  if (id.endsWith('.css') || id === './app/page') return {};
  throw new Error(id);
}});
vm.runInNewContext(code, e.context);
assert.ok(tree);
const boundary = new tree.type({}); boundary.state = {failed: true};
assert.equal(boundary.render().props.dangerouslySetInnerHTML.__html, fallback);
boundary.componentDidCatch(); assert.equal(e.notice.hidden, false);
e.notice.hidden = true; e.root.innerHTML = '<div>interactive UI</div>';
e.handlers.error[0]({target: 'broken image'});
assert.equal(e.timers.length, 0, 'asset errors must not unmount the working app');
e.handlers.error[0](new ErrorEvent(new Error('fatal runtime error')));
e.handlers.unhandledrejection[0]({reason: new Error('duplicate report')});
assert.equal(unmounts, 0, 'unmount must wait until React finishes its current task');
assert.equal(e.timers.length, 1, 'repeated failures schedule only one recovery');
e.timers.shift()();
assert.equal(unmounts, 1); assert.equal(e.root.innerHTML, fallback); assert.equal(e.notice.hidden, false);
console.log('PASS: static contact fallback, stalled module, fatal runtime recovery and duplicate errors');
