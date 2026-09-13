// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
// Independent of React/Three/Godot. A failed tracker must never block a world.
(function () {
  'use strict';
  if (window.parent !== window || window.xlandsAnalytics) return;
  const scriptBase = new URL('.', document.currentScript.src);
  const worlds = ['doraemon', 'frog', 'conan'];
  const titles = { home: 'XLands 首页', doraemon: '哆啦A梦世界', frog: '旅行青蛙世界', conan: '柯南世界' };
  const events = new Set(['world_enter', 'world_ready', 'world_load_error', 'world_runtime_error']);
  const reasons = new Set(['timeout', 'engine', 'download', 'frame', 'graphics', 'unknown']);
  const queue = [];
  let active = true, trackerReady = false, lastPage = null;
  function optedOut() {
    try { return navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true || localStorage.getItem('umami.disabled') === '1'; }
    catch (_) { return navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true; }
  }
  function page() {
    const standalone = location.pathname.match(/\/worlds\/(frog|conan)\/(?:index\.html)?$/);
    if (standalone) return standalone[1];
    const hash = location.hash.replace(/^#\/?/, '');
    if (!hash || hash === 'resources' || hash === 'agent') return 'home';
    const match = hash.match(/^world\/(doraemon|frog|conan)$/);
    return match ? match[1] : null; // Do not collect branch IDs, admin routes or arbitrary hashes.
  }
  function campaign() {
    const source = new URLSearchParams(location.search).get('utm_source') || '';
    return /^[a-z0-9_-]{1,40}$/i.test(source) ? source : '';
  }
  function referringSite() {
    try { const url = new URL(document.referrer); return /^https?:$/.test(url.protocol) ? url.origin : ''; }
    catch (_) { return ''; }
  }
  const source = campaign(), referrer = referringSite();
  const device = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent || '') || window.matchMedia?.('(any-pointer: coarse)').matches ? 'mobile' : 'desktop';
  function send(item) {
    if (!active || optedOut()) return;
    try {
      const result = window.umami.track(props => ({
        ...props,
        url: scriptBase.pathname + (item.page === 'home' ? '' : 'world/' + item.page),
        title: titles[item.page],
        referrer,
        ...(item.name ? {name: item.name} : {}),
        data: {...item.data, device, ...(source ? {source} : {})},
      }));
      Promise.resolve(result).catch(() => {});
    } catch (_) { /* Ad blockers and analytics outages are not game failures. */ }
  }
  function enqueue(item) {
    if (!active || optedOut()) return;
    if (trackerReady) send(item);
    else if (queue.length < 60) queue.push(item);
  }
  function event(name, data) {
    if (!events.has(name) || !data || !worlds.includes(data.world)) return;
    const safe = {world: data.world};
    if (Number.isFinite(data.load_ms)) safe.load_ms = Math.max(0, Math.min(3600000, Math.round(data.load_ms)));
    if (reasons.has(data.reason)) safe.reason = data.reason;
    enqueue({page: data.world, name, data: safe});
  }
  window.xlandsAnalytics = {event};
  const pending = window.__xlandsAnalyticsEvents || [];
  window.__xlandsAnalyticsEvents = [];
  function view() {
    const current = page();
    if (current === lastPage) return;
    lastPage = current;
    if (current) enqueue({page: current, data: {}});
  }
  view();
  pending.slice(0, 60).forEach(item => event(item.name, item.data));
  window.addEventListener('hashchange', view);
  function stop() { active = false; queue.length = 0; window.removeEventListener('hashchange', view); }
  if (optedOut()) { stop(); return; }
  // Config is public metadata only. Never place an account password/API key here.
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 4000);
  fetch(new URL('analytics-config.json', scriptBase), {signal: controller.signal, credentials: 'omit', cache: 'no-cache'})
    .then(response => { if (!response.ok) throw Error('config'); return response.json(); })
    .then(config => {
      if (!config.enabled || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(config.websiteId) ||
          !Array.isArray(config.domains) || !config.domains.includes(location.hostname)) { stop(); return; }
      const url = new URL(config.scriptUrl);
      if (url.protocol !== 'https:' || url.username || url.password) { stop(); return; }
      const script = document.createElement('script');
      script.src = url.href;
      script.async = true;
      script.dataset.websiteId = config.websiteId;
      // We own hash routing and events; no autoclicks, replay, heatmaps or frame sampling.
      script.dataset.autoTrack = 'false';
      script.dataset.doNotTrack = 'true';
      script.dataset.domains = config.domains.join(',');
      const scriptTimeout = setTimeout(stop, 10000);
      script.onload = () => {
        clearTimeout(scriptTimeout);
        if (!active || typeof window.umami?.track !== 'function') { stop(); return; }
        trackerReady = true;
        queue.splice(0).forEach(send);
      };
      script.onerror = () => { clearTimeout(scriptTimeout); stop(); };
      document.head.appendChild(script);
    })
    .catch(stop)
    .finally(() => clearTimeout(timeout));
})();
