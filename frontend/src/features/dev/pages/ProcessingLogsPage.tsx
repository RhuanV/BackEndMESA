/**
 * ProcessingLogsPage — Dev-only processing logs.
 *
 * Real data from GET /processing-logs: recent Airflow DAG runs (data-ingestion
 * pipeline) plus backend MCDA jobs persisted in processing_log. If Airflow is
 * unreachable the page still renders the persisted jobs and shows a warning.
 */
import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { sanitize } from '@/lib/security/sanitize';

interface AirflowRun {
  readonly job: string | null;
  readonly run_id: string | null;
  readonly status: string;
  readonly started_at: string | null;
  readonly ended_at: string | null;
  readonly duration_ms: number | null;
}

interface ProcessingJob {
  readonly id: number;
  readonly job: string;
  readonly layer: string | null;
  readonly status: string;
  readonly duration_ms: number | null;
  readonly detail: string | null;
  readonly created_at: string;
}

interface ProcessingLogsResponse {
  readonly airflow_runs: AirflowRun[];
  readonly airflow_error: string | null;
  readonly jobs: ProcessingJob[];
}

const statusColors: Record<string, string> = {
  completed: 'text-green-600',
  processing: 'text-amber-600',
  failed: 'text-red-600',
};

/** Formats a duration in ms as seconds (e.g. 12300 → "12.3s"), or "—". */
function formatDuration(ms: number | null): string {
  return ms == null ? '—' : `${(ms / 1000).toFixed(1)}s`;
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString('pt-BR');
}

export function ProcessingLogsPage() {
  const [data, setData] = useState<ProcessingLogsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await apiClient.get<ProcessingLogsResponse>('/processing-logs');
      setData(res.data);
      setError(null);
    } catch {
      setError('Erro ao carregar os logs de processamento.');
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
          <h2 className="text-2xl font-bold text-neutral-900">Logs de Processamento</h2>
          <p className="mt-1 text-sm text-neutral-500">Execuções de ingestão (Airflow) e jobs de análise MCDA.</p>
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

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Airflow DAG runs — real data-ingestion pipeline */}
          <section>
            <h3 className="mb-2 text-sm font-semibold text-neutral-700">Ingestão de dados (Airflow)</h3>
            {data?.airflow_error && (
              <div role="alert" className="mb-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-xs text-amber-700">
                Airflow indisponível: {sanitize(data.airflow_error)}
              </div>
            )}
            <div className="rounded-xl border border-neutral-200 bg-surface shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono" aria-label="DAG runs do Airflow">
                  <thead>
                    <tr className="border-b border-neutral-200 bg-neutral-50">
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Início</th>
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">DAG</th>
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Run ID</th>
                      <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">Status</th>
                      <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Duração</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.airflow_runs ?? []).map((run) => (
                      <tr key={run.run_id ?? `${run.job}-${run.started_at}`} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                        <td className="px-4 py-2.5 text-neutral-500">{formatTimestamp(run.started_at)}</td>
                        <td className="px-4 py-2.5 text-primary-600">{run.job ? sanitize(run.job) : '—'}</td>
                        <td className="px-4 py-2.5 text-neutral-700">{run.run_id ? sanitize(run.run_id) : '—'}</td>
                        <td className={`px-4 py-2.5 text-center font-semibold ${statusColors[run.status] ?? 'text-neutral-600'}`}>
                          {sanitize(run.status)}
                        </td>
                        <td className="px-4 py-2.5 text-right text-neutral-500">{formatDuration(run.duration_ms)}</td>
                      </tr>
                    ))}
                    {(data?.airflow_runs ?? []).length === 0 && (
                      <tr><td colSpan={5} className="px-4 py-6 text-center text-neutral-400">Nenhuma execução de DAG.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Backend MCDA jobs — persisted in processing_log */}
          <section>
            <h3 className="mb-2 text-sm font-semibold text-neutral-700">Jobs de análise (MCDA)</h3>
            <div className="rounded-xl border border-neutral-200 bg-surface shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono" aria-label="Jobs de análise MCDA">
                  <thead>
                    <tr className="border-b border-neutral-200 bg-neutral-50">
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Timestamp</th>
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Job ID</th>
                      <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Layer</th>
                      <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">Status</th>
                      <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Duração</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.jobs ?? []).map((job) => (
                      <tr key={job.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                        <td className="px-4 py-2.5 text-neutral-500">{formatTimestamp(job.created_at)}</td>
                        <td className="px-4 py-2.5 text-primary-600">{sanitize(job.job)}</td>
                        <td className="px-4 py-2.5 text-neutral-700">{job.layer ? sanitize(job.layer) : '—'}</td>
                        <td className={`px-4 py-2.5 text-center font-semibold ${statusColors[job.status] ?? 'text-neutral-600'}`}>
                          {sanitize(job.status)}
                        </td>
                        <td className="px-4 py-2.5 text-right text-neutral-500">{formatDuration(job.duration_ms)}</td>
                      </tr>
                    ))}
                    {(data?.jobs ?? []).length === 0 && (
                      <tr><td colSpan={5} className="px-4 py-6 text-center text-neutral-400">Nenhum job registrado.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
