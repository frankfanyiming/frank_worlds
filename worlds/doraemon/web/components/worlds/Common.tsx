'use client';
import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';
import type { TextKey } from '@/lib/community/i18n';
import type { World } from '@/lib/community/merge';
export type Translate = (key: TextKey) => string;
export const WORLDS: World[] = ['doraemon', 'frog', 'conan'];
export const worldKey: Record<World, TextKey> = {
  doraemon: 'worldDoraemon',
  frog: 'worldFrog',
  conan: 'worldConan',
};
export const titleKey: Record<World, TextKey> = {
  doraemon: 'titleDoraemon',
  frog: 'titleFrog',
  conan: 'titleConan',
};
export function Modal({
  title,
  children,
  onClose,
  t,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  t: Translate;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className={'xl-modal ' + (wide ? 'wide' : '')}
      aria-label={title}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header>
        <h2>{title}</h2>
        <button
          type="button"
          className="icon-button"
          onClick={onClose}
          aria-label={t('close')}
        >
          <X size={21} />
        </button>
      </header>
      {children}
    </dialog>
  );
}
export function WorldSelect({
  value,
  onChange,
  t,
  all = false,
}: {
  value: string;
  onChange: (value: string) => void;
  t: Translate;
  all?: boolean;
}) {
  return (
    <select
      aria-label={t('world')}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {all && <option value="">{t('allWorlds')}</option>}
      {WORLDS.map((w) => (
        <option key={w} value={w}>
          {t(worldKey[w])}
        </option>
      ))}
    </select>
  );
}
