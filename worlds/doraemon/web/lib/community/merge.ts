/** Scene changes are data, never executable code. IDs survive forks and merges. */
export const ASSETS = [
  'tent',
  'chair',
  'table',
  'lamp',
  'sign',
  'planter',
  'rock',
  'stump',
  'flowers',
  'fence',
  'crate',
  'mat',
] as const;
export type Asset = (typeof ASSETS)[number];
export type World = 'doraemon' | 'frog' | 'conan';
export type Tile = {
  id: string;
  x: number;
  z: number;
  biome: 'grass' | 'sand';
  label: string;
};
export type Item = {
  id: string;
  asset: Asset;
  tileId: string;
  position: { x: number; y: number; z: number };
  rotation: number;
  color: string;
  label: string;
};
export type Scene = {
  schema: 1;
  world: World;
  tiles: Record<string, Tile>;
  objects: Record<string, Item>;
};
export type Conflict = {
  key: string;
  kind: 'edit' | 'delete-edit' | 'add-add' | 'overlap';
  base: unknown;
  main: unknown;
  branch: unknown;
};
export type Resolution = Record<string, 'main' | 'branch'>;
export const radius: Record<Asset, number> = {
  tent: 0.84,
  chair: 0.31,
  table: 0.78,
  lamp: 0.2,
  sign: 0.46,
  planter: 0.32,
  rock: 0.46,
  stump: 0.36,
  flowers: 0.22,
  fence: 0.76,
  crate: 0.46,
  mat: 0.84,
};
const safeId = (id: string) =>
  /^[a-zA-Z0-9_-]{1,80}$/.test(id) &&
  !['__proto__', 'constructor', 'prototype'].includes(id);
export function objectOverlaps(scene: Scene) {
  const out: [string, string][] = [];
  const items = Object.values(scene.objects).filter(
    (o) =>
      o &&
      radius[o.asset] &&
      o.position &&
      o.asset !== 'flowers' &&
      o.asset !== 'mat',
  );
  for (let i = 0; i < items.length; i++)
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i],
        b = items[j];
      if (
        a.tileId === b.tileId &&
        Math.hypot(a.position.x - b.position.x, a.position.z - b.position.z) <
          (radius[a.asset] + radius[b.asset]) * 0.9
      )
        out.push([a.id, b.id]);
    }
  return out;
}
export function emptyScene(world: World): Scene {
  return { schema: 1, world, tiles: {}, objects: {} };
}
export function canonical(value: unknown): string {
  if (value === undefined) return 'undefined';
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object')
    return (
      '{' +
      Object.entries(value)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => JSON.stringify(k) + ':' + canonical(v))
        .join(',') +
      '}'
    );
  return JSON.stringify(value);
}
const same = (a: unknown, b: unknown) => canonical(a) === canonical(b);
export function mergeScenes(
  base: Scene,
  main: Scene,
  branch: Scene,
  resolutions: Resolution = {},
) {
  if (base.world !== main.world || main.world !== branch.world)
    throw new Error('WORLD_MISMATCH');
  const result = emptyScene(main.world),
    conflicts: Conflict[] = [];
  function mergeValue(
    key: string,
    b: unknown,
    m: unknown,
    f: unknown,
  ): unknown {
    if (same(m, f)) return structuredClone(m);
    if (same(b, m)) return structuredClone(f);
    if (same(b, f)) return structuredClone(m);
    const conflict: Conflict = {
      key,
      kind:
        b === undefined
          ? 'add-add'
          : m === undefined || f === undefined
            ? 'delete-edit'
            : 'edit',
      base: b,
      main: m,
      branch: f,
    };
    conflicts.push(conflict);
    return structuredClone(resolutions[key] === 'branch' ? f : m);
  }
  for (const collection of ['tiles', 'objects'] as const) {
    for (const id of new Set([
      ...Object.keys(base[collection]),
      ...Object.keys(main[collection]),
      ...Object.keys(branch[collection]),
    ])) {
      const b = base[collection][id],
        m = main[collection][id],
        f = branch[collection][id];
      let value: unknown;
      if (!b || !m || !f) value = mergeValue(`${collection}.${id}`, b, m, f);
      else {
        const out: Record<string, unknown> = {};
        for (const field of new Set([
          ...Object.keys(b),
          ...Object.keys(m),
          ...Object.keys(f),
        ])) {
          const v = mergeValue(
            `${collection}.${id}.${field}`,
            (b as any)[field],
            (m as any)[field],
            (f as any)[field],
          );
          if (v !== undefined) out[field] = v;
        }
        value = out;
      }
      if (value !== undefined)
        (result[collection] as Record<string, unknown>)[id] = value;
    }
  }
  const occupied = new Map<string, string>();
  for (const t of Object.values(result.tiles)) {
    const slot = `${t.x},${t.z}`,
      previous = occupied.get(slot);
    if (previous)
      conflicts.push({
        key: `overlap.${previous}.${t.id}`,
        kind: 'overlap',
        base: null,
        main: previous,
        branch: t.id,
      });
    occupied.set(slot, t.id);
  }
  for (const [a, b] of objectOverlaps(result))
    conflicts.push({
      key: `object-overlap.${a}.${b}`,
      kind: 'overlap',
      base: null,
      main: a,
      branch: b,
    });
  const unresolved = conflicts.filter(
    (c) => c.kind === 'overlap' || !resolutions[c.key],
  );
  return { scene: result, conflicts, unresolved };
}
export function validateScene(value: unknown): string[] {
  const errors: string[] = [];
  const s = value as Scene;
  if (
    !s ||
    s.schema !== 1 ||
    !['doraemon', 'frog', 'conan'].includes(s.world) ||
    !s.tiles ||
    !s.objects ||
    Array.isArray(s.tiles) ||
    Array.isArray(s.objects)
  )
    return ['INVALID_SCENE'];
  const tiles = Object.values(s.tiles),
    items = Object.values(s.objects);
  if (tiles.length > 64 || items.length > 1280) errors.push('SCENE_LIMIT');
  const occupied = new Set<string>();
  for (const [id, t] of Object.entries(s.tiles)) {
    if (
      !safeId(id) ||
      !t ||
      typeof t !== 'object' ||
      t.id !== id ||
      !Number.isInteger(t.x) ||
      !Number.isInteger(t.z) ||
      Math.abs(t.x) > 8 ||
      Math.abs(t.z) > 8 ||
      !['grass', 'sand'].includes(t.biome) ||
      typeof t.label !== 'string' ||
      t.label.length > 60
    )
      errors.push('INVALID_TILE');
    if (!t || typeof t !== 'object') continue;
    const key = `${t.x},${t.z}`;
    if (occupied.has(key)) errors.push('TILE_OVERLAP');
    occupied.add(key);
  }
  for (const [id, o] of Object.entries(s.objects)) {
    if (
      !o ||
      o.id !== id ||
      !safeId(id) ||
      !ASSETS.includes(o.asset) ||
      !Object.hasOwn(s.tiles, o.tileId) ||
      !o.position ||
      ![o.position.x, o.position.y, o.position.z, o.rotation].every(
        Number.isFinite,
      ) ||
      Math.abs(o.position.x) > 3.4 ||
      Math.abs(o.position.z) > 3.4 ||
      o.position.y !== 0 ||
      !/^#[0-9a-fA-F]{6}$/.test(o.color) ||
      typeof o.label !== 'string' ||
      o.label.length > 60
    )
      errors.push('INVALID_OBJECT');
    // A clear north/south path joins neighboring tiles.
    if (
      o?.position &&
      (Math.abs(o.position.x) < 0.7 || Math.abs(o.position.z) < 0.7) &&
      ['tent', 'table', 'fence', 'crate', 'rock'].includes(o.asset)
    )
      errors.push('PATH_BLOCKED');
  }
  for (const t of tiles)
    if (t && items.filter((o) => o?.tileId === t.id).length > 20)
      errors.push('TILE_OBJECT_LIMIT');
  if (objectOverlaps(s).length) errors.push('OBJECT_OVERLAP');
  if (tiles.length > 1 && !errors.includes('INVALID_TILE')) {
    const seen = new Set<string>();
    const queue = [tiles[0]];
    while (queue.length) {
      const p = queue.shift()!;
      if (seen.has(p.id)) continue;
      seen.add(p.id);
      for (const t of tiles)
        if (Math.abs(t.x - p.x) + Math.abs(t.z - p.z) === 1 && !seen.has(t.id))
          queue.push(t);
    }
    if (seen.size !== tiles.length) errors.push('DISCONNECTED_TILES');
  }
  return [...new Set(errors)];
}
export function addTile(scene: Scene, label = ''): Scene {
  const result = structuredClone(scene);
  const slots = new Set(Object.values(scene.tiles).map((t) => `${t.x},${t.z}`));
  const candidates = Object.values(scene.tiles).flatMap((t) => [
    [t.x + 1, t.z],
    [t.x, t.z + 1],
    [t.x - 1, t.z],
    [t.x, t.z - 1],
  ]);
  const [x, z] = candidates.find(
    ([x, z]) => !slots.has(`${x},${z}`) && Math.abs(x) <= 8 && Math.abs(z) <= 8,
  ) ?? [0, 0];
  if (slots.has(`${x},${z}`)) throw new Error('SCENE_LIMIT');
  const id = 'tile_' + crypto.randomUUID().replaceAll('-', '');
  result.tiles[id] = { id, x, z, biome: 'grass', label };
  return result;
}
export function sceneSummary(base: Scene, scene: Scene) {
  let added = 0,
    changed = 0,
    removed = 0;
  for (const c of ['tiles', 'objects'] as const)
    for (const id of new Set([
      ...Object.keys(base[c]),
      ...Object.keys(scene[c]),
    ])) {
      if (!base[c][id]) added++;
      else if (!scene[c][id]) removed++;
      else if (!same(base[c][id], scene[c][id])) changed++;
    }
  return { added, changed, removed };
}
