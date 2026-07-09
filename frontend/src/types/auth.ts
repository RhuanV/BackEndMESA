/**
 * Authentication and RBAC type definitions for GeoAvia.
 *
 * RBAC Model: 5 MESA-A roles (Sprint 3). Each role has explicit permissions;
 * there is no inheritance between them.
 *
 * Security note: No sensitive data (tokens, passwords) is stored in these types.
 * Tokens are managed exclusively via HttpOnly cookies by the backend.
 */

/** All valid user roles */
export type UserRole =
  | 'coordenador'
  | 'gestor'
  | 'supervisor'
  | 'operador'
  | 'administrador'
  | 'desenvolvedor';

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
  | 'admin:users:create'
  | 'admin:layers'
  | 'admin:audit'
  | 'dev:health'
  | 'dev:logs'
  | 'dev:debug';

/**
 * Per-role permission sets — Sprint 3.
 * Based on each role's responsibilities in the PO document.
 */
export const ROLE_PERMISSIONS: Record<UserRole, readonly Permission[]> = {
  coordenador: [
    'map:view',
    'map:layers',
    'analysis:configure',
    'analysis:run',
    'assessment:create',
    'results:view',
    'export:download',
    'admin:users',
    'admin:users:create',
    'admin:layers',
    'admin:audit',
  ],
  gestor: [
    'map:view',
    'map:layers',
    'assessment:create',
    'results:view',
    'export:download',
    'admin:users',
  ],
  supervisor: [
    'map:view',
    'map:layers',
    'analysis:configure',
    'results:view',
    'export:download',
    'admin:users',
    'admin:users:create',
  ],
  operador: [
    'map:view',
    'map:layers',
    'analysis:configure',
    'analysis:run',
    'assessment:create',
    'results:view',
    'export:download',
  ],
  administrador: [
    'map:view',
    'map:layers',
    'admin:layers',
    'admin:audit',
    'dev:health',
    'dev:logs',
    'dev:debug',
  ],
  desenvolvedor: [
    'map:view',
    'map:layers',
    'analysis:configure',
    'analysis:run',
    'assessment:create',
    'results:view',
    'export:download',
    'admin:users',
    'admin:users:create',
    'admin:layers',
    'admin:audit',
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
