/**
 * AnalysisPage — MESA analysis configuration and execution.
 */
import { AnalysisConfigPanel } from '@/features/analysis/components/AnalysisConfigPanel';

export function AnalysisPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">
          Análise MESA — Configuração MCDA
        </h2>
        <p className="mt-2 text-sm text-neutral-500">
          Configure os pesos relativos para cada critério do índice de adequabilidade.
          A soma dos pesos deve totalizar 100%.
        </p>
      </div>

      <div className="rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
        <AnalysisConfigPanel />
      </div>
    </div>
  );
}
