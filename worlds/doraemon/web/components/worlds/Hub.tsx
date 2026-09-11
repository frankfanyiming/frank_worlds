'use client';
import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  GitFork,
  Globe2,
  Home,
  KeyRound,
  Plus,
  Volume2,
  VolumeX,
  LockKeyhole,
  GitMerge,
} from 'lucide-react';
import { assetPath } from '@/lib/town/asset-path';
import { api, apiBase, ApiError, visitorToken } from '@/lib/community/client';
import {
  dictionaries,
  languages,
  initialLocale,
  errorText,
  type Locale,
  type TextKey,
} from '@/lib/community/i18n';
import type { World } from '@/lib/community/merge';
import type { AgentConnection } from '@/lib/community/agent';
import { Modal, WorldSelect, WORLDS, titleKey, worldKey } from './Common';
import Guestbook from './Guestbook';
import AgentDialog from './AgentDialog';
import AdminPanel from './AdminPanel';
const Doraemon = lazy(() => import('./DoraemonWorld'));
const Studio = lazy(() => import('./Studio'));
type BranchCard = {
  id: string;
  world: World;
  title: string;
  published: boolean;
  owned: boolean;
  revision: number;
  updatedAt: number;
  tileCount?: number;
  objectCount?: number;
};
export default function WorldHub() {
  const [locale, setLocale] = useState<Locale>('zh-CN'),
    [route, setRoute] = useState(''),
    [sound, setSound] = useState(false),
    [agentOpen, setAgentOpen] = useState(false),
    [connection, setConnection] = useState<AgentConnection | null>(null),
    [meta, setMeta] = useState({
      admin: false,
      hostedAgentEnabled: false,
      companyUrl: null as string | null,
    }),
    [branches, setBranches] = useState<BranchCard[]>([]),
    [filter, setFilter] = useState(''),
    [mine, setMine] = useState(false),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(''),
    [createOpen, setCreateOpen] = useState(false),
    [createWorld, setCreateWorld] = useState('frog'),
    [createTitle, setCreateTitle] = useState(''),
    [busy, setBusy] = useState(false);
  const t = (key: TextKey) =>
    dictionaries[locale][key] || dictionaries['zh-CN'][key];
  useEffect(() => {
    setLocale(initialLocale());
    const update = () => setRoute(decodeURIComponent(location.hash.slice(1)));
    update();
    if (location.hash === '#agent') setAgentOpen(true);
    window.addEventListener('hashchange', update);
    api('meta')
      .then(setMeta)
      .catch(() => {});
    return () => window.removeEventListener('hashchange', update);
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = t('brand') + ' · XLands';
    try { localStorage.setItem('xlands-language', locale); } catch {}
  }, [locale]);
  async function loadBranches() {
    setLoading(true);
    setError('');
    try {
      if (mine && !visitorToken()) {
        setBranches([]);
        return;
      }
      const params = new URLSearchParams();
      if (filter) params.set('world', filter);
      if (mine) params.set('mine', '1');
      setBranches((await api('branches?' + params)).branches);
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    if (!route || route === 'agent' || route === 'admin') loadBranches();
  }, [filter, mine, route]);
  function navigate(hash: string) {
    location.hash = hash;
  }
  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const b = await api('branches', 'POST', {
        world: createWorld,
        title: createTitle,
      });
      setCreateOpen(false);
      setCreateTitle('');
      navigate('branch/' + createWorld + '/' + b.id);
    } catch (e) {
      setError(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setBusy(false);
    }
  }
  const [kind, worldSlug, branchId] = route.split('/'),
    world = WORLDS.includes(worldSlug as World) ? (worldSlug as World) : 'frog';
  const agentDialog = agentOpen && (
    <AgentDialog
      t={t}
      connection={connection}
      onConnect={setConnection}
      hostedEnabled={meta.hostedAgentEnabled}
      onClose={() => setAgentOpen(false)}
    />
  );
  if (kind === 'branch' || kind === 'expansion')
    return (
      <div className="xlands">
        <Suspense
          fallback={<div className="xl-full-loading">{t('loading')}</div>}
        >
          <Studio
            key={route}
            branchId={kind === 'branch' ? branchId : undefined}
            world={world}
            t={t}
            locale={locale}
            onClose={() => navigate('')}
            onNavigate={navigate}
            connection={connection}
            connectAgent={() => setAgentOpen(true)}
            admin={meta.admin}
          />
        </Suspense>
        {agentDialog}
      </div>
    );
  if (kind === 'world')
    return (
      <div className="xlands xl-world">
        <div className="world-nav">
          <button onClick={() => navigate('')}>
            <ArrowLeft size={17} />
            {t('home')}
          </button>
          <strong>{t(titleKey[world])}</strong>
          <div>
            <button onClick={() => navigate('expansion/' + world)}>
              <GitMerge size={17} />
              {t('expand')}
            </button>
            <button
              className="icon-button"
              aria-label={sound ? t('soundOn') : t('soundOff')}
              onClick={() => setSound(!sound)}
            >
              {sound ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
          </div>
        </div>
        {world === 'doraemon' ? (
          <Suspense
            fallback={<div className="xl-full-loading">{t('preparing')}</div>}
          >
            <Doraemon sound={sound} />
          </Suspense>
        ) : (
          <NativeWorld
            world={world}
            locale={locale}
            sound={sound}
            t={t}
            onExpansion={() => navigate('expansion/' + world)}
          />
        )}
      </div>
    );
  return (
    <div className="xlands">
      <div className="hub-shell">
        <header className="hub-header">
          <a className="hub-brand" href="#" aria-label={t('brand')}>
            <Home size={29} strokeWidth={1.6} />
            <span>{t('brand')}</span>
          </a>
          <nav>
            <a
              className="guest-link"
              href="#guestbook"
              onClick={(e) => {
                e.preventDefault();
                document
                  .getElementById('guestbook')
                  ?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <BookOpen size={17} />
              {t('guestbook')}
            </a>
            <button
              onClick={() => setAgentOpen(true)}
              className={connection ? 'agent-connected' : ''}
            >
              <KeyRound size={16} />
              {t('agent')}
              {connection && <i />}
            </button>
            <label className="language-select">
              <Globe2 size={16} />
              <span className="sr-only">{t('language')}</span>
              <select
                value={locale}
                onChange={(e) => setLocale(e.target.value as Locale)}
              >
                {languages.map((l) => (
                  <option value={l.id} key={l.id}>
                    {l.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="icon-button"
              onClick={() => setSound(!sound)}
              aria-label={sound ? t('soundOn') : t('soundOff')}
            >
              {sound ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
          </nav>
        </header>
        <main>
          <div className="creator-prompt">
            <LockKeyhole size={19} />
            <input
              disabled
              aria-label={t('prompt')}
              placeholder={t('prompt')}
            />
            <span>{t('unavailable')}</span>
          </div>
          <section className="world-grid" aria-label={t('world')}>
            {WORLDS.map((w) => (
              <article className={'world-card world-' + w} key={w}>
                <button
                  className="world-image"
                  onClick={() => navigate('world/' + w)}
                  aria-label={t(titleKey[w])}
                >
                  <img
                    src={assetPath('covers/' + w + '.png')}
                    alt={t(worldKey[w])}
                    width={1448}
                    height={1086}
                    fetchPriority={w === 'doraemon' ? 'high' : 'auto'}
                  />
                  <span className="image-enter">
                    <ArrowUpRight size={30} />
                  </span>
                </button>
                <div className="world-card-bottom">
                  <h1>{t(titleKey[w])}</h1>
                  <div>
                    <button
                      className="link-button"
                      onClick={() => navigate('expansion/' + w)}
                    >
                      <GitMerge size={15} />
                      {t('expand')}
                    </button>
                    <button
                      className="enter-button"
                      onClick={() => navigate('world/' + w)}
                    >
                      {t('enter')}
                      <ArrowRight size={19} />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </section>
          <div className="coming-worlds" aria-label={t('coming')}>
            <span className="mini-door" aria-hidden="true" />
            <p>{t('coming')}</p>
            <span className="waiting-dots" aria-hidden="true">
              · · · · ·
            </span>
          </div>
          <section className="community-section">
            <div className="section-heading">
              <h2>
                <GitFork size={23} />
                {t('branches')}
              </h2>
              <button
                className="primary"
                onClick={() => {
                  setCreateOpen(true);
                  setError('');
                }}
              >
                <Plus size={17} />
                {t('createBranch')}
              </button>
            </div>
            <div className="community-filters">
              <div className="segmented">
                <button aria-pressed={!mine} onClick={() => setMine(false)}>
                  {t('publicBranches')}
                </button>
                <button aria-pressed={mine} onClick={() => setMine(true)}>
                  {t('myBranches')}
                </button>
              </div>
              <WorldSelect value={filter} all onChange={setFilter} t={t} />
            </div>
            {loading ? (
              <p className="empty">{t('loading')}</p>
            ) : error ? (
              <p className="empty" role="alert">
                {error} <button onClick={loadBranches}>{t('retry')}</button>
              </p>
            ) : branches.length ? (
              <div className="branch-grid">
                {branches.map((b) => (
                  <article
                    className={'branch-card branch-theme-' + b.world}
                    key={b.id}
                  >
                    <button
                      className="branch-preview"
                      onClick={() => navigate('branch/' + b.world + '/' + b.id)}
                      aria-label={t('visit') + ' · ' + b.title}
                    >
                      <span className="island-mark" aria-hidden="true">
                        <span />
                        <span />
                        <span />
                        <GitFork size={23} />
                      </span>
                      <span className="branch-world">
                        {t(worldKey[b.world])}
                      </span>
                    </button>
                    <div className="branch-details">
                      <h3>{b.title}</h3>
                      <div className="branch-meta">
                        <span>
                          {b.published ? t('published') : t('draft')} ·{' '}
                          {t('revision')} {b.revision}
                        </span>
                        <span>
                          {b.tileCount || 0} {t('tile')}
                        </span>
                      </div>
                      <button
                        className="link-button"
                        onClick={() =>
                          navigate('branch/' + b.world + '/' + b.id)
                        }
                      >
                        {t(b.owned ? 'edit' : 'visit')}
                        <ArrowUpRight size={17} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="branches-empty">
                <div className="empty-island" aria-hidden="true">
                  <Plus size={24} />
                </div>
                <span>{t('noBranches')}</span>
                <button
                  className="link-button"
                  onClick={() => setCreateOpen(true)}
                >
                  {t('createFrom')}
                  <ArrowUpRight size={16} />
                </button>
              </div>
            )}
          </section>
          <Guestbook t={t} locale={locale} admin={meta.admin} />
        </main>
        <footer className="hub-footer">
          <span>
            XLands <span>·</span> {t('brand')}
          </span>
          <div>
            <a
              href="https://github.com/frankfanyiming/frank_worlds"
              target="_blank"
              rel="noreferrer"
            >
              {t('git')}
              <ArrowUpRight size={14} />
            </a>
            {meta.companyUrl ? (
              <a href={meta.companyUrl} target="_blank" rel="noreferrer">
                {t('about')}
                <ArrowUpRight size={14} />
              </a>
            ) : (
              <span className="pending-about" aria-disabled="true">
                {t('about')}
                <ArrowUpRight size={14} />
              </span>
            )}
            <button
              className="link-button"
              onClick={async () => {
                if (meta.admin) {
                  navigate('admin');
                  return;
                }
                const base = await apiBase();
                location.assign(
                  (base || location.origin) +
                    '/signin-with-chatgpt?return_to=' +
                    encodeURIComponent('/#admin'),
                );
              }}
            >
              {t('admin')}
            </button>
          </div>
        </footer>
      </div>
      {createOpen && (
        <Modal
          title={t('createBranch')}
          t={t}
          onClose={() => setCreateOpen(false)}
        >
          <form className="create-form" onSubmit={create}>
            <label>
              {t('world')}
              <WorldSelect
                value={createWorld}
                onChange={setCreateWorld}
                t={t}
              />
            </label>
            <label>
              {t('name')}
              <input
                required
                autoFocus
                maxLength={60}
                placeholder={t('branchName')}
                value={createTitle}
                onChange={(e) => setCreateTitle(e.target.value)}
              />
            </label>
            <p className="muted">{t('privateDraft')}</p>
            <p role="status">{error}</p>
            <button className="primary" disabled={busy || !createTitle.trim()}>
              {busy ? t('loading') : t('create')}
              <ArrowRight size={17} />
            </button>
          </form>
        </Modal>
      )}
      {agentDialog}
      {route === 'admin' && meta.admin && (
        <AdminPanel t={t} onClose={() => navigate('')} onNavigate={navigate} />
      )}
    </div>
  );
}
function NativeWorld({
  world,
  locale,
  sound,
  t,
  onExpansion,
}: {
  world: 'frog' | 'conan';
  locale: Locale;
  sound: boolean;
  t: (k: TextKey) => string;
  onExpansion: () => void;
}) {
  const frame = useRef<HTMLIFrameElement>(null),
    soundRef = useRef(sound),
    initialSound = useRef(sound),
    lastActivity = useRef(Date.now());
  soundRef.current = sound;
  const [progress, setProgress] = useState(0),
    [detail, setDetail] = useState(''),
    [ready, setReady] = useState(false),
    [error, setError] = useState(false),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    setReady(false);
    setError(false);
    lastActivity.current = Date.now();
    let started = false;
    const watchdog = window.setInterval(() => {
      if (!started && Date.now() - lastActivity.current > 90000) setError(true);
    }, 5000);
    const fn = (e: MessageEvent) => {
      if (e.source !== frame.current?.contentWindow) return;
      lastActivity.current = Date.now();
      if (e.data?.type === 'xlands-ready') {
        started = true;
        setReady(true);
        frame.current?.contentWindow?.postMessage(
          { type: 'xlands-sound', enabled: soundRef.current },
          '*',
        );
      }
      if (e.data?.type === 'xlands-progress') {
        setProgress(e.data.progress);
        if (typeof e.data.detail === 'string') setDetail(e.data.detail);
      }
      if (e.data?.type === 'xlands-error') setError(true);
      if (e.data?.type === 'xlands-expansion') onExpansion();
    };
    window.addEventListener('message', fn);
    return () => {
      window.removeEventListener('message', fn);
      window.clearInterval(watchdog);
    };
  }, [world, retry]);
  useEffect(() => {
    frame.current?.contentWindow?.postMessage(
      { type: 'xlands-sound', enabled: sound },
      '*',
    );
  }, [sound]);
  return (
    <div className="native-world">
      {!error && <iframe
        ref={frame}
        key={retry}
        title={t(titleKey[world])}
        src={
          assetPath('worlds/' + world + '/index.html') + '?v=loading-2&lang=' +
          locale +
          '&sound=' +
          (initialSound.current ? '1' : '0')
        }
        allow="autoplay; fullscreen; gamepad"
        allowFullScreen
        onError={() => setError(true)}
      />}
      {!ready && (
        <div className="native-loading">
          <img src={assetPath('covers/' + world + '.png')} alt="" />
          <div>
            <h2>{error ? t('error') : t('preparing')}</h2>
            <progress value={progress} max={100} aria-label={t('loading')} />
            <span>{Math.round(progress)}%</span>
            {!error && detail && <p>{detail}</p>}
            {error && (
              <button
                onClick={() => {
                  setRetry(retry + 1);
                  setProgress(0);
                  setDetail('');
                }}
              >
                {t('retry')}
              </button>
            )}
          </div>
        </div>
      )}
      <div className="native-controls">
        <span>WASD · {t('walk')}</span>
        <span>Shift · {t('run')}</span>
        {world === 'frog' && <span>Space · {t('jump')}</span>}
        <span>E · {t('interact')}</span>
      </div>
    </div>
  );
}
