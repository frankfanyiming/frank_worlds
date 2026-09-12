'use client';
import { useEffect, useRef, useState } from 'react';
import { Hand, Footprints, ArrowUp, ScanLine } from 'lucide-react';
import type { Locale } from '@/lib/community/i18n';

export const touchCopy: Record<Locale, readonly string[]> = {
  'zh-CN': ['移动', '拖动画面转视角', '跑步', '互动', '动作', '视角'],
  'zh-TW': ['移動', '拖動畫面轉視角', '跑步', '互動', '動作', '視角'],
  en: ['Move', 'Drag the scene to look', 'Run', 'Interact', 'Action', 'View'],
  ja: ['移動', '画面をドラッグして見回す', '走る', '調べる', 'アクション', '視点'],
  ko: ['이동', '화면을 끌어 둘러보기', '달리기', '상호작용', '동작', '시점'],
};

/** A pointer belongs to one control until release; another finger never cancels it. */
export default function TouchControls({ locale, disabled, onMove, onRun, onInteract, onAction, onView }: {
  locale: Locale; disabled: boolean; onMove: (x: number, y: number) => void;
  onRun: (pressed: boolean) => void; onInteract: () => void;
  onAction: () => void; onView: () => void;
}) {
  const movePointer = useRef<number | null>(null), runPointers = useRef(new Set<number>());
  const callbacks = useRef({ onMove, onRun }); callbacks.current = { onMove, onRun };
  const [knob, setKnob] = useState({ x: 0, y: 0 });
  const copy = touchCopy[locale];
  const reset = () => { movePointer.current = null; runPointers.current.clear(); setKnob({ x: 0, y: 0 }); callbacks.current.onMove(0, 0); callbacks.current.onRun(false); };
  useEffect(() => {
    const hidden = () => { if (document.hidden) reset(); };
    window.addEventListener('blur', reset); window.addEventListener('resize', reset); document.addEventListener('visibilitychange', hidden);
    return () => { window.removeEventListener('blur', reset); window.removeEventListener('resize', reset); document.removeEventListener('visibilitychange', hidden); callbacks.current.onMove(0, 0); callbacks.current.onRun(false); };
  }, []);
  useEffect(() => { if (disabled) reset(); }, [disabled]);
  const move = (event: React.PointerEvent<HTMLDivElement>) => {
    if (movePointer.current !== event.pointerId) return;
    const rect = event.currentTarget.getBoundingClientRect(), radius = rect.width * .32;
    let x = (event.clientX - rect.left - rect.width / 2) / radius, y = (event.clientY - rect.top - rect.height / 2) / radius;
    const length = Math.hypot(x, y); if (length > 1) { x /= length; y /= length; }
    setKnob({ x: x * radius, y: y * radius });
    callbacks.current.onMove(length < .13 ? 0 : x, length < .13 ? 0 : y);
  };
  const release = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.pointerId !== movePointer.current) return;
    movePointer.current = null; setKnob({ x: 0, y: 0 }); callbacks.current.onMove(0, 0);
  };
  const releaseRun = (event: React.PointerEvent<HTMLButtonElement>) => {
    runPointers.current.delete(event.pointerId); callbacks.current.onRun(runPointers.current.size > 0);
  };
  return <div className="touch-controls" hidden={disabled}>
    <div className="touch-stick" role="group" aria-label={copy[0]}
      onPointerDown={event => { if (disabled || movePointer.current !== null) return; event.preventDefault(); movePointer.current = event.pointerId; event.currentTarget.setPointerCapture(event.pointerId); move(event); }}
      onPointerMove={move} onPointerUp={release} onPointerCancel={release} onLostPointerCapture={release}>
      <span className="touch-stick-knob" style={{ transform: `translate(${knob.x}px, ${knob.y}px)` }} />
      <small>{copy[0]}</small>
    </div>
    <span className="touch-look-hint">{copy[1]}</span>
    <div className="touch-actions">
      <button aria-label={copy[2]} onPointerDown={event => { event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); runPointers.current.add(event.pointerId); onRun(true); }} onPointerUp={releaseRun} onPointerCancel={releaseRun} onLostPointerCapture={releaseRun}><Footprints /><span>{copy[2]}</span></button>
      <button onClick={onView} aria-label={copy[5]}><ScanLine /><span>{copy[5]}</span></button>
      <button onClick={onAction} aria-label={copy[4]}><ArrowUp /><span>{copy[4]}</span></button>
      <button className="touch-interact" onClick={onInteract} aria-label={copy[3]}><Hand /><span>{copy[3]}</span></button>
    </div>
  </div>;
}
