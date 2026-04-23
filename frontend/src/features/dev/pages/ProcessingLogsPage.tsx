/**
 * ProcessingLogsPage — Dev-only raster processing logs.
 */

/** Mock processing logs */
const MOCK_PROCESSING_LOGS = [
  { id: 1, timestamp: '2026-04-23 14:23:12', job: 'MCDA-abc123', layer: 'anadem-declividade', status: 'completed', duration: '12.3s' },
  { id: 2, timestamp: '2026-04-23 14:23:18', job: 'MCDA-abc123', layer: 'mapbiomas-uso-solo', status: 'completed', duration: '8.7s' },
  { id: 3, timestamp: '2026-04-23 14:23:25', job: 'MCDA-abc123', layer: 'dnit-rodovias', status: 'completed', duration: '4.2s' },
  { id: 4, timestamp: '2026-04-23 14:23:28', job: 'MCDA-abc123', layer: 'aggregation', status: 'completed', duration: '3.1s' },
  { id: 5, timestamp: '2026-04-23 15:10:01', job: 'MCDA-def456', layer: 'anadem-declividade', status: 'failed', duration: '30.0s' },
];

const statusColors: Record<string, string> = {
  completed: 'text-green-600',
  processing: 'text-amber-600',
  failed: 'text-red-600',
};

export function ProcessingLogsPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Logs de Processamento</h2>
        <p className="mt-1 text-sm text-neutral-500">Logs de processamento raster e vetorial.</p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono" aria-label="Logs de processamento">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Timestamp</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Job ID</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Layer</th>
                <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">Status</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Duration</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_PROCESSING_LOGS.map((log) => (
                <tr key={log.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-2.5 text-neutral-500">{log.timestamp}</td>
                  <td className="px-4 py-2.5 text-primary-600">{log.job}</td>
                  <td className="px-4 py-2.5 text-neutral-700">{log.layer}</td>
                  <td className={`px-4 py-2.5 text-center font-semibold ${statusColors[log.status] ?? 'text-neutral-600'}`}>
                    {log.status}
                  </td>
                  <td className="px-4 py-2.5 text-right text-neutral-500">{log.duration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
