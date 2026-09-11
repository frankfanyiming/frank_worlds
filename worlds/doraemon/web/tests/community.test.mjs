import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFile, readdir } from 'node:fs/promises';
import { build } from 'esbuild';
async function moduleFor(file) {
  const { outputFiles } = await build({
    entryPoints: [file],
    bundle: true,
    platform: 'node',
    format: 'esm',
    write: false,
  });
  return import(
    'data:text/javascript;base64,' +
      Buffer.from(outputFiles[0].text).toString('base64')
  );
}
const M = await moduleFor('lib/community/merge.ts'),
  { handleCommunity } = await moduleFor('lib/community/server.ts'),
  { applyPlan } = await moduleFor('lib/community/agent.ts'),
  billing = await moduleFor('lib/community/billing.ts');
const sqlite = new DatabaseSync(':memory:');
for (const file of (await readdir('drizzle'))
  .filter((f) => f.endsWith('.sql'))
  .sort())
  sqlite.exec(await readFile('drizzle/' + file, 'utf8'));
const DB = {
  prepare(sql) {
    return {
      bind(...args) {
        return this.with(args);
      },
      with(args = []) {
        const execute = () => ({
          meta: { changes: Number(sqlite.prepare(sql).run(...args).changes) },
        });
        return {
          first: async () => sqlite.prepare(sql).get(...args) || null,
          all: async () => ({ results: sqlite.prepare(sql).all(...args) }),
          run: async () => execute(),
          execute,
        };
      },
      first() {
        return this.with().first();
      },
      all() {
        return this.with().all();
      },
      run() {
        return this.with().run();
      },
    };
  },
  async batch(statements) {
    sqlite.exec('BEGIN');
    try {
      const results = statements.map((statement) => statement.execute());
      sqlite.exec('COMMIT');
      return results;
    } catch (error) {
      sqlite.exec('ROLLBACK');
      throw error;
    }
  },
};
const env = { DB, OWNER_ACCOUNT_EMAIL: 'owner@example.test' };
let checks = 0;
async function req(
  path,
  method = 'GET',
  body,
  token = '',
  admin = false,
  expected = 200,
) {
  const r = await handleCommunity(
    new Request('https://test.example/api/community/' + path, {
      method,
      headers: {
        ...(token ? { 'X-Visitor-Token': token } : {}),
        ...(admin
          ? { 'oai-authenticated-user-email': 'owner@example.test' }
          : {}),
        Origin: 'https://frankfanyiming.github.io',
        'Content-Type': 'application/json',
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
    env,
  );
  const json = await r.json();
  assert.equal(
    r.status,
    expected,
    `${method} ${path}: ${JSON.stringify(json)}`,
  );
  checks++;
  return json;
}
const a = (await req('session', 'POST', {}, '', false, 201)).token,
  b = (await req('session', 'POST', {}, '', false, 201)).token;
const note = await req(
  'notes',
  'POST',
  {
    world: 'frog',
    body: 'A quiet little forest. <script>never run</script>',
    nickname: 'A',
    email: 'private@example.test',
    contactConsent: true,
  },
  a,
  false,
  201,
);
const publicNotes = await req('notes');
assert(!JSON.stringify(publicNotes).includes('private@example.test'));
assert(!JSON.stringify(publicNotes).includes('owner_id'));
assert.equal(publicNotes.notes[0].owned, false);
checks += 3;
await req('contacts', 'GET', undefined, a, false, 403);
assert.equal(
  (await req('contacts', 'GET', undefined, '', true)).contacts[0].email,
  'private@example.test',
);
checks++;
await req('notes/' + note.id, 'DELETE', undefined, b, false, 403);
await req(
  'notes',
  'POST',
  { world: 'frog', body: 'x', email: 'a@b.test', contactConsent: false },
  a,
  false,
  400,
);
const aid = (
  await req(
    'branches',
    'POST',
    { world: 'frog', title: 'Forest A' },
    a,
    false,
    201,
  )
).id;
let ba = await req('branches/' + aid, 'GET', undefined, a);
assert.equal(ba.baseRevision, 'initial');
checks++;
await req('branches/' + aid, 'GET', undefined, b, false, 404);
await req(
  'branches/' + aid,
  'PUT',
  {
    revision: ba.revision,
    title: 'Published A',
    scene: ba.scene,
    publish: true,
  },
  a,
);
ba = await req('branches/' + aid, 'GET', undefined, a);
const tileId = Object.keys(ba.scene.tiles)[0];
const draft = structuredClone(ba.scene);
draft.objects.lamp_1 = {
  id: 'lamp_1',
  tileId,
  asset: 'lamp',
  position: { x: 1.5, y: 0, z: 1.5 },
  rotation: 0,
  color: '#ffffff',
  label: 'A lamp',
};
await req(
  'branches/' + aid,
  'PUT',
  { revision: ba.revision, title: 'Private title', scene: draft },
  a,
);
const pub = await req('branches/' + aid);
assert.equal(pub.title, 'Published A');
assert.equal(Object.keys(pub.scene.objects).length, 0);
checks += 2;
const bid = (
  await req(
    'branches',
    'POST',
    { world: 'frog', sourceId: aid, title: 'Branch B' },
    b,
    false,
    201,
  )
).id;
let bb = await req('branches/' + bid, 'GET', undefined, b);
assert.equal(Object.keys(bb.scene.objects).length, 0);
assert.equal(bb.baseRevision, 'initial');
checks += 2;
await req('proposals', 'POST', { branchId: aid }, a, false, 409);
ba = await req('branches/' + aid, 'GET', undefined, a);
await req(
  'branches/' + aid,
  'PUT',
  { revision: ba.revision, title: ba.title, scene: ba.scene, publish: true },
  a,
);
const pa = await req('proposals', 'POST', { branchId: aid }, a, false, 201);
assert.equal((await req('proposals', 'POST', { branchId: aid }, a)).id, pa.id);
checks++;
await req(
  'proposals/' + pa.id + '/merge',
  'POST',
  { mainRevision: 'initial', resolutions: {} },
  b,
  false,
  403,
);
const merged = await req(
  'proposals/' + pa.id + '/merge',
  'POST',
  { mainRevision: 'initial', resolutions: {} },
  a,
  true,
);
let root = await req('main/frog');
assert(root.scene.objects.lamp_1);
assert.equal(root.revision, merged.revision);
checks += 2;
bb.scene.tiles[tileId].biome = 'sand';
await req(
  'branches/' + bid,
  'PUT',
  { revision: bb.revision, title: bb.title, scene: bb.scene, publish: true },
  b,
);
const pb = await req('proposals', 'POST', { branchId: bid }, b, false, 201);
const preview = await req('proposals/' + pb.id);
assert.equal(preview.conflicts.length, 1);
assert(preview.branchScene);
checks += 2;
await req(
  'proposals/' + pb.id + '/merge',
  'POST',
  { mainRevision: root.revision, resolutions: {} },
  a,
  true,
  409,
);
const resolutions = Object.fromEntries(
  preview.conflicts.map((c) => [c.key, 'branch']),
);
await req(
  'proposals/' + pb.id + '/merge',
  'POST',
  { mainRevision: root.revision, resolutions },
  a,
  true,
);
root = await req('main/frog');
assert(root.scene.objects.lamp_1);
assert.equal(root.scene.tiles[tileId].biome, 'sand');
checks += 2;
// A public snapshot retains its original base even after its author synchronizes a newer draft.
await req(
  'branches/' + aid + '/sync',
  'POST',
  {
    revision: (await req('branches/' + aid, 'GET', undefined, a)).revision,
    resolutions: { ['tiles.' + tileId]: 'main' },
  },
  a,
);
const publicAfterSync = await req('branches/' + aid);
assert.equal(publicAfterSync.baseRevision, 'initial');
checks++;
const current = await req('branches/' + aid, 'GET', undefined, a);
const first = await req(
  'branches/' + aid,
  'PUT',
  { revision: current.revision, scene: current.scene, title: 'first' },
  a,
);
await req(
  'branches/' + aid,
  'PUT',
  { revision: current.revision, scene: current.scene, title: 'stale' },
  a,
  false,
  409,
);
const beforeRollback = root.revision;
await req(
  'rollback',
  'POST',
  { world: 'frog', revision: merged.revision, mainRevision: root.revision },
  a,
  true,
);
root = await req('main/frog');
assert.notEqual(root.revision, merged.revision);
assert.equal(root.scene.tiles[tileId].biome, 'grass');
assert(
  (await req('history/frog')).revisions.some((r) => r.id === beforeRollback),
);
checks += 3;
await req('notes/' + note.id, 'DELETE', undefined, a);
assert.equal(
  (await req('contacts', 'GET', undefined, '', true)).contacts.length,
  0,
);
checks++;
const base = M.addTile(M.emptyScene('frog')),
  tid = Object.keys(base.tiles)[0];
base.objects.a = {
  id: 'a',
  asset: 'chair',
  tileId: tid,
  position: { x: 1.5, y: 0, z: 1.5 },
  rotation: 0,
  color: '#ffffff',
  label: '',
};
const left = structuredClone(base),
  right = structuredClone(base);
left.objects.a.color = '#112233';
right.objects.a.rotation = 1;
let result = M.mergeScenes(base, left, right);
assert.equal(result.unresolved.length, 0);
assert.equal(result.scene.objects.a.color, '#112233');
assert.equal(result.scene.objects.a.rotation, 1);
checks += 3;
right.objects.a.color = '#334455';
result = M.mergeScenes(base, left, right);
assert(result.unresolved.some((c) => c.key === 'objects.a.color'));
checks++;
const resolved = M.mergeScenes(base, left, right, {
  'objects.a.color': 'branch',
});
assert.equal(resolved.scene.objects.a.color, '#334455');
checks++;
delete left.objects.a;
result = M.mergeScenes(base, left, right);
assert(result.unresolved.some((c) => c.kind === 'delete-edit'));
checks++;
const overlap = M.addTile(base);
const second = Object.values(overlap.tiles).find((t) => t.id !== tid);
second.x = 0;
second.z = 0;
assert(M.validateScene(overlap).includes('TILE_OVERLAP'));
assert(
  M.mergeScenes(base, base, overlap).unresolved.some(
    (c) => c.kind === 'overlap',
  ),
);
checks += 2;
const malformed = structuredClone(base);
malformed.tiles[tid] = null;
assert(M.validateScene(malformed).includes('INVALID_TILE'));
malformed.objects.a = null;
assert(M.validateScene(malformed).includes('INVALID_OBJECT'));
checks += 2;
const blocked = structuredClone(base);
blocked.objects.a.asset = 'tent';
blocked.objects.a.position.x = 0;
assert(M.validateScene(blocked).includes('PATH_BLOCKED'));
checks++;
const injection = JSON.parse(
  '{"schema":1,"world":"frog","tiles":{"__proto__":{"id":"__proto__","x":0,"z":0,"biome":"grass","label":""}},"objects":{}}',
);
assert(M.validateScene(injection).includes('INVALID_TILE'));
checks++;
assert.throws(() =>
  applyPlan(base, {
    summary: 'invalid',
    operations: [{ action: 'execute', code: 'anything' }],
  }),
);
checks++;
const notReady = await req('agent/plan', 'POST', {}, a, false, 503);
assert.equal(notReady.error, 'AGENT_UNAVAILABLE');
assert.equal(billing.chargeMicros(1000, 1000, 10000), 60000);
checks += 2;
const raw = '{"type":"test"}',
  stamp = Math.floor(Date.now() / 1000),
  secret = 'test-webhook';
const hmac = await crypto.subtle.importKey(
  'raw',
  new TextEncoder().encode(secret),
  { name: 'HMAC', hash: 'SHA-256' },
  false,
  ['sign'],
);
const signature = Buffer.from(
  await crypto.subtle.sign(
    'HMAC',
    hmac,
    new TextEncoder().encode(stamp + '.' + raw),
  ),
).toString('hex');
assert(
  await billing.validStripeSignature(raw, `t=${stamp},v1=${signature}`, secret),
);
assert(
  !(await billing.validStripeSignature(
    raw + 'x',
    `t=${stamp},v1=${signature}`,
    secret,
  )),
);
assert(
  !(await billing.validStripeSignature(
    raw,
    `t=${stamp},v1=${signature}`,
    secret,
    (stamp + 600) * 1000,
  )),
);
checks += 3;
// Requests actually race after their initial reads; the D1 batch remains atomic.
async function raceRequest(path, method, body, token = a, admin = false) {
  const r = await handleCommunity(
    new Request('https://test.example/api/community/' + path, {
      method,
      headers: {
        'X-Visitor-Token': token,
        ...(admin
          ? { 'oai-authenticated-user-email': 'owner@example.test' }
          : {}),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }),
    env,
  );
  return { status: r.status, json: await r.json() };
}
const beforeRace = await req('branches/' + aid, 'GET', undefined, a);
const writes = await Promise.all(
  ['one', 'two'].map((title) =>
    raceRequest('branches/' + aid, 'PUT', {
      title,
      scene: beforeRace.scene,
      revision: beforeRace.revision,
    }),
  ),
);
assert.deepEqual(writes.map((r) => r.status).sort(), [200, 409]);
checks++;
assert.equal(
  (await req('branches/' + aid, 'GET', undefined, a)).revision,
  beforeRace.revision + 1,
);
checks++;
const racingProposals = [];
for (const token of [a, b]) {
  const c = (
    await req(
      'branches',
      'POST',
      { world: 'conan', title: 'Concurrent proposal' },
      token,
      false,
      201,
    )
  ).id;
  const branch = await req('branches/' + c, 'GET', undefined, token);
  await req(
    'branches/' + c,
    'PUT',
    { revision: branch.revision, scene: branch.scene, publish: true },
    token,
  );
  racingProposals.push(
    (await req('proposals', 'POST', { branchId: c }, token, false, 201)).id,
  );
}
const merges = await Promise.all(
  racingProposals.map((pid) =>
    raceRequest(
      'proposals/' + pid + '/merge',
      'POST',
      { mainRevision: 'initial', resolutions: {} },
      a,
      true,
    ),
  ),
);
assert.deepEqual(merges.map((r) => r.status).sort(), [200, 409]);
assert.equal((await req('history/conan')).revisions.length, 1);
checks += 2;
// Later private titles cannot change or disclose a proposal's frozen public title.
const frozen = (await req('proposals/' + pa.id)).title;
let privateBranch = await req('branches/' + aid, 'GET', undefined, a);
await req(
  'branches/' + aid,
  'PUT',
  {
    revision: privateBranch.revision,
    scene: privateBranch.scene,
    title: 'SECRET PRIVATE TITLE',
  },
  a,
);
assert.equal((await req('proposals/' + pa.id)).title, frozen);
assert(
  !JSON.stringify(await req('proposals')).includes('SECRET PRIVATE TITLE'),
);
checks += 2;
await req('notes', 'POST', null, a, false, 400);
// Exercise the paid path with local fake providers; no real payment or model call occurs.
const paidEnv = {
  DB,
  PAID_AGENT_ENABLED: 'true',
  OPENAI_API_KEY: 'test-key',
  STRIPE_SECRET_KEY: 'test-stripe',
  STRIPE_WEBHOOK_SECRET: secret,
  AGENT_CREDIT_PRICE_ID: 'price_local_test',
  AGENT_CREDIT_MICROS: '10000000',
  AGENT_MARKUP_BPS: '10000',
};
const account =
  'account_' +
  Buffer.from(
    await crypto.subtle.digest(
      'SHA-256',
      new TextEncoder().encode('buyer@example.test'),
    ),
  ).toString('hex');
async function paid(path, method = 'GET', body, headers = {}) {
  const r = await billing.billingRoute(
    new Request('https://test.example/api/community/' + path, {
      method,
      headers: {
        'oai-authenticated-user-email': 'buyer@example.test',
        ...headers,
      },
      body:
        body === undefined
          ? undefined
          : typeof body === 'string'
            ? body
            : JSON.stringify(body),
    }),
    paidEnv,
    path,
  );
  return { status: r.status, json: await r.json() };
}
for (const type of [
  'checkout.session.completed',
  'checkout.session.async_payment_succeeded',
]) {
  const rawEvent = JSON.stringify({
    id: crypto.randomUUID(),
    type,
    data: {
      object: {
        id: 'cs_same_checkout',
        payment_status: 'paid',
        client_reference_id: account,
        metadata: {
          product: 'xlands-agent',
          price_id: 'price_local_test',
          credit_micros: '10000000',
        },
      },
    },
  });
  const sig = Buffer.from(
    await crypto.subtle.sign(
      'HMAC',
      hmac,
      new TextEncoder().encode(stamp + '.' + rawEvent),
    ),
  ).toString('hex');
  assert.equal(
    (
      await paid('billing/webhook', 'POST', rawEvent, {
        'stripe-signature': `t=${stamp},v1=${sig}`,
      })
    ).status,
    200,
  );
  checks++;
}
assert.equal((await paid('billing/balance')).json.balanceMicros, 10000000);
checks++;
const originalFetch = globalThis.fetch;
let providerCalls = 0,
  providerFails = false;
try {
  globalThis.fetch = async (url) => {
    assert.equal(url, 'https://api.openai.com/v1/responses');
    providerCalls++;
    return providerFails
      ? Response.json({ error: 'fake outage' }, { status: 500 })
      : Response.json({
          output: [
            {
              content: [
                {
                  type: 'output_text',
                  text: JSON.stringify({
                    summary: 'No changes needed',
                    operations: [],
                  }),
                },
              ],
            },
          ],
          usage: { input_tokens: 1000, output_tokens: 1000 },
        });
  };
  const request = {
    requestId: crypto.randomUUID(),
    prompt: 'Keep this peaceful garden.',
    locale: 'en',
    scene: base,
  };
  assert.equal((await paid('agent/plan', 'POST', request)).status, 200);
  assert.equal((await paid('agent/plan', 'POST', request)).status, 200);
  assert.equal(providerCalls, 1);
  assert.equal((await paid('billing/balance')).json.balanceMicros, 9940000);
  checks += 4;
  providerFails = true;
  assert.equal(
    (
      await paid('agent/plan', 'POST', {
        ...request,
        requestId: crypto.randomUUID(),
      })
    ).status,
    502,
  );
  assert.equal((await paid('billing/balance')).json.balanceMicros, 9940000);
  checks += 2;
} finally {
  globalThis.fetch = originalFetch;
}
const abandoned = crypto.randomUUID();
sqlite
  .prepare(
    'INSERT INTO agent_jobs (id,owner_id,request_hash,status,reserved_micros,created_at) VALUES (?,?,?,?,?,?)',
  )
  .run(
    abandoned,
    account,
    'local-test',
    'pending',
    2000000,
    Date.now() - 700000,
  );
sqlite
  .prepare(
    'UPDATE credits SET balance_micros=balance_micros-2000000 WHERE owner_id=?',
  )
  .run(account);
assert.equal((await paid('billing/balance')).json.balanceMicros, 9940000);
assert.equal((await paid('billing/balance')).json.balanceMicros, 9940000);
assert.equal(
  sqlite
    .prepare('SELECT count(*) n FROM ledger WHERE id=?')
    .get('settle:' + abandoned).n,
  1,
);
checks += 3;
// A world at the documented limit must still be editable and list cheaply.
const full = M.emptyScene('frog');
for (let z = 0; z < 8; z++)
  for (let x = 0; x < 8; x++) {
    const tile = 'tile_' + x + '_' + z;
    full.tiles[tile] = {
      id: tile,
      x,
      z,
      biome: 'grass',
      label: 'A shared garden',
    };
    for (let n = 0; n < 20; n++) {
      const id = 'item_' + x + '_' + z + '_' + n + '_' + 'a'.repeat(45);
      full.objects[id] = {
        id,
        tileId: tile,
        asset: 'flowers',
        position: { x: 1 + (n % 3) * 0.3, y: 0, z: 1 + (n % 4) * 0.3 },
        rotation: 0,
        color: '#a1b2c3',
        label: 'A small patch of flowers for the community.',
      };
    }
  }
assert.equal(M.validateScene(full).length, 0);
assert(JSON.stringify(full).length > 150000);
checks += 2;
const fullId = (
  await req(
    'branches',
    'POST',
    { world: 'frog', title: 'Full garden' },
    a,
    false,
    201,
  )
).id;
const fullBranch = await req('branches/' + fullId, 'GET', undefined, a);
await req(
  'branches/' + fullId,
  'PUT',
  {
    revision: fullBranch.revision,
    title: fullBranch.title,
    scene: full,
    publish: true,
  },
  a,
);
const publicList = await req('branches?world=frog');
assert.equal(publicList.branches.find((b) => b.id === fullId).tileCount, 64);
assert(JSON.stringify(publicList).length < 10000);
checks += 2;
await req('notes', 'POST', { padding: 'x'.repeat(1048577) }, a, false, 413);
console.log(
  JSON.stringify(
    {
      checks,
      passed: true,
      coverage: [
        'public email privacy',
        'note ownership',
        'private drafts',
        'published snapshot isolation',
        'fork ancestry',
        'immutable proposals',
        'role-gated merge',
        'three-way merge',
        'conflict choices',
        'stale revision rejection',
        'rollback history',
        'spatial overlap',
        'malformed scene',
        'prototype keys',
        'non-executable AI plans',
        'paid gate',
        'webhook integrity',
        'simultaneous draft writes',
        'simultaneous main merges',
        'proposal title privacy',
        'payment event deduplication',
        'generation replay',
        'failed generation refund',
        'abandoned reservation recovery',
        'maximum world size stays editable',
        'bounded gallery response',
      ],
    },
    null,
    2,
  ),
);
