/**
 * Authentication Context for GeoAvia.
 *
 * Provides global auth state to the entire application via React Context.
 *
 * Security design:
 * - No tokens or passwords are stored in React state
 * - Token is stored in memory only (variable closure, not localStorage/sessionStorage)
 * - On mount, validates session by calling a protected endpoint
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
import type { AuthContextType, AuthUser } from '@/types/auth';
import { loginUser, validateSession } from '@/features/auth/services/authService';
import apiClient from '@/lib/api/axiosInstance';

const AuthContext = createContext<AuthContextType | null>(null);

// In-memory token storage (never in localStorage or sessionStorage)
// This is a module-level variable, not React state, to avoid exposing it in devtools
let memoryToken: string | null = null;

interface AuthProviderProps {
  readonly children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: try to restore session from memory token
  useEffect(() => {
    const restoreSession = async () => {
      if (memoryToken) {
        const validUser = await validateSession(memoryToken);
        if (validUser) {
          setUser(validUser);
          // Set default Authorization header for all requests
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${memoryToken}`;
        } else {
          memoryToken = null;
        }
      }
      setIsLoading(false);
    };

    void restoreSession();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await loginUser(username, password);

    // Store token in memory only
    memoryToken = result.token;

    // Set default Authorization header for subsequent requests
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${result.token}`;

    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    // Clear in-memory token
    memoryToken = null;

    // Remove Authorization header
    delete apiClient.defaults.headers.common['Authorization'];

    // Clear user state
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

/**
 * Hook to access authentication context.
 * Throws if used outside AuthProvider — fail-fast for developer safety.
 */
export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
