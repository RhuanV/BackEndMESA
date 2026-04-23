/**
 * ApiHealthPage — Dev-only API health check dashboard.
 */
import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api/axiosInstance';

interface HealthEndpoint {
  readonly name: string;
  readonly path: string;
  status: 'ok' | 'error' | 'loading';
  responseMs: number | null;
}

const ENDPOINTS: { name: string; path: string }[] = [
  { name: 'Backend Health', path: '/health' },
  { name: 'Auth Service', path: '/login' },
  { name: 'Assessments API', path: '/assessments' },
  { name: 'Analysis API', path: '/analysis/status/ping' },
];

export function ApiHealthPage() {
  const [health, setHealth] = useState<HealthEndpoint[]>(
    ENDPOINTS.map((e) => ({ ...e, status: 'loading', responseMs: null }))
  );
  const [lastCheck, setLastCheck] = useState<string>('');

  const checkHealth = useCallback(async () => {
    const results = await Promise.all(
      ENDPOINTS.map(async (ep) => {
        const start = performance.now();
        try {
          await apiClient.get(ep.path, { timeout: 5000 });
          return { ...ep, status: 'ok' as const, responseMs: Math.round(performance.now() - start) };
        } catch {
          return { ...ep, status: 'error' as const, responseMs: Math.round(performance.now() - start) };
        }
      })
    );
    setHealth(results);
    setLastCheck(new Date().toLocaleTimeString('pt-BR'));
  }, []);

  useEffect(() => {
    void checkHealth();
    const interval = setInterval(() => void checkHealth(), 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Saúde da API</h2>
          <p className="mt-1 text-sm text-neutral-500">Auto-refresh a cada 30s • Último check: {lastCheck}</p>
        </div>
        <button
          onClick={() => void checkHealth()}
          className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-700 transition-colors"
          type="button"
        >
          Atualizar
        </button>
      </div>

      <div className="space-y-3">
        {health.map((ep) => (
          <div key={ep.path} className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className={`h-3 w-3 rounded-full ${
                ep.status === 'ok' ? 'bg-green-500' : ep.status === 'error' ? 'bg-red-500' : 'bg-neutral-300 animate-pulse'
              }`} />
              <div>
                <p className="text-sm font-medium text-neutral-900">{ep.name}</p>
                <p className="text-xs font-mono text-neutral-400">{ep.path}</p>
              </div>
            </div>
            <div className="text-right">
              {ep.responseMs !== null && (
                <span className={`text-xs font-semibold ${ep.responseMs < 200 ? 'text-green-600' : ep.responseMs < 1000 ? 'text-amber-600' : 'text-red-600'}`}>
                  {ep.responseMs}ms
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
