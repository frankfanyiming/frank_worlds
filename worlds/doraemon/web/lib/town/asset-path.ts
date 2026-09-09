/** Hosted at the site root or in a GitHub Pages project subdirectory. */
export function assetPath(path: string): string {
  const base = typeof document === 'undefined' ? '/' : document.documentElement.dataset.assetBase || '/';
  return base.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
}
