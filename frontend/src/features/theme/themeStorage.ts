/**
 * Theme persistence + application.
 *
 * The preference is stored in localStorage; when absent we fall back to the OS
 * preference (`prefers-color-scheme`). All access is guarded so a blocked or
 * corrupt storage never throws (mirrors features/map/utils/layerVisibility).
 */
import type { Theme } from './types';

const STORAGE_KEY = 'geoavia:theme';

/** True when the OS asks for a dark UI (guarded for non-browser/test envs). */
function systemPrefersDark(): boolean {
  try {
    return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return false;
  }
}

/** Reads the stored theme, falling back to the OS preference, then light. */
export function getStoredTheme(): Theme {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === 'light' || raw === 'dark') return raw;
  } catch {
    // Corrupt/unavailable storage — fall through to the system preference.
  }
  return systemPrefersDark() ? 'dark' : 'light';
}

/** Persists the theme preference (silently ignores storage failures). */
export function storeTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Storage full or unavailable — ignore; the class is still applied.
  }
}

/** Applies the theme to the document root (adds/removes `.dark` + color-scheme). */
export function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.classList.toggle('dark', theme === 'dark');
  root.style.colorScheme = theme;
}
