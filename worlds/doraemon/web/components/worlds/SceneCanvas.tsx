'use client';
import { useEffect, useRef, useState } from 'react';
import { assetPath } from '@/lib/town/asset-path';
import type { Scene } from '@/lib/community/merge';
import type { TextKey } from '@/lib/community/i18n';
export default function SceneCanvas({
  scene,
  selected,
  onSelect,
  t,
}: {
  scene: Scene;
  selected?: string;
  onSelect?: (id: string) => void;
  t: (k: TextKey) => string;
}) {
  const host = useRef<HTMLDivElement>(null),
    api = useRef<any>(null),
    selectRef = useRef(onSelect),
    dataRef = useRef(scene);
  selectRef.current = onSelect;
  dataRef.current = scene;
  const [error, setError] = useState(false),
    [ready, setReady] = useState(false),
    [walk, setWalk] = useState(false);
  useEffect(() => {
    let disposed = false,
      cleanup = () => {};
    setReady(false);
    (async () => {
      const [T, { OrbitControls }, { GLTFLoader }] = await Promise.all([
        import('three'),
        import('three/addons/controls/OrbitControls.js'),
        import('three/addons/loaders/GLTFLoader.js'),
      ]);
      if (disposed || !host.current) return;
      const element = host.current,
        renderer = new T.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = T.PCFSoftShadowMap;
      renderer.setClearColor(0xe4e9dc);
      renderer.outputColorSpace = T.SRGBColorSpace;
      renderer.toneMapping = T.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      element.appendChild(renderer.domElement);
      const stage = new T.Scene();
      stage.fog = new T.Fog(0xe4e9dc, 65, 155);
      const camera = new T.PerspectiveCamera(42, 1, 0.1, 230);
      camera.position.set(12, 15, 17);
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.maxPolarAngle = Math.PI * 0.47;
      controls.minDistance = 3;
      controls.maxDistance = 110;
      controls.target.set(0, 0, 0);
      const ambient = new T.HemisphereLight(0xfff7e5, 0x5a6b48, 2.2);
      stage.add(ambient);
      const sun = new T.DirectionalLight(0xffefd3, 3.2);
      sun.position.set(-10, 20, 12);
      sun.castShadow = true;
      sun.shadow.mapSize.set(2048, 2048);
      Object.assign(sun.shadow.camera, {
        left: -60,
        right: 60,
        top: 60,
        bottom: -60,
        near: 1,
        far: 100,
      });
      sun.shadow.bias = -0.0007;
      stage.add(sun);
      const loader = new GLTFLoader(),
        cache = new Map<string, any>();
      let group = new T.Group();
      stage.add(group);
      let current = 0;
      let walking = false,
        frame = 0;
      const keys = new Set<string>();
      let drawTime = performance.now();
      async function model(name: string) {
        if (!cache.has(name))
          cache.set(
            name,
            loader
              .loadAsync(assetPath(`community-models/${name}.glb`))
              .then((g) => g.scene),
          );
        return cache.get(name);
      }
      let box: any = null;
      function highlight(id?: string) {
        if (box) {
          stage.remove(box);
          box.geometry.dispose();
          box.material.dispose();
          box = null;
        }
        if (!id) return;
        const obj = group.children.find((o) => o.userData.itemId === id);
        if (obj) {
          box = new T.BoxHelper(obj, 0xd79758);
          stage.add(box);
        }
      }
      async function update(data: Scene, selection?: string) {
        const version = ++current;
        const next = new T.Group();
        try {
          const tiles = Object.values(data.tiles);
          await Promise.all(
            tiles.map(async (tile) => {
              const o = (await model(`tile-${tile.biome}`)).clone(true);
              o.position.set(tile.x * 8, 0, tile.z * 8);
              o.userData.itemId = tile.id;
              next.add(o);
            }),
          );
          await Promise.all(
            Object.values(data.objects).map(async (item) => {
              const tile = data.tiles[item.tileId];
              if (!tile) return;
              const o = (await model(item.asset)).clone(true);
              o.position.set(
                tile.x * 8 + item.position.x,
                0,
                tile.z * 8 + item.position.z,
              );
              o.rotation.y = item.rotation;
              o.userData.itemId = item.id;
              o.traverse((m: any) => {
                if (m.isMesh) {
                  m.material = m.material.clone();
                  m.userData.xlandsOwnedMaterial = true;
                  if (item.color !== '#ffffff')
                    m.material.color.multiply(new T.Color(item.color));
                }
              });
              next.add(o);
            }),
          );
          if (disposed || version !== current) {
            disposeClones(next);
            return;
          }
          next.traverse((m: any) => {
            if (m.isMesh) {
              m.castShadow = true;
              m.receiveShadow = true;
            }
          });
          stage.remove(group);
          disposeClones(group);
          group = next;
          stage.add(group);
          highlight(selection);
          setReady(true);
        } catch {
          if (!disposed) setError(true);
        }
      }
      function disposeClones(g: any) {
        g.traverse((o: any) => {
          if (o.userData.xlandsOwnedMaterial) o.material.dispose();
        });
      }

      const ray = new T.Raycaster(),
        pointer = new T.Vector2();
      let down = [0, 0];
      const pointerDown = (e: PointerEvent) => {
        down = [e.clientX, e.clientY];
        element.focus();
      };
      const pointerUp = (e: PointerEvent) => {
        if (Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 7) return;
        const r = renderer.domElement.getBoundingClientRect();
        pointer.set(
          ((e.clientX - r.left) / r.width) * 2 - 1,
          (-(e.clientY - r.top) / r.height) * 2 + 1,
        );
        ray.setFromCamera(pointer, camera);
        const hit = ray.intersectObjects(group.children, true)[0];
        if (hit) {
          let o: any = hit.object;
          while (o && !o.userData.itemId) o = o.parent;
          if (o) selectRef.current?.(o.userData.itemId);
        }
      };
      const keyDown = (e: KeyboardEvent) => {
        if (/^(Key[WASD]|Arrow|Space)/.test(e.code)) {
          keys.add(e.code);
          e.preventDefault();
        }
      };
      const keyUp = (e: KeyboardEvent) => keys.delete(e.code);
      const blur = () => keys.clear();
      element.addEventListener('keydown', keyDown);
      element.addEventListener('keyup', keyUp);
      element.addEventListener('blur', blur);
      element.addEventListener('pointerdown', pointerDown);
      element.addEventListener('pointerup', pointerUp);
      const resize = new ResizeObserver(() => {
        const w = element.clientWidth,
          h = element.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      });
      resize.observe(element);
      function animate() {
        if (disposed) return;
        frame = requestAnimationFrame(animate);
        const stamp = performance.now(),
          dt = Math.min(0.05, (stamp - drawTime) / 1000);
        drawTime = stamp;
        if (walking) {
          const forward = new T.Vector3();
          camera.getWorldDirection(forward);
          forward.y = 0;
          forward.normalize();
          const right = new T.Vector3()
            .crossVectors(forward, T.Object3D.DEFAULT_UP)
            .normalize();
          const delta = new T.Vector3();
          if (keys.has('KeyW') || keys.has('ArrowUp')) delta.add(forward);
          if (keys.has('KeyS') || keys.has('ArrowDown')) delta.sub(forward);
          if (keys.has('KeyD') || keys.has('ArrowRight')) delta.add(right);
          if (keys.has('KeyA') || keys.has('ArrowLeft')) delta.sub(right);
          delta.normalize().multiplyScalar(dt * 3.5);
          const next = camera.position.clone().add(delta);
          const inside = Object.values(dataRef.current.tiles).some(
            (tile) =>
              Math.abs(next.x - tile.x * 8) < 3.7 &&
              Math.abs(next.z - tile.z * 8) < 3.7,
          );
          if (inside) {
            camera.position.add(delta);
            controls.target.add(delta);
          }
        }
        controls.update();
        renderer.render(stage, camera);
      }
      api.current = {
        update,
        highlight,
        setWalk: (value: boolean) => {
          walking = value;
          keys.clear();
          if (value) {
            const tile = Object.values(dataRef.current.tiles)[0];
            const x = (tile?.x || 0) * 8,
              z = (tile?.z || 0) * 8;
            camera.position.set(x, 1.6, z + 2.5);
            controls.target.set(x, 1.6, z);
            controls.maxPolarAngle = Math.PI * 0.65;
            controls.minDistance = 0.2;
            controls.enablePan = false;
          } else {
            camera.position.set(12, 15, 17);
            controls.target.set(0, 0, 0);
            controls.maxPolarAngle = Math.PI * 0.47;
            controls.minDistance = 3;
            controls.enablePan = true;
          }
          element.focus();
        },
      };
      await update(dataRef.current);
      animate();
      cleanup = () => {
        current++;
        cancelAnimationFrame(frame);
        resize.disconnect();
        controls.dispose();
        disposeClones(group);
        if (box) {
          box.geometry.dispose();
          box.material.dispose();
        }
        renderer.dispose();
        element.removeEventListener('keydown', keyDown);
        element.removeEventListener('keyup', keyUp);
        element.removeEventListener('blur', blur);
        element.removeEventListener('pointerdown', pointerDown);
        element.removeEventListener('pointerup', pointerUp);
        renderer.domElement.remove();
        for (const p of cache.values())
          p.then((g: any) =>
            g.traverse((o: any) => {
              o.geometry?.dispose();
              o.material?.dispose();
            }),
          );
        api.current = null;
      };
      if (disposed) cleanup();
    })().catch(() => !disposed && setError(true));
    return () => {
      disposed = true;
      cleanup();
    };
  }, []);
  useEffect(() => {
    api.current?.update(scene, selected);
  }, [scene]);
  useEffect(() => api.current?.highlight(selected), [selected]);
  return (
    <div className="scene-frame">
      <div
        ref={host}
        tabIndex={0}
        className="scene-canvas"
        aria-label={t('mainMap')}
      />
      {!ready && !error && (
        <div className="scene-status" role="status">
          {t('loading')}
        </div>
      )}
      {error && (
        <div className="scene-status" role="alert">
          {t('error')}
        </div>
      )}
      <div className="scene-mode">
        <button
          onClick={() => {
            setWalk(!walk);
            api.current?.setWalk(!walk);
          }}
          aria-pressed={walk}
        >
          {walk ? t('mainMap') : t('walk')}
        </button>
        <span>{walk ? 'W A S D' : t('camera')}</span>
      </div>
    </div>
  );
}
