'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/community/client';
import { Modal, type Translate, WORLDS, worldKey } from './Common';
export default function AdminPanel({
  t,
  onClose,
  onNavigate,
}: {
  t: Translate;
  onClose: () => void;
  onNavigate: (route: string) => void;
}) {
  const [contacts, setContacts] = useState<any[]>([]),
    [status, setStatus] = useState('');
  useEffect(() => {
    setStatus(t('loading'));
    api('contacts')
      .then((r) => {
        setContacts(r.contacts);
        setStatus('');
      })
      .catch(() => setStatus(t('authRequired')));
  }, []);
  return (
    <Modal t={t} title={t('admin')} onClose={onClose} wide>
      <div className="row-actions">
        {WORLDS.map((w) => (
          <button key={w} onClick={() => onNavigate('expansion/' + w)}>
            {t(worldKey[w])} · {t('proposals')}
          </button>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 24 }}>
        {t('email')} · {t('footerPrivacy')}
      </p>
      <p role="status">{status}</p>
      {contacts.map((c) => (
        <article key={c.note_id} className="proposal-row">
          <div style={{ flex: 1 }}>
            <strong>{c.nickname}</strong>
            <p
              style={{ fontSize: 13, whiteSpace: 'pre-wrap', margin: '8px 0' }}
            >
              {c.body}
            </p>
            <a href={'mailto:' + c.email}>{c.email} ↗</a>
          </div>
        </article>
      ))}
    </Modal>
  );
}
