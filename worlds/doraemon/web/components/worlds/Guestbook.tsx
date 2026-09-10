'use client';
import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Feather, Trash2 } from 'lucide-react';
import { api, ApiError } from '@/lib/community/client';
import { errorText, type Locale } from '@/lib/community/i18n';
import { WorldSelect, worldKey, type Translate } from './Common';
import type { World } from '@/lib/community/merge';
type Note = {
  id: string;
  world: World;
  nickname: string;
  body: string;
  createdAt: number;
  owned: boolean;
};
export default function Guestbook({
  t,
  locale,
  admin,
}: {
  t: Translate;
  locale: Locale;
  admin: boolean;
}) {
  const [notes, setNotes] = useState<Note[]>([]),
    [loading, setLoading] = useState(true),
    [body, setBody] = useState(''),
    [nickname, setNickname] = useState(''),
    [email, setEmail] = useState(''),
    [consent, setConsent] = useState(false),
    [world, setWorld] = useState('frog'),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(''),
    [failed, setFailed] = useState(false);
  const honeypot = useRef<HTMLInputElement>(null),
    message = useRef<HTMLTextAreaElement>(null);
  async function load() {
    setLoading(true);
    setFailed(false);
    try {
      const result = await api('notes');
      setNotes(result.notes);
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) {
      setNotice(t('contentRequired'));
      return;
    }
    if (email && !consent) {
      setNotice(t('emailConsent'));
      return;
    }
    setBusy(true);
    setNotice('');
    try {
      await api('notes', 'POST', {
        body,
        nickname: nickname || t('nicknameHint'),
        email,
        contactConsent: consent,
        world,
        website: honeypot.current?.value || '',
      });
      setBody('');
      setEmail('');
      setConsent(false);
      setNotice(t('sent'));
      await load();
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: string) {
    setBusy(true);
    try {
      await api('notes/' + id, 'DELETE');
      setNotes((v) => v.filter((n) => n.id !== id));
    } catch {
      setNotice(t('error'));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="guestbook" id="guestbook">
      <div className="section-heading">
        <h2>
          <Feather size={23} />
          {t('guestbook')}
        </h2>
        <button
          className="link-button"
          onClick={() => message.current?.focus()}
        >
          {t('write')}
          <ArrowUpRight size={17} />
        </button>
      </div>
      <div className="book-layout">
        <form className="note-compose" onSubmit={submit}>
          <label className="sr-only" htmlFor="guest-note">
            {t('message')}
          </label>
          <textarea
            id="guest-note"
            ref={message}
            maxLength={500}
            required
            rows={5}
            placeholder={t('messageHint')}
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <div className="compose-meta">
            <WorldSelect value={world} onChange={setWorld} t={t} />
            <span>{body.length}/500</span>
          </div>
          <div className="note-fields">
            <label>
              {t('nickname')}
              <input
                maxLength={30}
                placeholder={t('nicknameHint')}
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                autoComplete="nickname"
              />
            </label>
            <label>
              {t('email')}
              <input
                type="email"
                maxLength={254}
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
              <small>{t('emailHint')}</small>
            </label>
          </div>
          <label className="xl-honeypot" aria-hidden="true">
            Website
            <input ref={honeypot} tabIndex={-1} autoComplete="off" />
          </label>
          {email && (
            <label className="consent">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
              />
              {t('contactConsent')}
            </label>
          )}
          <div className="compose-footer">
            <span role="status">{notice}</span>
            <button
              className="primary"
              type="submit"
              disabled={busy || !body.trim()}
            >
              {busy ? t('sending') : t('send')}
              <ArrowUpRight size={17} />
            </button>
          </div>
        </form>
        <div className="note-pages" aria-live="polite">
          {loading ? (
            <p className="empty">{t('loading')}</p>
          ) : failed ? (
            <p className="empty">
              {t('serverPending')} <button onClick={load}>{t('retry')}</button>
            </p>
          ) : notes.length === 0 ? (
            <div className="empty-page">
              <span className="book-lines" aria-hidden="true" />
              <p>{t('noMessages')}</p>
            </div>
          ) : (
            notes.map((n, i) => (
              <article key={n.id} className={'visitor-note paper-' + (i % 3)}>
                <div>
                  <span className="note-world">{t(worldKey[n.world])}</span>
                  {(n.owned || admin) && (
                    <button
                      className="icon-button"
                      disabled={busy}
                      onClick={() => remove(n.id)}
                      aria-label={t('deleteMessage')}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
                <p>{n.body}</p>
                <footer>
                  <span>{n.nickname}</span>
                  <time dateTime={new Date(n.createdAt).toISOString()}>
                    {new Date(n.createdAt).toLocaleDateString(locale, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </time>
                </footer>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
