// SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
// SPDX-License-Identifier: MIT
// XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
/** Hosted at the site root or in a GitHub Pages project subdirectory. */
export function assetPath(path: string): string {
  const base = typeof document === 'undefined' ? '/' : document.documentElement.dataset.assetBase || '/';
  return base.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
}
