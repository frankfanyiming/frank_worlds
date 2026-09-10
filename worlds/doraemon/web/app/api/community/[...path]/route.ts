import { env } from 'cloudflare:workers';
import { handleCommunity } from '@/lib/community/server';
export const dynamic = 'force-dynamic';
export const GET = (request: Request) => handleCommunity(request, env as any);
export const POST = GET;
export const PUT = GET;
export const DELETE = GET;
export const OPTIONS = GET;
