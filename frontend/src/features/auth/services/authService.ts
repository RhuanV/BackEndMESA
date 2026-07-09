/**
 * Authentication service for GeoAvia.
 *
 * Handles API communication for login/logout/session validation.
 * Security notes:
 * - Passwords are sent via POST body only (never in URL/query params)
 * - The backend manages tokens via HttpOnly cookies (future)
 * - Currently handles the Bearer token flow as transitional fallback
 * - Error messages are generic to prevent user enumeration
 */
import apiClient from '@/lib/api/axiosInstance';
import type { AuthUser, LoginResponse } from '@/types';

/**
 * Authenticates a user with the backend.
 *
 * The backend currently expects OAuth2PasswordRequestForm (form-encoded).
 * When it migrates to HttpOnly cookies, only this service needs to change.
 */
export async function loginUser(
  username: string,
  password: string
): Promise<{ user: AuthUser; token: string }> {
  // Backend expects form-encoded data (OAuth2PasswordRequestForm)
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await apiClient.post<LoginResponse>('/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  const { access_token } = response.data;

  // Decode non-sensitive payload from JWT (sub, username, role)
  // Security: We only extract display data. The token itself is not stored in state.
  const payload = parseJwtPayload(access_token);

  return {
    user: {
      username: payload.username,
      role: payload.role,
    },
    token: access_token,
  };
}

/**
 * Resets a password using an admin-issued recovery code (public endpoint).
 * The user provides their username, the code relayed by an administrator, and a
 * new password. Errors from the backend are intentionally generic.
 */
export async function resetPasswordByCode(
  username: string,
  code: string,
  newPassword: string
): Promise<void> {
  await apiClient.post('/password-reset', {
    username,
    code,
    new_password: newPassword,
  });
}

/**
 * Validates the current session by calling a protected endpoint.
 * Used on app mount to check if the user is still authenticated.
 */
export async function validateSession(token: string): Promise<AuthUser | null> {
  try {
    const response = await apiClient.get<Array<Record<string, unknown>>>('/users', {
      headers: { Authorization: `Bearer ${token}` },
    });
    // If we get a 200, the session is valid
    if (response.status === 200) {
      const payload = parseJwtPayload(token);
      return { username: payload.username, role: payload.role };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Parses the non-sensitive payload from a JWT without verifying the signature.
 *
 * Security: This is ONLY used for UI display purposes (username, role).
 * The actual token validation is done server-side on every API call.
 * We NEVER trust client-side JWT decoding for authorization decisions.
 */
function parseJwtPayload(token: string): { sub: string; username: string; role: AuthUser['role'] } {
  try {
    const base64Payload = token.split('.')[1];
    if (!base64Payload) {
      throw new Error('Invalid token format');
    }
    const jsonPayload = atob(base64Payload);
    const payload: unknown = JSON.parse(jsonPayload);

    if (
      typeof payload === 'object' &&
      payload !== null &&
      'sub' in payload &&
      'username' in payload &&
      'role' in payload
    ) {
      const p = payload as { sub: string; username: string; role: string };
      const validRoles = ['operador', 'administrador', 'desenvolvedor'] as const;
      const role = validRoles.includes(p.role as AuthUser['role'])
        ? (p.role as AuthUser['role'])
        : 'operador';

      return { sub: p.sub, username: p.username, role };
    }
    throw new Error('Invalid payload structure');
  } catch {
    return { sub: '', username: 'Usuário', role: 'operador' };
  }
}
