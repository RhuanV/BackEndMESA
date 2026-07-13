/**
 * App — Root application component.
 *
 * Wraps the entire application with:
 * - ErrorBoundary (catches rendering errors, shows generic message)
 * - ThemeProvider (global light/dark theme state)
 * - AuthProvider (global authentication state)
 * - RouterProvider (route-based navigation)
 */
import { RouterProvider } from 'react-router-dom';
import { ErrorBoundary } from '@/components/feedback';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import { ThemeProvider } from '@/features/theme/context/ThemeContext';
import { router } from './Router';

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
