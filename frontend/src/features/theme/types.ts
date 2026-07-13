/** Theme domain types and pure helpers. */

export type Theme = 'light' | 'dark';

export interface ThemeContextType {
  readonly theme: Theme;
  readonly toggleTheme: () => void;
  readonly setTheme: (theme: Theme) => void;
}

/** Returns the opposite theme. Pure — safe to unit-test without a DOM. */
export function nextTheme(theme: Theme): Theme {
  return theme === 'dark' ? 'light' : 'dark';
}
