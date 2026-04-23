/**
 * App — Root application component.
 *
 * Wraps the entire application with:
 * - ErrorBoundary (catches rendering errors, shows generic message)
 * - AuthProvider (global authentication state)
 * - RouterProvider (route-based navigation)
 */
import { RouterProvider } from 'react-router-dom';
import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import { router } from './Router';

export function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ErrorBoundary>
  );
}
