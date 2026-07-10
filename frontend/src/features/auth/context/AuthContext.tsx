/**
 * Authentication Context for GeoAvia.
 *
 * Provides global auth state to the entire application via React Context.
 *
 * Security design:
 * - No tokens or passwords are stored in React state or localStorage
 * - The access token lives in an in-memory store (lib/api/authToken)
 * - The session survives a refresh via an httpOnly refresh cookie: on mount we
 *   call /refresh to mint a new access token and resolve the user from /me
 * - Exposes only non-sensitive user data (username, role)
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import type { AuthContextType, AuthUser } from '@/types';
import { loginUser, logoutUser, refreshSession } from '@/features/auth/services/authService';

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  readonly children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: restore the session from the httpOnly refresh cookie (survives F5).
  useEffect(() => {
    const restoreSession = async () => {
      const restored = await refreshSession();
      if (restored) setUser(restored);
      setIsLoading(false);
    };

    void restoreSession();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await loginUser(username, password);
    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
    }),
    [user, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Accesses the auth context; throws an error if used outside the AuthProvider.
// eslint-disable-next-line react-refresh/only-export-components -- hook exposed alongside the provider
export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
