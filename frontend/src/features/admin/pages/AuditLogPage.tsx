/**
 * AuditLogPage — Admin-only access audit log.
 */
import { sanitize } from '@/lib/security/sanitize';

/** Mock audit log for Sprint 2 */
const MOCK_LOGS = [
  { id: 1, timestamp: '2026-04-23 14:22:05', user: 'analyst1', action: 'LOGIN', detail: 'Login via /api/login' },
  { id: 2, timestamp: '2026-04-23 14:23:12', user: 'analyst1', action: 'ANALYSIS', detail: 'MCDA analysis submitted (id: abc-123)' },
  { id: 3, timestamp: '2026-04-23 14:35:00', user: 'admin1', action: 'USER_EDIT', detail: 'Changed role: analyst2 → admin' },
  { id: 4, timestamp: '2026-04-23 14:40:30', user: 'analyst2', action: 'EXPORT', detail: 'Exported Shapefile (region: SP)' },
  { id: 5, timestamp: '2026-04-23 15:01:18', user: 'dev1', action: 'DEBUG', detail: 'Debug mode enabled' },
];

const actionColors: Record<string, string> = {
  LOGIN: 'bg-blue-100 text-blue-700',
  ANALYSIS: 'bg-teal-100 text-teal-700',
  USER_EDIT: 'bg-purple-100 text-purple-700',
  EXPORT: 'bg-amber-100 text-amber-700',
  DEBUG: 'bg-neutral-100 text-neutral-600',
};

export function AuditLogPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Auditoria de Acessos</h2>
        <p className="mt-1 text-sm text-neutral-500">Log de ações realizadas no sistema.</p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden">
        <table className="w-full text-sm" aria-label="Log de auditoria">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50">
              <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Data/Hora</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Usuário</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Ação</th>
              <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_LOGS.map((log) => (
              <tr key={log.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-neutral-600">{log.timestamp}</td>
                <td className="px-4 py-3 font-medium text-neutral-900">{sanitize(log.user)}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${actionColors[log.action] ?? 'bg-neutral-100 text-neutral-700'}`}>
                    {log.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{sanitize(log.detail)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
