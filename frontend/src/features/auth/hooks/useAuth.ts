/**
 * useAuth hook — Convenience wrapper around AuthContext.
 *
 * Provides typed access to authentication state and actions.
 */
import { useAuthContext } from '@/features/auth/context/AuthContext';

export function useAuth() {
  return useAuthContext();
}
