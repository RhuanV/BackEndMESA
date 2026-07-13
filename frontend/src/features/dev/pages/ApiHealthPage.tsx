/**
 * ApiHealthPage — Dev-only API health dashboard.
 *
 * Reads GET /health/detailed, which checks the real dependencies (PostgreSQL/
 * PostGIS, Airflow, disk, memory) server-side and reports each with a status,
 * latency and a human-readable detail. Replaces the previous client-side guess
 * that pinged endpoints (two of which always failed).
 */
import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { sanitize } from '@/lib/security/sanitize';

type CheckStatus = 'ok' | 'error' | 'degraded' | 'unknown';

interface HealthCheck {
  readonly name: string;
  readonly status: CheckStatus;
  readonly latency_ms?: number | null;
  readonly detail?: string | null;
}

interface HealthReport {
  readonly status: CheckStatus;
  readonly checked_at: string;
  readonly checks: HealthCheck[];
}

const dotColor: Record<CheckStatus, string> = {
  ok: 'bg-green-500',
  error: 'bg-red-500',
  degraded: 'bg-amber-500',
  unknown: 'bg-neutral-300',
};

const aggregateLabel: Record<CheckStatus, string> = {
  ok: 'Todos os serviços operacionais',
  degraded: 'Operacional com degradação',
  error: 'Falha crítica detectada',
  unknown: 'Estado desconhecido',
};

export function ApiHealthPage() {
  const [report, setReport] = useState<HealthReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastCheck, setLastCheck] = useState<string>('');

  const checkHealth = useCallback(async () => {
    try {
      const res = await apiClient.get<HealthReport>('/health/detailed', { timeout: 8000 });
      setReport(res.data);
      setError(null);
    } catch {
      setError('Não foi possível obter a saúde da API.');
    } finally {
      setLastCheck(new Date().toLocaleTimeString('pt-BR'));
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- checagem inicial; depois roda em polling
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

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      {report && (
        <div className="mb-4 flex items-center gap-3 rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
          <div className={`h-3 w-3 rounded-full ${dotColor[report.status]}`} />
          <p className="text-sm font-semibold text-neutral-900">{aggregateLabel[report.status]}</p>
        </div>
      )}

      <div className="space-y-3">
        {(report?.checks ?? []).map((check) => (
          <div key={check.name} className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className={`h-3 w-3 rounded-full ${dotColor[check.status] ?? dotColor.unknown}`} />
              <div>
                <p className="text-sm font-medium text-neutral-900">{sanitize(check.name)}</p>
                {check.detail && <p className="text-xs text-neutral-400">{sanitize(check.detail)}</p>}
              </div>
            </div>
            {check.latency_ms != null && (
              <span className={`text-xs font-semibold ${check.latency_ms < 200 ? 'text-green-600' : check.latency_ms < 1000 ? 'text-amber-600' : 'text-red-600'}`}>
                {check.latency_ms}ms
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
