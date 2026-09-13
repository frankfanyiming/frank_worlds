// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
import type { World } from './merge';
type Event = {name: string; data: {world: World; load_ms?: number; reason?: string}};
declare global {
  interface Window {
    xlandsAnalytics?: {event: (name: string, data: Event['data']) => void};
    __xlandsAnalyticsEvents?: Event[];
  }
}
function track(name: string, data: Event['data']) {
  try {
    if (window.xlandsAnalytics) window.xlandsAnalytics.event(name, data);
    else {
      const queue = window.__xlandsAnalyticsEvents ??= [];
      if (queue.length < 60) queue.push({name, data});
    }
  } catch { /* Statistics never affect loading or gameplay. */ }
}
/** One record per actual engine attempt, including explicit retries. */
export function beginWorldLoad(world: World) {
  const start = Date.now();
  let disposed = false, loaded = false, failed = false;
  track('world_enter', {world});
  return {
    ready() {
      if (disposed || loaded || failed) return;
      loaded = true;
      track('world_ready', {world, load_ms: Date.now() - start});
    },
    error(reason: 'timeout' | 'engine' | 'download' | 'frame' | 'graphics' | 'unknown' = 'unknown') {
      if (disposed || failed) return;
      failed = true;
      track(loaded ? 'world_runtime_error' : 'world_load_error', {world, reason, load_ms: Date.now() - start});
    },
    dispose() { disposed = true; },
  };
}
