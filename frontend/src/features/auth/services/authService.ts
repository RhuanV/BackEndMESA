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
import { setAccessToken } from '@/lib/api/authToken';
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
  setAccessToken(access_token);

  // Identity comes from the server (GET /me), never from decoding the token.
  // The token is opaque to the client.
  const user = await fetchCurrentUser();

  return { user, token: access_token };
}

/**
 * Exchanges the httpOnly refresh cookie for a fresh access token. Returns the
 * user identity, or null if there is no valid session (e.g. after logout).
 */
export async function refreshSession(): Promise<AuthUser | null> {
  try {
    const { data } = await apiClient.post<{ access_token: string }>('/refresh');
    setAccessToken(data.access_token);
    return await fetchCurrentUser();
  } catch {
    setAccessToken(null);
    return null;
  }
}

/** Ends the session on the server (clears the refresh cookie). */
export async function logoutUser(): Promise<void> {
  try {
    await apiClient.post('/logout');
  } finally {
    setAccessToken(null);
  }
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

const VALID_ROLES = ['operador', 'administrador', 'desenvolvedor'] as const;

/**
 * Fetches the authenticated user's identity from the server (GET /me).
 *
 * The access token is attached by the axios request interceptor. Role and
 * username are the server's answer, never derived from decoding the token.
 */
async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<{ username: string; role: string }>('/me');
  const { username, role } = response.data;
  if (
    typeof username !== 'string' ||
    !VALID_ROLES.includes(role as AuthUser['role'])
  ) {
    throw new Error('Invalid /me response');
  }
  return { username, role: role as AuthUser['role'] };
}
