/**
 * ResultsPanel — Summary statistics and ranking overview.
 *
 * Displays:
 * - Summary statistics cards (total sites, best score, etc.)
 * - RankingTable with sortable results
 * - Uses mock data for Sprint 1 demonstration
 *
 * Security: All data is sanitized before rendering.
 */
import { RankingTable } from './RankingTable';
import type { MesaRankingResult } from '@/types/mesa';

/** Mock data for Sprint 1 demonstration */
const MOCK_RESULTS: MesaRankingResult[] = [
  {
    rank: 1,
    siteName: 'Sítio Aeroportuário Norte — Campinas',
    totalScore: 87,
    slopeScore: 92,
    distanceScore: 85,
    obstacleScore: 90,
    costScore: 81,
    latitude: -22.9,
    longitude: -47.06,
  },
  {
    rank: 2,
    siteName: 'Sítio Vale do Ribeira',
    totalScore: 74,
    slopeScore: 78,
    distanceScore: 70,
    obstacleScore: 80,
    costScore: 68,
    latitude: -24.5,
    longitude: -47.8,
  },
  {
    rank: 3,
    siteName: 'Sítio Planalto Central — Goiás',
    totalScore: 68,
    slopeScore: 65,
    distanceScore: 75,
    obstacleScore: 60,
    costScore: 72,
    latitude: -15.8,
    longitude: -49.3,
  },
  {
    rank: 4,
    siteName: 'Sítio Litoral Sul — Florianópolis',
    totalScore: 55,
    slopeScore: 50,
    distanceScore: 60,
    obstacleScore: 45,
    costScore: 65,
    latitude: -27.6,
    longitude: -48.5,
  },
  {
    rank: 5,
    siteName: 'Sítio Serra da Mantiqueira',
    totalScore: 42,
    slopeScore: 30,
    distanceScore: 55,
    obstacleScore: 35,
    costScore: 48,
    latitude: -22.4,
    longitude: -45.0,
  },
];

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
  // In Sprint 1, we use mock data. In production, this will come from the API.
  const results = MOCK_RESULTS;

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
          value={results.length}
          icon="📍"
          color="bg-primary-600/10"
        />
        <StatCard
          label="Melhor Score"
          value={bestScore}
          icon="⭐"
          color="bg-green-500/10"
        />
        <StatCard
          label="Média Geral"
          value={avgScore.toFixed(1)}
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
        <RankingTable data={results} />
      </div>
    </div>
  );
}
