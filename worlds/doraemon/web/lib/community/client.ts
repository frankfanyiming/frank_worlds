import { assetPath } from '../town/asset-path';
export class ApiError extends Error {
  constructor(
    public code: string,
    public status = 400,
    public details: unknown = null,
  ) {
    super(code);
  }
}
let basePromise: Promise<string> | undefined;
export async function apiBase() {
  if (!basePromise)
    basePromise = fetch(assetPath('community-config.json'))
      .then((r) => (r.ok ? r.json() : {}))
      .then((c: any) => c.apiOrigin || '')
      .catch(() => '');
  return basePromise;
}
export function visitorToken() {
  try {
    return localStorage.getItem('xlands-visitor-token') || '';
  } catch {
    return '';
  }
}
let sessionPromise: Promise<void> | undefined;
async function ensureSession() {
  if (visitorToken()) return;
  if (!sessionPromise)
    sessionPromise = (async () => {
      const origin = await apiBase();
      const response = await fetch(origin + '/api/community/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      const json: any = await response.json();
      if (!response.ok)
        throw new ApiError(json.error || 'NOT_CONFIGURED', response.status);
      localStorage.setItem('xlands-visitor-token', json.token);
    })().finally(() => {
      sessionPromise = undefined;
    });
  return sessionPromise;
}
export async function api<T = any>(
  path: string,
  method = 'GET',
  body?: unknown,
): Promise<T> {
  if (method !== 'GET') await ensureSession();
  const origin = await apiBase();
  let response: Response;
  try {
    response = await fetch(origin + '/api/community/' + path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Visitor-Token': visitorToken(),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials:
        origin && new URL(origin).origin !== location.origin
          ? 'omit'
          : 'same-origin',
    });
  } catch {
    throw new ApiError('NETWORK', 0);
  }
  const json: any = await response
    .json()
    .catch(() => ({ error: 'NOT_CONFIGURED' }));
  if (response.status === 401 && json.error === 'UNAUTHORIZED') {
    localStorage.removeItem('xlands-visitor-token');
    throw new ApiError('UNAUTHORIZED', 401);
  }
  if (!response.ok)
    throw new ApiError(json.error || 'FAILED', response.status, json.details);
  return json as T;
}
