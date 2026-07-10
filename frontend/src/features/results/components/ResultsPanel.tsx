/**
 * ResultsPanel — Summary statistics and ranking overview.
 *
 * Sprint 2: ranking now comes from GET /ranking (real DB rows scored on the
 * backend). Mock fallback removed — empty state handled by RankingTable.
 *
 * Security: All data is sanitized before rendering.
 */
import { useEffect, useState } from 'react';
import { RankingTable } from './RankingTable';
import { getRanking } from '@/features/results/services/rankingService';
import type { MesaRankingResult } from '@/types';

interface StatCardProps {
  readonly label: string;
  readonly value: string | number;
  readonly icon: string;
  readonly color: string;
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <span className="text-lg" aria-hidden="true">{icon}</span>
        </div>
        <div>
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">{label}</p>
          <p className="text-xl font-bold text-neutral-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

export function ResultsPanel() {
  const [results, setResults] = useState<MesaRankingResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading state before the fetch
    setIsLoading(true);
    getRanking()
      .then((data) => {
        if (!cancelled) {
          setResults(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Erro ao carregar ranqueamento.';
          setError(message);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const bestScore = results.length > 0
    ? Math.max(...results.map((r) => r.totalScore))
    : 0;

  const avgScore = results.length > 0
    ? results.reduce((sum, r) => sum + r.totalScore, 0) / results.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Sítios Avaliados"
          value={isLoading ? '…' : results.length}
          icon="📍"
          color="bg-primary-600/10"
        />
        <StatCard
          label="Melhor Score"
          value={isLoading ? '…' : bestScore}
          icon="⭐"
          color="bg-green-500/10"
        />
        <StatCard
          label="Média Geral"
          value={isLoading ? '…' : avgScore.toFixed(1)}
          icon="📊"
          color="bg-accent-500/10"
        />
        <StatCard
          label="Classificação"
          value="MESA-Auto"
          icon="🏛️"
          color="bg-warning-500/10"
        />
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">
          {error}
        </div>
      )}

      {/* Ranking Table */}
      <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-neutral-900">
            Ranqueamento de Sítios
          </h3>
          <p className="text-sm text-neutral-500">
            Classificação baseada nos critérios do Manual de Apoio MESA 2021
          </p>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-sm text-neutral-400">
            Carregando ranqueamento…
          </div>
        ) : (
          <RankingTable data={results} />
        )}
      </div>
    </div>
  );
}
