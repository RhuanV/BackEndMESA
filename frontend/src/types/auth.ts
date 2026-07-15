/**
 * Authentication and RBAC type definitions for GeoAvia.
 *
 * RBAC Model: 3 roles. Each role has an explicit permission set; there is no
 * inheritance between them.
 *   - operador      : operates the program (no admin/dev powers)
 *   - administrador : operador + user management, layer config, audit
 *   - desenvolvedor : everything, incl. developer tools (sandboxed in production)
 *
 * Security note: No sensitive data (tokens, passwords) is stored in these types.
 */

/** All valid user roles */
export type UserRole = 'operador' | 'administrador' | 'desenvolvedor';

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
  | 'dev:logs';

/**
 * Per-role permission sets (3-role model).
 *   - operador      : operational features only
 *   - administrador : operador + user management, layer config, audit
 *   - desenvolvedor : everything, including developer tools
 */
export const ROLE_PERMISSIONS: Record<UserRole, readonly Permission[]> = {
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
  /**
   * Backend effective permissions (base role ∪ assigned custom profile), as
   * returned by GET /me. Used for permission-aware UI gating (defense in depth;
   * the backend remains the real boundary). Optional for backward compatibility.
   */
  readonly permissions?: readonly string[];
  /** Assigned custom permission profile id, or null when none. */
  readonly profileId?: number | null;
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
