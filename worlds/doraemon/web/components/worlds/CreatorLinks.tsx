'use client';
import { useState } from 'react';
import { ArrowUpRight, Copy } from 'lucide-react';
import { CREATOR, copyPlainText } from '@/lib/community/creator';
import type { Translate } from './Common';

export default function CreatorLinks({ t }: { t: Translate }) {
  const [notice, setNotice] = useState('');
  return <div className="creator-links">
    <a href={CREATOR.x} target="_blank" rel="noopener noreferrer">
      <span className="social-mark" aria-hidden="true">X</span>
      <span><strong>X</strong><small>@FrankFYM001</small></span>
      <ArrowUpRight size={17} aria-hidden="true" />
    </a>
    <button type="button" aria-label={t('douyin') + ' ' + CREATOR.douyin + ' · ' + t('copyAccount')}
      onClick={async () => setNotice(t(await copyPlainText(CREATOR.douyin) ? 'accountCopied' : 'copyFailed'))}>
      <span className="social-mark" aria-hidden="true">♪</span>
      <span><strong>{t('douyin')}</strong><small>{CREATOR.douyin}</small><small>{t('copyAccount')}</small></span>
      <Copy size={15} aria-hidden="true" />
    </button>
    <a href={CREATOR.xiaohongshuUrl} target="_blank" rel="noopener noreferrer">
      <span className="social-mark social-red" aria-hidden="true">小红书</span>
      <span><strong>{t('xiaohongshu')}</strong><small>{CREATOR.xiaohongshu}</small></span>
      <ArrowUpRight size={17} aria-hidden="true" />
    </a>
    {notice && <p className="social-notice" role="status">{notice}</p>}
  </div>;
}
