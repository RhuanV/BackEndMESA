/**
 * Authentication and RBAC type definitions for GeoAvia.
 *
 * RBAC Model: Roles are NON-OVERLAPPING silos. 'dev' does not inherit
 * 'admin' access and vice-versa. Each role has explicit permissions.
 *
 * Security note: No sensitive data (tokens, passwords) is stored in these types.
 * Tokens are managed exclusively via HttpOnly cookies by the backend.
 */

/** All valid user roles */
export type UserRole = 'analyst' | 'admin' | 'dev';

/** All valid feature permissions */
export type Permission =
  | 'map:view'
  | 'map:layers'
  | 'analysis:configure'
  | 'analysis:run'
  | 'assessment:create'
  | 'results:view'
  | 'export:download'
  | 'admin:users'
  | 'admin:layers'
  | 'admin:audit'
  | 'dev:health'
  | 'dev:logs'
  | 'dev:debug';

/**
 * Per-role permission sets.
 * IMPORTANT: These are NON-OVERLAPPING — admin cannot access dev features and vice-versa.
 */
export const ROLE_PERMISSIONS: Record<UserRole, readonly Permission[]> = {
  analyst: [
    'map:view',
    'map:layers',
    'analysis:configure',
    'analysis:run',
    'assessment:create',
    'results:view',
    'export:download',
  ],
  admin: [
    'map:view',
    'map:layers',
    'results:view',
    'admin:users',
    'admin:layers',
    'admin:audit',
  ],
  dev: [
    'map:view',
    'map:layers',
    'results:view',
    'dev:health',
    'dev:logs',
    'dev:debug',
  ],
} as const;

/** Check if a role has a specific permission */
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].includes(permission);
}

/** Represents the authenticated user's non-sensitive profile data */
export interface AuthUser {
  readonly username: string;
  readonly role: UserRole;
}

/** Shape of the authentication context provided to the application */
export interface AuthContextType {
  readonly user: AuthUser | null;
  readonly isAuthenticated: boolean;
  readonly isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

/** Login API request payload */
export interface LoginRequest {
  readonly username: string;
  readonly password: string;
}

/** Login API response from the backend */
export interface LoginResponse {
  readonly access_token: string;
  readonly token_type: string;
}
