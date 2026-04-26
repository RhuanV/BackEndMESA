/**
 * ResultsPage — MESA results and ranking page.
 */
import { ResultsPanel } from '@/features/results/components/ResultsPanel';

export function ResultsPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">
          Resultados — Ranqueamento MESA
        </h2>
        <p className="mt-2 text-sm text-neutral-500">
          Visualização do ranqueamento dos sítios aeroportuários avaliados
          conforme a metodologia MESA-Auto.
        </p>
      </div>

      <ResultsPanel />
    </div>
  );
}
