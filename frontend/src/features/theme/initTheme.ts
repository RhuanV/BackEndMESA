/**
 * Applies the persisted theme synchronously, before React renders, to avoid a
 * flash of the wrong theme (FOUC). Called at the top of main.tsx. An inline
 * <script> in index.html is not an option here because the CSP is `script-src
 * 'self'`; running this from the entry module keeps the CSP intact.
 */
import { applyTheme, getStoredTheme } from './themeStorage';

export function initTheme(): void {
  applyTheme(getStoredTheme());
}
