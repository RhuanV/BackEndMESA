/**
 * In-memory access-token store shared by the axios instance and the auth layer.
 *
 * Security: the access token lives only in a module variable (never in
 * localStorage/sessionStorage), so it is not exposed to trivial XSS scraping.
 * Persistence across refreshes is handled by the httpOnly refresh cookie + the
 * /refresh endpoint, not by the client storing the token.
 */
let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}
