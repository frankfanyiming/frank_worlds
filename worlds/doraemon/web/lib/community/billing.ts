import { agentRequest, readPlan, applyPlan } from './agent';
import { validateScene } from './merge';
type Env = {
  DB: any;
  OPENAI_API_KEY?: string;
  PAID_AGENT_ENABLED?: string;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  AGENT_CREDIT_PRICE_ID?: string;
  AGENT_CREDIT_MICROS?: string;
  AGENT_MARKUP_BPS?: string;
};
const digest = async (value: string) =>
  [
    ...new Uint8Array(
      await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)),
    ),
  ]
    .map((x) => x.toString(16).padStart(2, '0'))
    .join('');
const response = (data: unknown, status = 200) =>
  Response.json(data, { status });
export function paidEnabled(env: Env) {
  return (
    env.PAID_AGENT_ENABLED === 'true' &&
    !!env.OPENAI_API_KEY &&
    !!env.STRIPE_SECRET_KEY &&
    !!env.STRIPE_WEBHOOK_SECRET &&
    !!env.AGENT_CREDIT_PRICE_ID &&
    Number(env.AGENT_CREDIT_MICROS) > 0 &&
    Number(env.AGENT_MARKUP_BPS) >= 10000
  );
}
export function chargeMicros(input: number, output: number, bps: number) {
  return Math.ceil(((input * 10 + output * 50) * bps) / 10000);
}
// Reconcile abandoned reservations on the next account request. A generation times out
// after three minutes, so ten minutes gives settlement ample time without stranding credit.
async function releaseExpiredHolds(db: any, uid: string) {
  const rows = (
    await db
      .prepare(
        'SELECT id,reserved_micros FROM agent_jobs WHERE owner_id=? AND status=? AND created_at<? LIMIT 20',
      )
      .bind(uid, 'pending', Date.now() - 600000)
      .all()
  ).results;
  for (const row of rows)
    await db.batch([
      db
        .prepare(
          'UPDATE credits SET balance_micros=balance_micros+? WHERE owner_id=? AND EXISTS(SELECT 1 FROM agent_jobs WHERE id=? AND status=?)',
        )
        .bind(row.reserved_micros, uid, row.id, 'pending'),
      db
        .prepare(
          'INSERT OR IGNORE INTO ledger (id,owner_id,amount_micros,kind,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM agent_jobs WHERE id=? AND status=?)',
        )
        .bind(
          'settle:' + row.id,
          uid,
          row.reserved_micros,
          'expired-refund',
          Date.now(),
          row.id,
          'pending',
        ),
      db
        .prepare(
          'UPDATE agent_jobs SET status=?,cost_micros=0 WHERE id=? AND status=?',
        )
        .bind('failed', row.id, 'pending'),
    ]);
}
export async function validStripeSignature(
  raw: string,
  header: string,
  secret: string,
  time = Date.now(),
) {
  const fields = header.split(',').map((x) => x.split('='));
  const timestamp = fields.find(([k]) => k === 't')?.[1];
  const candidates = fields.filter(([k]) => k === 'v1').map(([, v]) => v);
  if (
    !timestamp ||
    !Number.isFinite(Number(timestamp)) ||
    Math.abs(time / 1000 - Number(timestamp)) > 300
  )
    return false;
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const expected = [
    ...new Uint8Array(
      await crypto.subtle.sign(
        'HMAC',
        key,
        new TextEncoder().encode(timestamp + '.' + raw),
      ),
    ),
  ]
    .map((x) => x.toString(16).padStart(2, '0'))
    .join('');
  return candidates.some((value) => {
    if (value.length !== expected.length) return false;
    let diff = 0;
    for (let i = 0; i < value.length; i++)
      diff |= value.charCodeAt(i) ^ expected.charCodeAt(i);
    return diff === 0;
  });
}
export async function billingRoute(
  request: Request,
  env: Env,
  path: string,
): Promise<Response> {
  if (!paidEnabled(env)) return response({ error: 'AGENT_UNAVAILABLE' }, 503);
  const db = env.DB;
  if (path === 'billing/webhook' && request.method === 'POST') {
    const raw = await request.text();
    if (
      raw.length > 500000 ||
      !(await validStripeSignature(
        raw,
        request.headers.get('stripe-signature') || '',
        env.STRIPE_WEBHOOK_SECRET!,
      ))
    )
      return response({ error: 'INVALID_SIGNATURE' }, 400);
    let event: any;
    try {
      event = JSON.parse(raw);
    } catch {
      return response({ error: 'INVALID_INPUT' }, 400);
    }
    if (
      ![
        'checkout.session.completed',
        'checkout.session.async_payment_succeeded',
      ].includes(event.type)
    )
      return response({ received: true });
    const session = event.data?.object;
    if (
      session?.payment_status !== 'paid' ||
      session.metadata?.product !== 'xlands-agent'
    )
      return response({ received: true });
    const uid = session.client_reference_id,
      amount = Number(session.metadata.credit_micros);
    if (
      !/^account_[a-f0-9]{64}$/.test(uid) ||
      !Number.isSafeInteger(amount) ||
      amount <= 0 ||
      session.metadata.price_id !== env.AGENT_CREDIT_PRICE_ID
    )
      return response({ error: 'INVALID_INPUT' }, 400);
    // Both Stripe event types can describe the same checkout: key the ledger by session, not event.
    const ledger = 'checkout:' + session.id;
    await db
      .prepare(
        'INSERT OR IGNORE INTO credits (owner_id,balance_micros) VALUES (?,0)',
      )
      .bind(uid)
      .run();
    await db.batch([
      db
        .prepare(
          'UPDATE credits SET balance_micros=balance_micros+? WHERE owner_id=? AND NOT EXISTS(SELECT 1 FROM ledger WHERE id=?)',
        )
        .bind(amount, uid, ledger),
      db
        .prepare(
          'INSERT OR IGNORE INTO ledger (id,owner_id,amount_micros,kind,created_at) VALUES (?,?,?,?,?)',
        )
        .bind(ledger, uid, amount, 'credit', Date.now()),
    ]);
    return response({ received: true });
  }
  const email = request.headers.get('oai-authenticated-user-email');
  if (!email) return response({ error: 'SIGN_IN_REQUIRED' }, 401);
  const uid = 'account_' + (await digest(email.toLowerCase())),
    markup = Number(env.AGENT_MARKUP_BPS),
    reserve = chargeMicros(160000, 6000, markup);
  await releaseExpiredHolds(db, uid);
  if (path === 'billing/balance' && request.method === 'GET') {
    const row = await db
      .prepare('SELECT balance_micros FROM credits WHERE owner_id=?')
      .bind(uid)
      .first();
    return response({
      balanceMicros: row?.balance_micros || 0,
      maxRequestMicros: reserve,
      currency: 'USD',
      model: 'gpt-6-astra',
      markupBps: markup,
    });
  }
  let b: any;
  try {
    const raw = await request.text();
    if (raw.length > 150000) return response({ error: 'INVALID_INPUT' }, 413);
    b = JSON.parse(raw || '{}');
  } catch {
    return response({ error: 'INVALID_INPUT' }, 400);
  }
  if (path === 'billing/checkout' && request.method === 'POST') {
    const origin = new URL(request.url).origin;
    const params = new URLSearchParams({
      mode: 'payment',
      client_reference_id: uid,
      'line_items[0][price]': env.AGENT_CREDIT_PRICE_ID!,
      'line_items[0][quantity]': '1',
      success_url: origin + '/?payment=complete#agent',
      cancel_url: origin + '/#agent',
      'metadata[product]': 'xlands-agent',
      'metadata[credit_micros]': env.AGENT_CREDIT_MICROS!,
      'metadata[price_id]': env.AGENT_CREDIT_PRICE_ID!,
    });
    const result = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + env.STRIPE_SECRET_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
      signal: AbortSignal.timeout(20000),
    });
    if (!result.ok) return response({ error: 'PAYMENT_UNAVAILABLE' }, 503);
    const value: any = await result.json();
    return response({ url: value.url });
  }
  if (path !== 'agent/plan' || request.method !== 'POST')
    return response({ error: 'NOT_FOUND' }, 404);
  if (
    !b ||
    !/^[-a-f0-9]{36}$/.test(b.requestId) ||
    typeof b.prompt !== 'string' ||
    b.prompt.length > 2000 ||
    validateScene(b.scene).length
  )
    return response({ error: 'INVALID_INPUT' }, 422);
  const payload = agentRequest(
      b.scene,
      b.prompt,
      'gpt-6-astra',
      String(b.locale || 'en'),
    ),
    payloadText = JSON.stringify(payload);
  if (new TextEncoder().encode(payloadText).length > 150000)
    return response({ error: 'SCENE_LIMIT' }, 422);
  const requestHash = await digest(payloadText),
    old = await db
      .prepare('SELECT * FROM agent_jobs WHERE id=?')
      .bind(b.requestId)
      .first();
  if (old) {
    if (old.owner_id !== uid || old.request_hash !== requestHash)
      return response({ error: 'STALE' }, 409);
    return old.status === 'complete'
      ? response(JSON.parse(old.result))
      : response(
          { error: old.status === 'pending' ? 'AGENT_BUSY' : 'API_FAILED' },
          409,
        );
  }
  // The debit and job insert share a transaction. Insufficient funds never trigger a provider request.
  const hold = await db.batch([
    db
      .prepare(
        'INSERT INTO agent_jobs (id,owner_id,request_hash,status,reserved_micros,created_at) SELECT ?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM credits WHERE owner_id=? AND balance_micros>=?)',
      )
      .bind(
        b.requestId,
        uid,
        requestHash,
        'pending',
        reserve,
        Date.now(),
        uid,
        reserve,
      ),
    db
      .prepare(
        'UPDATE credits SET balance_micros=balance_micros-? WHERE owner_id=? AND EXISTS(SELECT 1 FROM agent_jobs WHERE id=?)',
      )
      .bind(reserve, uid, b.requestId),
    db
      .prepare(
        'INSERT INTO ledger (id,owner_id,amount_micros,kind,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM agent_jobs WHERE id=?)',
      )
      .bind(
        'hold:' + b.requestId,
        uid,
        -reserve,
        'hold',
        Date.now(),
        b.requestId,
      ),
  ]);
  if (hold[0].meta.changes !== 1)
    return response({ error: 'INSUFFICIENT_CREDIT' }, 402);
  let plan: any,
    cost = 0,
    success = false;
  try {
    const r = await fetch('https://api.openai.com/v1/responses', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + env.OPENAI_API_KEY,
        'Content-Type': 'application/json',
      },
      body: payloadText,
      signal: AbortSignal.timeout(180000),
    });
    if (!r.ok) throw Error();
    const result: any = await r.json();
    plan = readPlan(result);
    applyPlan(b.scene, plan);
    if (
      !Number.isSafeInteger(result.usage?.input_tokens) ||
      result.usage.input_tokens < 0 ||
      !Number.isSafeInteger(result.usage?.output_tokens) ||
      result.usage.output_tokens < 0
    )
      throw Error();
    cost = Math.min(
      reserve,
      chargeMicros(
        result.usage.input_tokens,
        result.usage.output_tokens,
        markup,
      ),
    );
    success = true;
  } catch {
    /* Failed or invalid plans are refunded; any upstream cost belongs to the platform. */
  }
  const settled = await db.batch([
    db
      .prepare(
        'UPDATE credits SET balance_micros=balance_micros+? WHERE owner_id=? AND EXISTS(SELECT 1 FROM agent_jobs WHERE id=? AND status=?)',
      )
      .bind(reserve - cost, uid, b.requestId, 'pending'),
    db
      .prepare(
        'INSERT OR IGNORE INTO ledger (id,owner_id,amount_micros,kind,created_at) SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM agent_jobs WHERE id=? AND status=?)',
      )
      .bind(
        'settle:' + b.requestId,
        uid,
        reserve - cost,
        success ? 'settle' : 'refund',
        Date.now(),
        b.requestId,
        'pending',
      ),
    db
      .prepare(
        'UPDATE agent_jobs SET status=?,cost_micros=?,result=? WHERE id=? AND status=?',
      )
      .bind(
        success ? 'complete' : 'failed',
        cost,
        success ? JSON.stringify(plan) : null,
        b.requestId,
        'pending',
      ),
  ]);
  if (settled[2].meta.changes !== 1)
    return response({ error: 'API_FAILED' }, 502);
  return success ? response(plan) : response({ error: 'API_FAILED' }, 502);
}
