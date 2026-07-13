/**
 * AuditLogPage — Admin-only security/action audit log.
 *
 * Reads the append-only audit trail from GET /audit-logs (administrador,
 * desenvolvedor). The endpoint is the real security boundary; this page only
 * renders what it returns.
 */
import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { sanitize } from '@/lib/security/sanitize';

interface AuditEntry {
  readonly id: number;
  readonly username: string | null;
  readonly user_role: string | null;
  readonly action: string;
  readonly resource: string | null;
  readonly detail: string | null;
  readonly ip_address: string | null;
  readonly created_at: string;
}

const actionColors: Record<string, string> = {
  LOGIN: 'bg-blue-100 text-blue-700',
  LOGIN_FAILED: 'bg-red-100 text-red-700',
  LOGOUT: 'bg-neutral-100 text-neutral-600',
  USER_CREATE: 'bg-emerald-100 text-emerald-700',
  USER_DELETE: 'bg-rose-100 text-rose-700',
  USER_EDIT: 'bg-purple-100 text-purple-700',
  ANALYSIS_RUN: 'bg-teal-100 text-teal-700',
  EXPORT: 'bg-amber-100 text-amber-700',
  DEV_WRITE_BLOCKED: 'bg-orange-100 text-orange-700',
};

/** Formats an ISO timestamp as a compact local date/time. */
function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString('pt-BR');
}

export function AuditLogPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await apiClient.get<AuditEntry[]>('/audit-logs');
      setLogs(res.data);
      setError(null);
    } catch {
      setError('Erro ao carregar o log de auditoria.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load on mount
    void fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Auditoria de Acessos</h2>
          <p className="mt-1 text-sm text-neutral-500">Log de ações realizadas no sistema.</p>
        </div>
        <button
          onClick={() => void fetchLogs()}
          className="rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-primary-700 transition-colors"
          type="button"
        >
          Atualizar
        </button>
      </div>

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      <div className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Log de auditoria">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Data/Hora</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Usuário</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Ação</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Detalhes</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Origem</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-neutral-600">{formatTimestamp(log.created_at)}</td>
                  <td className="px-4 py-3 font-medium text-neutral-900">{log.username ? sanitize(log.username) : '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${actionColors[log.action] ?? 'bg-neutral-100 text-neutral-700'}`}>
                      {sanitize(log.action)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-500 text-xs">{log.detail ? sanitize(log.detail) : '—'}</td>
                  <td className="px-4 py-3 font-mono text-xs text-neutral-400">{log.ip_address ? sanitize(log.ip_address) : '—'}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-neutral-400">Nenhum evento registrado.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
