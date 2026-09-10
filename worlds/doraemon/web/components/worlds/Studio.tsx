'use client';
import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Plus,
  RotateCw,
  Trash2,
  Undo2,
  Redo2,
  Save,
  GitFork,
  GitMerge,
  Share2,
  Globe2,
  WandSparkles,
} from 'lucide-react';
import { api, apiBase, ApiError } from '@/lib/community/client';
import {
  ASSETS,
  addTile,
  canonical,
  emptyScene,
  mergeScenes,
  sceneSummary,
  validateScene,
  type Scene,
  type World,
  type Item,
  type Asset,
  type Resolution,
  type Conflict,
} from '@/lib/community/merge';
import {
  applyPlan,
  generateWithKey,
  type AgentConnection,
  type AgentPlan,
} from '@/lib/community/agent';
import { errorText, type Locale } from '@/lib/community/i18n';
import { Modal, worldKey, type Translate } from './Common';
const SceneCanvas = lazy(() => import('./SceneCanvas'));
type Branch = {
  id: string;
  title: string;
  world: World;
  revision: number;
  baseRevision: string;
  scene: Scene;
  base: Scene;
  owned: boolean;
  published: boolean;
};
export default function Studio({
  branchId,
  world,
  t,
  locale,
  onClose,
  onNavigate,
  connection,
  connectAgent,
  admin,
}: {
  branchId?: string;
  world: World;
  t: Translate;
  locale: Locale;
  onClose: () => void;
  onNavigate: (hash: string) => void;
  connection: AgentConnection | null;
  connectAgent: () => void;
  admin: boolean;
}) {
  const [branch, setBranch] = useState<Branch | null>(null),
    [scene, setScene] = useState<Scene>(emptyScene(world)),
    [mainRevision, setMainRevision] = useState('initial'),
    [title, setTitle] = useState(''),
    [ready, setReady] = useState(false),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(''),
    [selected, setSelected] = useState(''),
    [asset, setAsset] = useState<Asset>('tent'),
    [history, setHistory] = useState<Scene[]>([]),
    [future, setFuture] = useState<Scene[]>([]),
    [proposals, setProposals] = useState<any[]>([]),
    [versions, setVersions] = useState<any[]>([]),
    [showVersions, setShowVersions] = useState(false),
    [review, setReview] = useState<any>(null),
    [resolution, setResolution] = useState<Resolution>({}),
    [prompt, setPrompt] = useState(''),
    [plan, setPlan] = useState<AgentPlan | null>(null),
    [syncConflict, setSyncConflict] = useState<any>(null);
  const lastSaved = useRef(''),
    editable = !!branch?.owned,
    dirty = editable && canonical({ scene, title }) !== lastSaved.current;
  async function load() {
    setReady(false);
    setNotice('');
    try {
      if (branchId) {
        const b = await api<Branch>('branches/' + branchId);
        setBranch(b);
        setScene(b.scene);
        setTitle(b.title);
        lastSaved.current = canonical({ scene: b.scene, title: b.title });
      } else {
        const m = await api('main/' + world);
        setScene(m.scene);
        setMainRevision(m.revision);
        setTitle(t('expand'));
        const p = await api('proposals?world=' + world);
        setProposals(p.proposals);
      }
      setHistory([]);
      setFuture([]);
      setReady(true);
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    }
  }
  useEffect(() => {
    load();
  }, [branchId, world]);
  useEffect(() => {
    const fn = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', fn);
    return () => window.removeEventListener('beforeunload', fn);
  }, [dirty]);
  function edit(next: Scene) {
    if (!editable) return;
    setHistory((h) => [...h.slice(-29), scene]);
    setFuture([]);
    setScene(next);
    setNotice('');
    setPlan(null);
  }
  function updateItem(change: Partial<Item>) {
    if (!scene.objects[selected]) return;
    const next = structuredClone(scene);
    next.objects[selected] = { ...next.objects[selected], ...change };
    edit(next);
  }
  const selectedItem = scene.objects[selected],
    selectedTile =
      scene.tiles[selected] ||
      scene.tiles[selectedItem?.tileId] ||
      Object.values(scene.tiles)[0];
  const errors = validateScene(scene);
  async function save(publish = false) {
    if (!branch) return false;
    if (errors.length) {
      setNotice(errorText(errors[0], t));
      return false;
    }
    setBusy(true);
    setNotice('');
    try {
      const r = await api('branches/' + branch.id, 'PUT', {
        revision: branch.revision,
        scene,
        title,
        publish,
      });
      setBranch({
        ...branch,
        revision: r.revision,
        published: publish || branch.published,
        scene,
      });
      lastSaved.current = canonical({ scene, title });
      setNotice(t(publish ? 'published' : 'saved'));
      return true;
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function fork() {
    setBusy(true);
    try {
      const b = await api('branches', 'POST', {
        world,
        sourceId: branchId,
        title: title + ' · ' + t('branch'),
      });
      onNavigate('branch/' + world + '/' + b.id);
    } catch {
      setNotice(t('error'));
    } finally {
      setBusy(false);
    }
  }
  async function propose() {
    if (!(await save(true))) return;
    setBusy(true);
    try {
      const p = await api('proposals', 'POST', { branchId });
      setNotice(t('requestSubmitted'));
      await openReview(p.id);
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setBusy(false);
    }
  }
  async function openReview(id: string) {
    try {
      const result = await api('proposals/' + id);
      setReview(result);
      setResolution({});
    } catch {
      setNotice(t('error'));
    }
  }
  async function merge() {
    if (!review) return;
    setBusy(true);
    try {
      await api('proposals/' + review.id + '/merge', 'POST', {
        mainRevision: review.mainRevision,
        resolutions: resolution,
      });
      setReview(null);
      setNotice(t('mainUpdated'));
      await load();
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
      if (e instanceof ApiError && e.code === 'STALE')
        await openReview(review.id);
    } finally {
      setBusy(false);
    }
  }
  async function sync(resolutions: Resolution = {}, mainRevision?: string) {
    if (!branch) return;
    if (dirty && !(await save())) return;
    setBusy(true);
    try {
      const b = await api<Branch>('branches/' + branch.id);
      await api('branches/' + branch.id + '/sync', 'POST', {
        revision: b.revision,
        resolutions,
        mainRevision,
      });
      setSyncConflict(null);
      setResolution({});
      await load();
      setNotice(t('saved'));
    } catch (e) {
      if (e instanceof ApiError && e.code === 'CONFLICT') {
        setSyncConflict(e.details);
        setResolution({});
      } else
        setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setBusy(false);
    }
  }
  async function generate(e: React.FormEvent) {
    e.preventDefault();
    if (!connection) {
      connectAgent();
      return;
    }
    setBusy(true);
    setPlan(null);
    setNotice(t('generating'));
    try {
      const next =
        connection.kind === 'key'
          ? await generateWithKey(connection, scene, prompt, locale)
          : await api('agent/plan', 'POST', {
              scene,
              prompt,
              locale,
              requestId: crypto.randomUUID(),
            });
      applyPlan(scene, next);
      setPlan(next);
      setNotice(t('planReady'));
    } catch (e) {
      setNotice(errorText(e instanceof Error ? e.message : 'API_FAILED', t));
    } finally {
      setBusy(false);
    }
  }
  async function versionsOpen() {
    setShowVersions(true);
    try {
      setVersions((await api('history/' + world)).revisions);
    } catch {
      setNotice(t('error'));
    }
  }
  async function rollback(id: string) {
    setBusy(true);
    try {
      await api('rollback', 'POST', { world, revision: id, mainRevision });
      setShowVersions(false);
      await load();
      setNotice(t('mainUpdated'));
    } catch (e) {
      setNotice(errorText(e instanceof ApiError ? e.code : 'NETWORK', t));
    } finally {
      setBusy(false);
    }
  }
  function addObject() {
    if (!selectedTile) return;
    const next = structuredClone(scene);
    const id = 'item_' + crypto.randomUUID().replaceAll('-', '');
    for (const x of [1.4, 2.2, 3, -1.4, -2.2, -3])
      for (const z of [-2.8, -1.6, 1.6, 2.8]) {
        next.objects[id] = {
          id,
          tileId: selectedTile.id,
          asset,
          position: { x, y: 0, z },
          rotation: 0,
          color: '#ffffff',
          label: '',
        };
        if (!validateScene(next).length) {
          edit(next);
          setSelected(id);
          return;
        }
      }
    setNotice(t('limit'));
  }
  function move(dx: number, dz: number) {
    const next = structuredClone(scene);
    if (selectedItem) {
      next.objects[selected].position.x =
        Math.round((next.objects[selected].position.x + dx * 0.2) * 10) / 10;
      next.objects[selected].position.z =
        Math.round((next.objects[selected].position.z + dz * 0.2) * 10) / 10;
    } else if (selectedTile) {
      next.tiles[selectedTile.id].x += dx;
      next.tiles[selectedTile.id].z += dz;
    }
    edit(next);
  }
  const currentReview = review
    ? mergeScenes(review.base, review.main, review.branchScene, resolution)
    : null;
  async function signIn() {
    const base = await apiBase();
    location.assign(
      (base || location.origin) +
        '/signin-with-chatgpt?return_to=' +
        encodeURIComponent('/#expansion/' + world),
    );
  }
  return (
    <div className="xl-studio">
      <header className="studio-header">
        <button
          onClick={() => {
            if (dirty) {
              setNotice(t('unsaved'));
              return;
            }
            onClose();
          }}
        >
          <ArrowLeft size={17} />
          {t('home')}
        </button>
        <div>
          <span>
            {t(worldKey[world])} / {t(branch ? 'branch' : 'expand')}
          </span>
          {editable ? (
            <input
              aria-label={t('name')}
              maxLength={60}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          ) : (
            <h1>{title}</h1>
          )}
        </div>
        <div className="row-actions">
          <button
            onClick={() => {
              navigator.clipboard
                .writeText(location.href)
                .then(() => setNotice(t('copied')))
                .catch(() => setNotice(t('error')));
            }}
          >
            <Share2 size={16} />
            {t('share')}
          </button>
          {branch && !editable && (
            <button className="primary" disabled={busy} onClick={fork}>
              <GitFork size={17} />
              {t('fork')}
            </button>
          )}
          {editable && (
            <>
              <button disabled={busy} onClick={() => save()}>
                <Save size={16} />
                {t('save')}
                {dirty ? ' *' : ''}
              </button>
              <button
                className="primary"
                disabled={busy}
                onClick={() => save(true)}
              >
                <Globe2 size={16} />
                {t('publish')}
              </button>
            </>
          )}
        </div>
      </header>
      <div className="studio-notice" role="status">
        {busy
          ? t('loading')
          : notice ||
            (!branch
              ? t('extensionHint')
              : editable
                ? t('editorHint')
                : t('publishedHint'))}
      </div>
      {!ready ? (
        <div className="studio-loading">
          <p>{notice || t('loading')}</p>
          {notice && <button onClick={load}>{t('retry')}</button>}
        </div>
      ) : (
        <div className={'studio-workspace ' + (!editable ? 'view-mode' : '')}>
          <div className="studio-scene">
            <Suspense fallback={<p>{t('loading')}</p>}>
              <SceneCanvas
                scene={scene}
                selected={selected}
                onSelect={setSelected}
                t={t}
              />
            </Suspense>
            {errors.length > 0 && (
              <p className="validation" role="alert">
                {errors.map((e) => errorText(e, t)).join(' · ')}
              </p>
            )}
            {Object.keys(scene.tiles).length === 0 && (
              <div className="map-empty">
                <p>{t('noBranches')}</p>
                <button className="primary" onClick={fork}>
                  <Plus size={16} />
                  {t('createBranch')}
                </button>
              </div>
            )}
          </div>
          {editable && (
            <aside className="studio-tools">
              <div className="tool-row">
                <button
                  disabled={!history.length}
                  onClick={() => {
                    setFuture((f) => [scene, ...f]);
                    setScene(history[history.length - 1]);
                    setHistory((h) => h.slice(0, -1));
                  }}
                  aria-label={t('undo')}
                >
                  <Undo2 size={18} />
                </button>
                <button
                  disabled={!future.length}
                  onClick={() => {
                    setHistory((h) => [...h, scene]);
                    setScene(future[0]);
                    setFuture((f) => f.slice(1));
                  }}
                  aria-label={t('redo')}
                >
                  <Redo2 size={18} />
                </button>
                <span>
                  {t('revision')} {branch?.revision}
                </span>
              </div>
              <label>
                {t('tile')}
                <select
                  value={selectedTile?.id || ''}
                  onChange={(e) => setSelected(e.target.value)}
                >
                  {Object.values(scene.tiles).map((tile, i) => (
                    <option key={tile.id} value={tile.id}>
                      {tile.label || t('tile') + ' ' + (i + 1)} · {tile.x},{' '}
                      {tile.z}
                    </option>
                  ))}
                </select>
              </label>
              <button
                onClick={() => {
                  try {
                    const next = addTile(scene);
                    edit(next);
                    setSelected(Object.keys(next.tiles).at(-1)!);
                  } catch {
                    setNotice(t('limit'));
                  }
                }}
              >
                <Plus size={16} />
                {t('addTile')}
              </button>
              <label>
                {t('objects')}
                <select
                  value={asset}
                  onChange={(e) => setAsset(e.target.value as Asset)}
                >
                  {ASSETS.map((a) => (
                    <option key={a} value={a}>
                      {t(a)}
                    </option>
                  ))}
                </select>
              </label>
              <button onClick={addObject} disabled={!selectedTile}>
                <Plus size={16} />
                {t('addObject')}
              </button>
              <div className="object-list">
                {Object.values(scene.objects)
                  .filter((o) => o.tileId === selectedTile?.id)
                  .map((o) => (
                    <button
                      key={o.id}
                      aria-pressed={selected === o.id}
                      onClick={() => setSelected(o.id)}
                    >
                      {t(o.asset)}
                      {o.label ? ' · ' + o.label : ''}
                    </button>
                  ))}
              </div>
              {selectedTile && (
                <div className="selection-tools">
                  <b>{selectedItem ? t(selectedItem.asset) : t('moveTile')}</b>
                  <div className="direction-pad">
                    <button onClick={() => move(0, -1)} aria-label={t('north')}>
                      <ArrowUp size={18} />
                    </button>
                    <button onClick={() => move(-1, 0)} aria-label={t('west')}>
                      <ArrowLeft size={18} />
                    </button>
                    <button onClick={() => move(0, 1)} aria-label={t('south')}>
                      <ArrowDown size={18} />
                    </button>
                    <button onClick={() => move(1, 0)} aria-label={t('east')}>
                      <ArrowRight size={18} />
                    </button>
                  </div>
                  {selectedItem ? (
                    <>
                      <label>
                        {t('name')}
                        <input
                          maxLength={60}
                          value={selectedItem.label}
                          onChange={(e) =>
                            updateItem({ label: e.target.value })
                          }
                        />
                      </label>
                      <div className="tool-row">
                        <button
                          onClick={() =>
                            updateItem({
                              rotation: selectedItem.rotation + Math.PI / 4,
                            })
                          }
                        >
                          <RotateCw size={16} />
                          {t('rotate')}
                        </button>
                        <label className="color-label">
                          {t('color')}
                          <input
                            type="color"
                            value={selectedItem.color}
                            onChange={(e) =>
                              updateItem({ color: e.target.value })
                            }
                          />
                        </label>
                      </div>
                      <button
                        className="danger-text"
                        onClick={() => {
                          const next = structuredClone(scene);
                          delete next.objects[selected];
                          edit(next);
                          setSelected(selectedTile.id);
                        }}
                      >
                        <Trash2 size={16} />
                        {t('remove')}
                      </button>
                    </>
                  ) : (
                    <>
                      <label>
                        {t('theme')}
                        <select
                          value={selectedTile.biome}
                          onChange={(e) => {
                            const next = structuredClone(scene);
                            next.tiles[selectedTile.id].biome = e.target
                              .value as 'grass' | 'sand';
                            edit(next);
                          }}
                        >
                          <option value="grass">{t('grass')}</option>
                          <option value="sand">{t('sand')}</option>
                        </select>
                      </label>
                      <button
                        className="danger-text"
                        onClick={() => {
                          const next = structuredClone(scene);
                          delete next.tiles[selectedTile.id];
                          for (const o of Object.values(next.objects))
                            if (o.tileId === selectedTile.id)
                              delete next.objects[o.id];
                          edit(next);
                          setSelected('');
                        }}
                      >
                        <Trash2 size={16} />
                        {t('remove')}
                      </button>
                    </>
                  )}
                </div>
              )}
              <form className="studio-agent" onSubmit={generate}>
                <label>
                  <WandSparkles size={16} /> Agent
                  <textarea
                    rows={3}
                    maxLength={2000}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={t('prompt')}
                  />
                </label>
                <button type="submit" disabled={busy || !prompt.trim()}>
                  {connection ? t('generate') : t('connect')}
                </button>
                <small>{t('agentDraftHint')}</small>
                {plan && (
                  <div className="agent-plan">
                    <p>{plan.summary}</p>
                    <span>
                      {plan.operations.length} {t('changed')}
                    </span>
                    <button
                      className="primary"
                      type="button"
                      onClick={() => {
                        try {
                          edit(applyPlan(scene, plan));
                          setNotice(t('planReady'));
                        } catch (e) {
                          setNotice(errorText((e as Error).message, t));
                        }
                      }}
                    >
                      {t('apply')}
                    </button>
                  </div>
                )}
              </form>
              <div className="merge-tools">
                <button disabled={busy} onClick={() => sync()}>
                  <GitFork size={16} />
                  {t('sync')}
                </button>
                <button disabled={busy} className="primary" onClick={propose}>
                  <GitMerge size={16} />
                  {t('propose')}
                </button>
                <small>{t('mergeHint')}</small>
              </div>
            </aside>
          )}
        </div>
      )}
      {!branch && ready && (
        <section className="studio-proposals">
          <div className="section-heading">
            <h2>{t('proposals')}</h2>
            <button onClick={versionsOpen}>{t('versionHistory')}</button>
          </div>
          {proposals.length ? (
            proposals.map((p) => (
              <div className="proposal-row" key={p.id}>
                <span>
                  <strong>{p.title}</strong>
                  <small>
                    {t('revision')} {p.branch_revision}
                  </small>
                </span>
                <span className={'status ' + p.status}>
                  {t(
                    p.status === 'merged'
                      ? 'merged'
                      : p.status === 'open'
                        ? 'pending'
                        : 'rejected',
                  )}
                </span>
                <button onClick={() => openReview(p.id)}>
                  {t('review')}
                  <ArrowRight size={16} />
                </button>
              </div>
            ))
          ) : (
            <p className="empty">{t('noProposals')}</p>
          )}
        </section>
      )}
      {review && (
        <Modal
          title={t('proposal') + ' · ' + review.title}
          t={t}
          wide
          onClose={() => setReview(null)}
        >
          <p className="muted">
            {t('added')} {review.summary.added} · {t('changed')}{' '}
            {review.summary.changed} · {t('removed')} {review.summary.removed}
          </p>
          <div className="review-preview">
            <Suspense fallback={<p>{t('loading')}</p>}>
              <SceneCanvas scene={currentReview!.scene} t={t} />
            </Suspense>
          </div>
          <ConflictChoices
            conflicts={review.conflicts}
            resolution={resolution}
            onChange={setResolution}
            t={t}
          />
          <div className="modal-footer">
            <span role="status">{notice}</span>
            {review.status === 'merged' ? (
              <strong>{t('merged')}</strong>
            ) : admin ? (
              <button
                className="primary"
                disabled={
                  busy ||
                  !!currentReview?.unresolved.length ||
                  !!validateScene(currentReview!.scene).length
                }
                onClick={merge}
              >
                <GitMerge size={16} />
                {t('merge')}
              </button>
            ) : (
              <button onClick={signIn}>
                {t('admin')} · {t('signIn')}
              </button>
            )}
          </div>
        </Modal>
      )}
      {syncConflict && (
        <Modal
          title={t('conflicts')}
          t={t}
          onClose={() => setSyncConflict(null)}
        >
          <ConflictChoices
            conflicts={syncConflict.conflicts}
            resolution={resolution}
            onChange={setResolution}
            t={t}
          />
          <button
            className="primary"
            disabled={
              busy ||
              syncConflict.conflicts.some(
                (c: Conflict) => c.kind === 'overlap' || !resolution[c.key],
              )
            }
            onClick={() => sync(resolution, syncConflict.mainRevision)}
          >
            {t('resolve')}
          </button>
        </Modal>
      )}
      {showVersions && (
        <Modal
          title={t('versionHistory')}
          t={t}
          onClose={() => setShowVersions(false)}
        >
          <p className="muted">{t('rollbackHint')}</p>
          {versions.length ? (
            versions.map((v) => (
              <div className="proposal-row" key={v.id}>
                <span>
                  <code>{v.id.slice(0, 8)}</code>
                  <small>{new Date(v.created_at).toLocaleString(locale)}</small>
                </span>
                {admin && (
                  <button disabled={busy} onClick={() => rollback(v.id)}>
                    {t('rollback')}
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="empty">{t('nothing')}</p>
          )}
        </Modal>
      )}
    </div>
  );
}
function ConflictChoices({
  conflicts,
  resolution,
  onChange,
  t,
}: {
  conflicts: Conflict[];
  resolution: Resolution;
  onChange: (r: Resolution) => void;
  t: Translate;
}) {
  return (
    <div className="conflicts">
      {conflicts.length === 0 ? (
        <p className="connected">
          {t('noConflicts')} · {t('autoMerge')}
        </p>
      ) : (
        conflicts.map((c) => (
          <div className="conflict" key={c.key}>
            <b>
              {c.kind === 'overlap'
                ? t('overlap')
                : c.key.split('.').slice(-1)[0]}
            </b>
            {c.kind !== 'overlap' && (
              <div className="conflict-options">
                {(['main', 'branch'] as const).map((side) => (
                  <button
                    key={side}
                    className={resolution[c.key] === side ? 'chosen' : ''}
                    onClick={() => onChange({ ...resolution, [c.key]: side })}
                  >
                    <span>
                      {t(side === 'main' ? 'keepMain' : 'keepBranch')}
                    </span>
                    <code>{JSON.stringify(c[side]) || t('removed')}</code>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
