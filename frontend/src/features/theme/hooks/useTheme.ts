/** Public hook to read/toggle the app theme. */
import { useThemeContext } from '../context/ThemeContext';

export function useTheme() {
  return useThemeContext();
}
