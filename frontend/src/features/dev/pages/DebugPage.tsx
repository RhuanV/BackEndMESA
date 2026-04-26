/**
 * DebugPage — Dev-only debug mode configuration.
 */
export function DebugPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Debug Mode</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Ferramentas de depuração para desenvolvimento.
        </p>
      </div>
      <div className="space-y-4">
        <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-neutral-800 mb-3">Map Debug</h3>
          <p className="text-xs text-neutral-500 mb-4">
            Use o botão no mapa para ativar coordenadas em tempo real.
          </p>
          <div className="rounded-lg bg-neutral-50 p-3 font-mono text-xs text-neutral-600 space-y-1">
            <div>MODE: {import.meta.env.MODE}</div>
            <div>API: {import.meta.env.VITE_API_BASE_URL}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
