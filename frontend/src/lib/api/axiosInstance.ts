/**
 * Axios instance for GeoAvia API communication.
 *
 * Security features:
 * - Access token attached from an in-memory store (never localStorage).
 * - withCredentials: true so the httpOnly refresh cookie is sent to /refresh.
 * - On 401, transparently refreshes the access token once and retries; if the
 *   refresh fails, redirects to login.
 * - No sensitive data logged to console.
 */
import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { getAccessToken, setAccessToken } from './authToken';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true, // send/receive the httpOnly refresh cookie
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 15000, // 15 second timeout to prevent hanging requests
});

// Attach the current access token (if any) to every request.
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

/** Endpoints that must never trigger the refresh-and-retry flow. */
function isAuthEndpoint(url: string | undefined): boolean {
  return !!url && (url.includes('/refresh') || url.includes('/login'));
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!axios.isAxiosError(error) || !error.response) {
      // Network / timeout / 5xx without response — never expose details.
      return Promise.reject(new Error('Erro de comunicação com o servidor.'));
    }

    const { status } = error.response;
    const original = error.config as RetriableConfig | undefined;

    // 401: try to refresh the access token once, then replay the request.
    if (status === 401 && original && !original._retry && !isAuthEndpoint(original.url)) {
      original._retry = true;
      try {
        const { data } = await apiClient.post<{ access_token: string }>('/refresh');
        setAccessToken(data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return await apiClient(original);
      } catch {
        setAccessToken(null);
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(new Error('Sessão expirada. Faça login novamente.'));
      }
    }

    if (status === 401) {
      setAccessToken(null);
      return Promise.reject(new Error('Sessão expirada. Faça login novamente.'));
    }

    if (status === 403) {
      return Promise.reject(new Error('Acesso negado. Permissão insuficiente.'));
    }

    // 4xx (400/404/422/429/…): pass the original error so callers can read
    // error.response.data.detail for user feedback.
    if (status < 500) {
      return Promise.reject(error);
    }

    return Promise.reject(new Error('Erro de comunicação com o servidor.'));
  }
);

export default apiClient;
