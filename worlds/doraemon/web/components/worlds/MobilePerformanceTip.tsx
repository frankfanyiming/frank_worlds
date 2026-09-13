// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
'use client';
import { useEffect, useState } from 'react';
import { Monitor, X } from 'lucide-react';
import type { Translate } from './Common';

// Only remembers dismissing this notice in this tab; no network or analytics.
const dismissedKey = 'xlands-mobile-tip-dismissed';
export default function MobilePerformanceTip({ t }: { t: Translate }) {
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    try { setDismissed(sessionStorage.getItem(dismissedKey) === '1'); } catch {}
  }, []);
  if (dismissed) return null;
  return <aside className="mobile-performance-tip" aria-label={t('mobileTipTitle')}>
    <Monitor size={17} aria-hidden="true" />
    <p>{t('mobilePerformanceTip')}</p>
    <button type="button" aria-label={t('close')} onClick={() => {
      setDismissed(true);
      try { sessionStorage.setItem(dismissedKey, '1'); } catch {}
    }}><X size={17} aria-hidden="true" /></button>
  </aside>;
}
