import { billingRoute, paidEnabled } from './billing';
import {
  emptyScene,
  addTile,
  mergeScenes,
  validateScene,
  sceneSummary,
  type World,
  type Scene,
} from './merge';
type Db = {
  prepare: (query: string) => any;
  batch: (statements: any[]) => Promise<any[]>;
};
type Env = {
  DB: Db;
  OWNER_ACCOUNT_EMAIL?: string;
  OPENAI_API_KEY?: string;
  PAID_AGENT_ENABLED?: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  AGENT_CREDIT_PRICE_ID?: string;
  AGENT_CREDIT_MICROS?: string;
  AGENT_MARKUP_BPS?: string;
  COMPANY_URL?: string;
};
const worlds = ['doraemon', 'frog', 'conan'];
const now = () => Date.now();
const id = () => crypto.randomUUID();
class HttpError extends Error {
  constructor(
    public code: string,
    public status = 400,
    public details: unknown = null,
  ) {
    super(code);
  }
}
const required = (condition: unknown, code = 'INVALID_INPUT', status = 400) => {
  if (!condition) throw new HttpError(code, status);
};
async function hash(input: string) {
  return [
    ...new Uint8Array(
      await crypto.subtle.digest('SHA-256', new TextEncoder().encode(input)),
    ),
  ]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
const json = (data: unknown, status = 200) => Response.json(data, { status });
const clean = (v: unknown, n: number) =>
  typeof v === 'string' ? v.trim().slice(0, n) : '';
async function bodyOf(request: Request) {
  const raw = await request.text();
  required(raw.length <= 150000, 'INVALID_INPUT', 413);
  let value: unknown;
  try {
    value = JSON.parse(raw || '{}');
  } catch {
    throw new HttpError('INVALID_INPUT');
  }
  required(value && typeof value === 'object' && !Array.isArray(value));
  return value as Record<string, any>;
}
async function owner(request: Request, db: Db) {
  const token = request.headers.get('X-Visitor-Token') || '';
  required(/^[0-9a-f]{64}$/.test(token), 'UNAUTHORIZED', 401);
  const row = await db
    .prepare('SELECT id FROM visitors WHERE token_hash = ?')
    .bind(await hash(token))
    .first();
  required(row, 'UNAUTHORIZED', 401);
  return row.id as string;
}
function admin(request: Request, env: Env) {
  const email = request.headers.get('oai-authenticated-user-email');
  return (
    !!env.OWNER_ACCOUNT_EMAIL &&
    email?.toLowerCase() === env.OWNER_ACCOUNT_EMAIL.toLowerCase()
  );
}
async function main(db: Db, world: World) {
  required(worlds.includes(world));
  const row = await db
    .prepare('SELECT * FROM main_heads WHERE world = ?')
    .bind(world)
    .first();
  return row
    ? { revision: row.revision, scene: JSON.parse(row.data) as Scene }
    : { revision: 'initial', scene: emptyScene(world) };
}
const validScene = (scene: unknown) => {
  const errors = validateScene(scene);
  if (errors.length) throw new HttpError(errors[0], 422, errors);
};
const requireOwner = (row: any, uid: string) =>
  required(row && row.owner_id === uid, 'UNAUTHORIZED', 403);
async function limited(
  db: Db,
  uid: string,
  table: 'notes' | 'branches',
  limit: number,
) {
  const count = await db
    .prepare(
      `SELECT count(*) n FROM ${table} WHERE owner_id = ? AND created_at > ?`,
    )
    .bind(uid, now() - 600000)
    .first();
  required(count.n < limit, 'RATE_LIMIT', 429);
}
const publicBranch = (r: any, uid?: string) => ({
  id: r.id,
  world: r.world,
  title: r.owner_id === uid ? r.title : r.published_title || r.title,
  sourceId: r.source_id,
  revision: r.owner_id === uid ? r.revision : r.published_revision,
  published: r.published_revision !== null,
  updatedAt: r.updated_at,
  owned: r.owner_id === uid,
  tileCount: Object.keys(
    JSON.parse(
      (r.owner_id === uid ? r.data : r.published_data) || '{"tiles":{}}',
    ).tiles,
  ).length,
});
export async function handleCommunity(
  request: Request,
  env: Env,
): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname.split('/api/community/')[1] || '';
  const db = env.DB;
  const allowedOrigins = ['https://frankfanyiming.github.io', url.origin];
  const origin = request.headers.get('Origin') || '';
  const local = /^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin);
  const allowed = !origin || allowedOrigins.includes(origin) || local;
  const cors: Record<string, string> = {
    Vary: 'Origin',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  };
  if (allowed && origin) {
    cors['Access-Control-Allow-Origin'] = origin;
    cors['Access-Control-Allow-Headers'] = 'Content-Type, X-Visitor-Token';
    cors['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
  }
  if (request.method === 'OPTIONS')
    return new Response(null, { status: allowed ? 204 : 403, headers: cors });
  let response: Response;
  try {
    required(allowed, 'UNAUTHORIZED', 403);
    required(db, 'NOT_CONFIGURED', 503);
    let uid = '';
    if (request.headers.get('X-Visitor-Token')) uid = await owner(request, db);
    if (path.startsWith('billing/') || path === 'agent/plan')
      response = await billingRoute(request, env, path);
    else if (path === 'meta')
      response = json({
        model: 'gpt-6-astra',
        hostedAgentEnabled: paidEnabled(env),
        companyUrl: env.COMPANY_URL || null,
        admin: admin(request, env),
      });
    else if (path === 'session' && request.method === 'POST') {
      const ip = request.headers.get('CF-Connecting-IP') || 'local';
      const ipHash = await hash(ip + ':xlands-session');
      const count = await db
        .prepare(
          'SELECT count(*) n FROM visitors WHERE ip_hash = ? AND created_at > ?',
        )
        .bind(ipHash, now() - 3600000)
        .first();
      required(count.n < 20, 'RATE_LIMIT', 429);
      const token = [...crypto.getRandomValues(new Uint8Array(32))]
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
      await db
        .prepare(
          'INSERT INTO visitors (id,token_hash,ip_hash,created_at) VALUES (?,?,?,?)',
        )
        .bind(id(), await hash(token), ipHash, now())
        .run();
      response = json({ token }, 201);
    } else if (path === 'notes' && request.method === 'GET') {
      const world = url.searchParams.get('world');
      const rows = await db
        .prepare(
          'SELECT id,owner_id,world,nickname,body,created_at FROM notes WHERE (? IS NULL OR world = ?) ORDER BY created_at DESC LIMIT 60',
        )
        .bind(world, world)
        .all();
      response = json({
        notes: rows.results.map((r: any) => ({
          id: r.id,
          world: r.world,
          nickname: r.nickname,
          body: r.body,
          createdAt: r.created_at,
          owned: uid === r.owner_id,
        })),
      });
    } else if (path === 'notes' && request.method === 'POST') {
      required(uid, 'UNAUTHORIZED', 401);
      const b = await bodyOf(request);
      const body = clean(b.body, 500),
        email = clean(b.email, 254);
      required(!b.website && body.length > 0 && worlds.includes(b.world));
      if (email)
        required(
          /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && b.contactConsent === true,
          'INVALID_EMAIL',
        );
      await limited(db, uid, 'notes', 5);
      const nid = id(),
        stamp = now();
      const statements = [
        db
          .prepare(
            'INSERT INTO notes (id,owner_id,world,nickname,body,created_at) VALUES (?,?,?,?,?,?)',
          )
          .bind(
            nid,
            uid,
            b.world,
            clean(b.nickname, 30) || 'Traveler',
            body,
            stamp,
          ),
      ];
      if (email)
        statements.push(
          db
            .prepare(
              'INSERT INTO contacts (note_id,email,consent_at) VALUES (?,?,?)',
            )
            .bind(nid, email, stamp),
        );
      await db.batch(statements);
      response = json({ id: nid }, 201);
    } else if (path.startsWith('notes/') && request.method === 'DELETE') {
      required(uid, 'UNAUTHORIZED', 401);
      const nid = path.split('/')[1];
      const row = await db
        .prepare('SELECT owner_id FROM notes WHERE id = ?')
        .bind(nid)
        .first();
      required(
        row && (row.owner_id === uid || admin(request, env)),
        'UNAUTHORIZED',
        403,
      );
      await db.batch([
        db.prepare('DELETE FROM contacts WHERE note_id = ?').bind(nid),
        db.prepare('DELETE FROM notes WHERE id = ?').bind(nid),
      ]);
      response = json({ ok: true });
    } else if (path === 'contacts' && request.method === 'GET') {
      required(admin(request, env), 'ADMIN_REQUIRED', 403);
      response = json({
        contacts: (
          await db
            .prepare(
              'SELECT c.note_id,c.email,c.consent_at,n.body,n.nickname FROM contacts c JOIN notes n ON n.id=c.note_id ORDER BY c.consent_at DESC LIMIT 100',
            )
            .all()
        ).results,
      });
    } else if (path.startsWith('main/') && request.method === 'GET') {
      const world = path.split('/')[1] as World;
      response = json(await main(db, world));
    } else if (path === 'branches' && request.method === 'GET') {
      const world = url.searchParams.get('world');
      const mine = url.searchParams.get('mine') === '1';
      if (mine) required(uid, 'UNAUTHORIZED', 401);
      const rows = await db
        .prepare(
          'SELECT id,owner_id,world,title,source_id,revision,published_revision,published_title,published_data,data,updated_at FROM branches WHERE (? IS NULL OR world = ?) AND ((? = 1 AND owner_id = ?) OR (? = 0 AND published_revision IS NOT NULL)) ORDER BY updated_at DESC LIMIT 60',
        )
        .bind(world, world, mine ? 1 : 0, uid, mine ? 1 : 0)
        .all();
      response = json({
        branches: rows.results.map((r: any) => publicBranch(r, uid)),
      });
    } else if (path === 'branches' && request.method === 'POST') {
      required(uid, 'UNAUTHORIZED', 401);
      const b = await bodyOf(request);
      required(worlds.includes(b.world));
      await limited(db, uid, 'branches', 10);
      const root = await main(db, b.world);
      let scene = root.scene,
        base = root.scene,
        baseRevision = root.revision;
      let sourceId = null;
      if (b.sourceId) {
        const source = await db
          .prepare('SELECT * FROM branches WHERE id = ? AND world = ?')
          .bind(b.sourceId, b.world)
          .first();
        required(
          source && (source.published_data || source.owner_id === uid),
          'UNAUTHORIZED',
          403,
        );
        const mine = source.owner_id === uid;
        scene = JSON.parse(mine ? source.data : source.published_data);
        base = JSON.parse(mine ? source.base_data : source.published_base_data);
        baseRevision = mine
          ? source.base_revision
          : source.published_base_revision;
        sourceId = source.id;
      }
      if (!b.sourceId) scene = addTile(scene, clean(b.title, 60));
      validScene(scene);
      const bid = id(),
        title = clean(b.title, 60) || 'Untitled',
        stamp = now();
      await db.batch([
        db
          .prepare(
            'INSERT INTO branches (id,owner_id,world,title,source_id,base_revision,base_data,revision,data,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
          )
          .bind(
            bid,
            uid,
            b.world,
            title,
            sourceId,
            baseRevision,
            JSON.stringify(base),
            1,
            JSON.stringify(scene),
            stamp,
            stamp,
          ),
        db
          .prepare(
            'INSERT INTO branch_versions (id,branch_id,revision,data,created_at) VALUES (?,?,?,?,?)',
          )
          .bind(id(), bid, 1, JSON.stringify(scene), stamp),
      ]);
      response = json({ id: bid }, 201);
    } else if (/^branches\/[^/]+$/.test(path) && request.method === 'GET') {
      const row = await db
        .prepare('SELECT * FROM branches WHERE id = ?')
        .bind(path.split('/')[1])
        .first();
      required(
        row && (row.owner_id === uid || row.published_data),
        'NOT_FOUND',
        404,
      );
      response = json({
        ...publicBranch(row, uid),
        scene: JSON.parse(row.owner_id === uid ? row.data : row.published_data),
        base: JSON.parse(
          row.owner_id === uid ? row.base_data : row.published_base_data,
        ),
        baseRevision:
          row.owner_id === uid
            ? row.base_revision
            : row.published_base_revision,
      });
    } else if (/^branches\/[^/]+$/.test(path) && request.method === 'PUT') {
      required(uid, 'UNAUTHORIZED', 401);
      const bid = path.split('/')[1],
        b = await bodyOf(request);
      const row = await db
        .prepare('SELECT * FROM branches WHERE id = ?')
        .bind(bid)
        .first();
      requireOwner(row, uid);
      required(b.revision === row.revision, 'STALE', 409);
      required(b.scene?.world === row.world);
      validScene(b.scene);
      const data = JSON.stringify(b.scene),
        next = row.revision + 1,
        stamp = now();
      const result = await db.batch([
        db
          .prepare(
            'INSERT INTO branch_versions (id,branch_id,revision,data,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM branches WHERE id=? AND revision=?)',
          )
          .bind(id(), bid, next, data, stamp, bid, b.revision),
        db
          .prepare(
            'UPDATE branches SET title=?,data=?,revision=?,updated_at=?,published_data=CASE WHEN ?=1 THEN ? ELSE published_data END,published_revision=CASE WHEN ?=1 THEN ? ELSE published_revision END,published_base_data=CASE WHEN ?=1 THEN base_data ELSE published_base_data END,published_base_revision=CASE WHEN ?=1 THEN base_revision ELSE published_base_revision END,published_title=CASE WHEN ?=1 THEN ? ELSE published_title END WHERE id=? AND owner_id=? AND revision=?',
          )
          .bind(
            clean(b.title, 60) || row.title,
            data,
            next,
            stamp,
            b.publish ? 1 : 0,
            data,
            b.publish ? 1 : 0,
            next,
            b.publish ? 1 : 0,
            b.publish ? 1 : 0,
            b.publish ? 1 : 0,
            clean(b.title, 60) || row.title,
            bid,
            uid,
            b.revision,
          ),
      ]);
      required(result[1].meta.changes === 1, 'STALE', 409);
      response = json({ revision: next });
    } else if (
      /^branches\/[^/]+\/sync$/.test(path) &&
      request.method === 'POST'
    ) {
      required(uid, 'UNAUTHORIZED', 401);
      const bid = path.split('/')[1],
        b = await bodyOf(request);
      const row = await db
        .prepare('SELECT * FROM branches WHERE id = ?')
        .bind(bid)
        .first();
      requireOwner(row, uid);
      required(b.revision === row.revision, 'STALE', 409);
      const root = await main(db, row.world);
      if (b.mainRevision)
        required(b.mainRevision === root.revision, 'STALE', 409);
      const merged = mergeScenes(
        JSON.parse(row.base_data),
        root.scene,
        JSON.parse(row.data),
        b.resolutions || {},
      );
      if (merged.unresolved.length)
        response = json(
          {
            error: 'CONFLICT',
            details: { ...merged, mainRevision: root.revision },
          },
          409,
        );
      else {
        validScene(merged.scene);
        const next = row.revision + 1,
          data = JSON.stringify(merged.scene);
        const result = await db.batch([
          db
            .prepare(
              'INSERT INTO branch_versions (id,branch_id,revision,data,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM branches WHERE id=? AND revision=?)',
            )
            .bind(id(), bid, next, data, now(), bid, b.revision),
          db
            .prepare(
              'UPDATE branches SET data=?,revision=?,base_revision=?,base_data=?,updated_at=? WHERE id=? AND revision=?',
            )
            .bind(
              data,
              next,
              root.revision,
              JSON.stringify(root.scene),
              now(),
              bid,
              b.revision,
            ),
        ]);
        required(result[1].meta.changes === 1, 'STALE', 409);
        response = json({ revision: next });
      }
    } else if (path === 'proposals' && request.method === 'POST') {
      required(uid, 'UNAUTHORIZED', 401);
      const b = await bodyOf(request);
      const row = await db
        .prepare('SELECT * FROM branches WHERE id=?')
        .bind(b.branchId)
        .first();
      requireOwner(row, uid);
      required(row.published_revision === row.revision, 'PUBLISH_FIRST', 409);
      validScene(JSON.parse(row.data));
      const existing = await db
        .prepare(
          'SELECT id FROM proposals WHERE branch_id=? AND branch_revision=?',
        )
        .bind(row.id, row.revision)
        .first();
      if (existing) response = json({ id: existing.id });
      else {
        const pid = id();
        await db
          .prepare(
            'INSERT INTO proposals (id,branch_id,owner_id,world,title,branch_revision,base_revision,base_data,data,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
          )
          .bind(
            pid,
            row.id,
            uid,
            row.world,
            row.title,
            row.revision,
            row.base_revision,
            row.base_data,
            row.data,
            'open',
            now(),
          )
          .run();
        response = json({ id: pid }, 201);
      }
    } else if (path === 'proposals' && request.method === 'GET') {
      const world = url.searchParams.get('world');
      response = json({
        proposals: (
          await db
            .prepare(
              'SELECT p.id,p.branch_id,p.world,p.status,p.branch_revision,p.created_at,COALESCE(p.title,b.published_title) title FROM proposals p JOIN branches b ON b.id=p.branch_id WHERE (? IS NULL OR p.world=?) ORDER BY p.created_at DESC LIMIT 80',
            )
            .bind(world, world)
            .all()
        ).results,
      });
    } else if (/^proposals\/[^/]+$/.test(path) && request.method === 'GET') {
      const row = await db
        .prepare(
          'SELECT p.*,COALESCE(p.title,b.published_title) title FROM proposals p JOIN branches b ON b.id=p.branch_id WHERE p.id=?',
        )
        .bind(path.split('/')[1])
        .first();
      required(row, 'NOT_FOUND', 404);
      const root = await main(db, row.world);
      const base = JSON.parse(row.base_data),
        scene = JSON.parse(row.data);
      response = json({
        id: row.id,
        title: row.title,
        world: row.world,
        status: row.status,
        base,
        branchScene: scene,
        main: root.scene,
        mainRevision: root.revision,
        branchRevision: row.branch_revision,
        summary: sceneSummary(base, scene),
        ...mergeScenes(base, root.scene, scene),
      });
    } else if (
      /^proposals\/[^/]+\/merge$/.test(path) &&
      request.method === 'POST'
    ) {
      required(admin(request, env), 'ADMIN_REQUIRED', 403);
      const b = await bodyOf(request),
        pid = path.split('/')[1];
      const row = await db
        .prepare('SELECT * FROM proposals WHERE id=?')
        .bind(pid)
        .first();
      required(row?.status === 'open', 'STALE', 409);
      const root = await main(db, row.world);
      required(root.revision === b.mainRevision, 'STALE', 409);
      const merged = mergeScenes(
        JSON.parse(row.base_data),
        root.scene,
        JSON.parse(row.data),
        b.resolutions || {},
      );
      required(!merged.unresolved.length, 'CONFLICT', 409);
      validScene(merged.scene);
      const rid = id(),
        data = JSON.stringify(merged.scene),
        stamp = now();
      await db
        .prepare(
          'INSERT OR IGNORE INTO main_heads (world,revision,data,updated_at) VALUES (?,?,?,?)',
        )
        .bind(
          row.world,
          'initial',
          JSON.stringify(emptyScene(row.world)),
          stamp,
        )
        .run();
      const results = await db.batch([
        db
          .prepare(
            'INSERT INTO revisions (id,world,parent_id,proposal_id,data,created_at) SELECT ?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM main_heads WHERE world=? AND revision=?) AND EXISTS(SELECT 1 FROM proposals WHERE id=? AND status=?)',
          )
          .bind(
            rid,
            row.world,
            root.revision,
            pid,
            data,
            stamp,
            row.world,
            b.mainRevision,
            pid,
            'open',
          ),
        db
          .prepare(
            'UPDATE main_heads SET revision=?,data=?,updated_at=? WHERE world=? AND revision=? AND EXISTS(SELECT 1 FROM revisions WHERE id=?)',
          )
          .bind(rid, data, stamp, row.world, b.mainRevision, rid),
        db
          .prepare(
            'UPDATE proposals SET status=?,merged_revision=? WHERE id=? AND EXISTS(SELECT 1 FROM revisions WHERE id=?)',
          )
          .bind('merged', rid, pid, rid),
      ]);
      required(results[1].meta.changes === 1, 'STALE', 409);
      response = json({ revision: rid });
    } else if (path.startsWith('history/') && request.method === 'GET') {
      response = json({
        revisions: (
          await db
            .prepare(
              'SELECT id,parent_id,proposal_id,created_at FROM revisions WHERE world=? ORDER BY created_at DESC LIMIT 50',
            )
            .bind(path.split('/')[1])
            .all()
        ).results,
      });
    } else if (path === 'rollback' && request.method === 'POST') {
      required(admin(request, env), 'ADMIN_REQUIRED', 403);
      const b = await bodyOf(request),
        root = await main(db, b.world);
      required(root.revision === b.mainRevision, 'STALE', 409);
      const old = await db
        .prepare('SELECT data FROM revisions WHERE id=? AND world=?')
        .bind(b.revision, b.world)
        .first();
      required(old, 'NOT_FOUND', 404);
      validScene(JSON.parse(old.data));
      const rid = id(),
        stamp = now();
      const result = await db.batch([
        db
          .prepare(
            'INSERT INTO revisions (id,world,parent_id,data,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM main_heads WHERE world=? AND revision=?)',
          )
          .bind(
            rid,
            b.world,
            root.revision,
            old.data,
            stamp,
            b.world,
            root.revision,
          ),
        db
          .prepare(
            'UPDATE main_heads SET revision=?,data=?,updated_at=? WHERE world=? AND revision=?',
          )
          .bind(rid, old.data, stamp, b.world, root.revision),
      ]);
      required(result[1].meta.changes === 1, 'STALE', 409);
      response = json({ revision: rid });
    } else response = json({ error: 'NOT_FOUND' }, 404);
  } catch (e) {
    const known = e instanceof HttpError;
    response = json(
      {
        error: known ? e.code : 'SERVICE_UNAVAILABLE',
        details: known ? e.details : null,
      },
      known ? e.status : 503,
    );
  }
  for (const [k, v] of Object.entries(cors)) response.headers.set(k, v);
  return response;
}
