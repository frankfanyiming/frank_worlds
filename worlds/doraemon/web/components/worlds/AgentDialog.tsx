'use client';
import { useState } from 'react';
import { KeyRound, Check, ExternalLink } from 'lucide-react';
import { Modal, type Translate } from './Common';
import { api, apiBase } from '@/lib/community/client';
import type { AgentConnection } from '@/lib/community/agent';
export default function AgentDialog({
  t,
  connection,
  onConnect,
  onClose,
  hostedEnabled,
}: {
  t: Translate;
  connection: AgentConnection | null;
  onConnect: (value: AgentConnection | null) => void;
  onClose: () => void;
  hostedEnabled: boolean;
}) {
  const [tab, setTab] = useState<'key' | 'hosted'>('key'),
    [key, setKey] = useState(''),
    [model, setModel] = useState('gpt-6-astra'),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState('');
  async function connect(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setNotice('');
    try {
      const response = await fetch(
        'https://api.openai.com/v1/models/' + encodeURIComponent(model.trim()),
        {
          headers: { Authorization: 'Bearer ' + key.trim() },
          signal: AbortSignal.timeout(15000),
        },
      );
      if (!response.ok) throw Error();
      onConnect({ kind: 'key', key: key.trim(), model: model.trim() });
      setKey('');
      setNotice(t('connected'));
    } catch {
      setNotice(t('modelUnavailable'));
    } finally {
      setBusy(false);
    }
  }
  async function pay() {
    setBusy(true);
    try {
      const result = await api('billing/checkout', 'POST', {
        returnUrl: location.href,
      });
      if (result.url && new URL(result.url).hostname === 'checkout.stripe.com')
        location.assign(result.url);
      else throw Error();
    } catch {
      setNotice(t('hostedPending'));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title={t('agent')} onClose={onClose} t={t}>
      <div className="segmented">
        <button aria-pressed={tab === 'key'} onClick={() => setTab('key')}>
          {t('ownKey')}
        </button>
        <button
          aria-pressed={tab === 'hosted'}
          onClick={() => setTab('hosted')}
        >
          {t('platform')}
        </button>
      </div>
      {tab === 'key' ? (
        <form className="agent-form" onSubmit={connect}>
          <label>
            {t('apiKey')}
            <input
              required
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="sk-…"
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
          </label>
          <label>
            {t('model')}
            <input
              required
              value={model}
              pattern="[a-zA-Z0-9_.:-]+"
              onChange={(e) => setModel(e.target.value)}
            />
          </label>
          <p className="muted">
            {t('keyHint')}
            <br />
            {t('keyDestination')}
          </p>
          <div className="row-actions">
            <button
              type="submit"
              className="primary"
              disabled={busy || !key.trim()}
            >
              <KeyRound size={16} />
              {busy ? t('loading') : t('connectKey')}
            </button>
            {connection && (
              <button
                type="button"
                onClick={() => {
                  onConnect(null);
                  setKey('');
                  setNotice('');
                }}
              >
                {t('disconnect')}
              </button>
            )}
          </div>
          {connection?.kind === 'key' && (
            <p className="connected">
              <Check size={16} />
              {connection.model} · {t('connected')}
            </p>
          )}
        </form>
      ) : (
        <div className="agent-form">
          <strong>GPT‑6 Astra</strong>
          <p className="muted">{t('hostedHint')}</p>
          <button
            className="primary"
            disabled={!hostedEnabled || busy}
            onClick={pay}
          >
            {hostedEnabled ? t('pay') : t('hostedPending')}
            <ExternalLink size={16} />
          </button>
          {hostedEnabled && (
            <button
              onClick={() => {
                onConnect({ kind: 'hosted', key: '', model: 'gpt-6-astra' });
                onClose();
              }}
            >
              {t('connect')}
            </button>
          )}
        </div>
      )}
      <p role="status" className="form-status">
        {notice}
      </p>
    </Modal>
  );
}
