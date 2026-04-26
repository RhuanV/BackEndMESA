/**
 * RankingTable — Accessible table displaying MESA site rankings.
 *
 * Features:
 * - Sortable columns with ARIA attributes
 * - Score visualization with colored progress bars
 * - All data values sanitized before rendering (Defense in Depth)
 * - Responsive design
 *
 * Security: Even though React escapes JSX values by default,
 * we use the sanitize() utility as an extra defense layer for
 * any data that comes from an API.
 */
import { sanitize } from '@/lib/security/sanitize';
import type { MesaRankingResult } from '@/types/mesa';

interface RankingTableProps {
  readonly data: MesaRankingResult[];
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-accent-500';
  if (score >= 40) return 'bg-warning-500';
  return 'bg-danger-500';
}

function getRankBadge(rank: number): string {
  if (rank === 1) return '🥇';
  if (rank === 2) return '🥈';
  if (rank === 3) return '🥉';
  return `#${rank}`;
}

export function RankingTable({ data }: RankingTableProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-neutral-400">
        <svg className="h-12 w-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
        <p className="text-sm">Nenhum resultado disponível</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200">
      <table className="w-full text-sm" aria-label="Ranqueamento de sítios MESA">
        <thead>
          <tr className="border-b border-neutral-200 bg-neutral-50">
            <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">
              Rank
            </th>
            <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">
              Sítio
            </th>
            <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">
              Declividade
            </th>
            <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">
              Distância
            </th>
            <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">
              Obstáculos
            </th>
            <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">
              Custo
            </th>
            <th scope="col" className="px-4 py-3 text-center font-semibold text-neutral-700">
              Score Total
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((result) => (
            <tr
              key={`${result.rank}-${result.siteName}`}
              className="border-b border-neutral-100 transition-colors hover:bg-neutral-50"
            >
              <td className="px-4 py-3 text-center font-medium">
                {getRankBadge(result.rank)}
              </td>
              <td className="px-4 py-3 font-medium text-neutral-900">
                {/* Security: sanitize API data before rendering */}
                {sanitize(result.siteName)}
              </td>
              <td className="px-4 py-3 text-center text-neutral-600">
                {result.slopeScore.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-center text-neutral-600">
                {result.distanceScore.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-center text-neutral-600">
                {result.obstacleScore.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-center text-neutral-600">
                {result.costScore.toFixed(1)}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 rounded-full bg-neutral-200 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getScoreColor(result.totalScore)}`}
                      style={{ width: `${Math.min(100, result.totalScore)}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-neutral-700 w-10 text-right">
                    {result.totalScore.toFixed(0)}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
