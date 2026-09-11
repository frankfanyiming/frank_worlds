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
async function requestJson(url: string, options: RequestInit = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    // An upstream protection page is not a valid API response, even with status 200.
    if (!response.headers.get('Content-Type')?.includes('application/json'))
      throw new ApiError('NETWORK', response.status);
    const json: any = await response.json();
    if (!json || typeof json !== 'object') throw new ApiError('NETWORK', response.status);
    return { response, json };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('NETWORK', 0);
  } finally {
    clearTimeout(timer);
  }
}
export async function apiBase() {
  if (!basePromise)
    basePromise = requestJson(assetPath('community-config.json'))
      .then(({ response, json }) => {
        if (!response.ok) throw new ApiError('NETWORK', response.status);
        return json.apiOrigin || '';
      })
      .catch((error) => {
        basePromise = undefined;
        throw error;
      });
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
      const { response, json } = await requestJson(origin + '/api/community/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
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
  const token = visitorToken();
  const { response, json } = await requestJson(origin + '/api/community/' + path, {
      method,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { 'X-Visitor-Token': token } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials:
        origin && new URL(origin).origin !== location.origin
          ? 'omit'
          : 'same-origin',
    });
  if (response.status === 401 && json.error === 'UNAUTHORIZED') {
    localStorage.removeItem('xlands-visitor-token');
    throw new ApiError('UNAUTHORIZED', 401);
  }
  if (!response.ok)
    throw new ApiError(json.error || 'FAILED', response.status, json.details);
  return json as T;
}
