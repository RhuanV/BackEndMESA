/**
 * Axios instance for GeoAvia API communication.
 *
 * Security features:
 * - withCredentials: true for HttpOnly cookie support
 * - Global 401/403 interceptor to handle auth failures
 * - No sensitive data logged to console
 * - Base URL from environment variables (never hardcoded)
 */
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true, // Required for HttpOnly cookies (future backend migration)
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 15000, // 15 second timeout to prevent hanging requests
});

/**
 * Response interceptor: Global error handling.
 *
 * - 401: Session expired or invalid → redirect to login
 * - 403: Insufficient permissions → user stays on page, sees access denied
 * - Other errors: Generic handling, never expose technical details
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const { status } = error.response;

      if (status === 401) {
        // Session expired — clear any client-side state and redirect
        window.location.href = '/login';
        return Promise.reject(new Error('Sessão expirada. Faça login novamente.'));
      }

      if (status === 403) {
        return Promise.reject(new Error('Acesso negado. Permissão insuficiente.'));
      }

      // 4xx validation errors (400, 404, 422, …): pass through with the original
      // axios error so callers can read error.response.data.detail for user feedback.
      if (status < 500) {
        return Promise.reject(error);
      }
    }

    // 5xx and network errors — never expose technical details to the user
    return Promise.reject(new Error('Erro de comunicação com o servidor.'));
  }
);

export default apiClient;
