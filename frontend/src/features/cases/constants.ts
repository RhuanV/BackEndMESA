/** Shared display constants for MESA case lifecycle status. */
import type { CaseStatus } from '@/features/cases/services/casesApi';

export const STATUS_LABELS: Record<CaseStatus, string> = {
  iniciado: 'Iniciado',
  em_analise: 'Em Análise',
  campo: 'Campo',
  concluido: 'Concluído',
};

export const STATUS_COLORS: Record<CaseStatus, string> = {
  iniciado: 'bg-neutral-100 text-neutral-700',
  em_analise: 'bg-amber-100 text-amber-700',
  campo: 'bg-sky-100 text-sky-700',
  concluido: 'bg-emerald-100 text-emerald-700',
};

/** Ordered lifecycle (mirrors the backend STATUS_ORDER). */
export const STATUS_ORDER: CaseStatus[] = ['iniciado', 'em_analise', 'campo', 'concluido'];
