/**
 * ThemeContext — global light/dark theme state.
 *
 * Mirrors the AuthContext pattern: a provider holding state with
 * useState/useCallback/useMemo, plus a `useThemeContext` accessor that enforces
 * usage within the provider. The theme is applied to <html> and persisted on
 * every change; the initial value comes from localStorage / OS preference.
 */
import { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Theme, ThemeContextType } from '../types';
import { nextTheme } from '../types';
import { applyTheme, getStoredTheme, storeTheme } from '../themeStorage';

const ThemeContext = createContext<ThemeContextType | null>(null);

interface ThemeProviderProps {
  readonly children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme);

  // Keep the document root and storage in sync with the current theme.
  useEffect(() => {
    applyTheme(theme);
    storeTheme(theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggleTheme = useCallback(() => setThemeState((prev) => nextTheme(prev)), []);

  const value = useMemo<ThemeContextType>(
    () => ({ theme, toggleTheme, setTheme }),
    [theme, toggleTheme, setTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hook exposed alongside the provider
export function useThemeContext(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return context;
}
