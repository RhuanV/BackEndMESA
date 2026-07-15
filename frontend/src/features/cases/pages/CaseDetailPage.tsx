/**
 * CaseDetailPage — single case: lifecycle transitions and linked candidate sites.
 *
 * Status transitions call POST /cases/{id}/status (adjacent-state rule enforced
 * on the backend and audited). Managers (administrador/desenvolvedor) see the
 * transition and site-linking controls.
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button, Input } from '@/components/ui';
import { extractErrorDetail } from '@/lib/api/errors';
import { sanitize } from '@/lib/security/sanitize';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  changeCaseStatus,
  getCase,
  linkCaseSite,
  type CaseDetail,
  type CaseStatus,
} from '@/features/cases/services/casesApi';
import { STATUS_COLORS, STATUS_LABELS, STATUS_ORDER } from '@/features/cases/constants';

/** Adjacent-state targets (mirrors the backend rule) for the transition buttons. */
function adjacentTargets(status: CaseStatus): CaseStatus[] {
  const i = STATUS_ORDER.indexOf(status);
  return STATUS_ORDER.filter((_, idx) => Math.abs(idx - i) === 1);
}

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const caseId = Number(id);
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user?.role === 'administrador' || user?.role === 'desenvolvedor';

  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [assessmentId, setAssessmentId] = useState('');

  const fetchCase = useCallback(async () => {
    try {
      setDetail(await getCase(caseId));
      setError(null);
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Erro ao carregar o caso.');
    } finally {
      setIsLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load on mount
    void fetchCase();
  }, [fetchCase]);

  const handleTransition = async (target: CaseStatus) => {
    setBusy(true);
    setError(null);
    try {
      setDetail(await changeCaseStatus(caseId, target));
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Não foi possível alterar o status.');
    } finally {
      setBusy(false);
    }
  };

  const handleLinkSite = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const aid = Number(assessmentId);
    if (!Number.isInteger(aid) || aid <= 0) return;
    setBusy(true);
    setError(null);
    try {
      await linkCaseSite(caseId, aid);
      setAssessmentId('');
      await fetchCase();
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Não foi possível vincular o sítio.');
    } finally {
      setBusy(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <p className="text-danger-600">{error ?? 'Caso não encontrado.'}</p>
        <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/cases')}>
          ← Voltar
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <button
        onClick={() => navigate('/dashboard/cases')}
        className="mb-4 text-sm text-primary-600 hover:underline"
      >
        ← Voltar para casos
      </button>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">{sanitize(detail.nome)}</h2>
          {detail.descricao && <p className="mt-1 text-sm text-neutral-500">{sanitize(detail.descricao)}</p>}
          <p className="mt-1 text-xs text-neutral-400">
            Município {sanitize(detail.municipioIbgeCode ?? '—')} · UF {sanitize(detail.estadoUf ?? '—')}
          </p>
        </div>
        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${STATUS_COLORS[detail.status]}`}>
          {STATUS_LABELS[detail.status]}
        </span>
      </div>

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      {/* Lifecycle stepper */}
      <div className="mb-8 rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-neutral-900">Ciclo de Vida</h3>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {STATUS_ORDER.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${s === detail.status ? STATUS_COLORS[s] : 'bg-neutral-50 text-neutral-400'}`}>
                {STATUS_LABELS[s]}
              </span>
              {i < STATUS_ORDER.length - 1 && <span className="text-neutral-300">→</span>}
            </div>
          ))}
        </div>
        {canManage ? (
          <div className="flex flex-wrap gap-2">
            {adjacentTargets(detail.status).map((target) => (
              <Button key={target} size="sm" variant="secondary" disabled={busy} onClick={() => void handleTransition(target)}>
                Mover para {STATUS_LABELS[target]}
              </Button>
            ))}
          </div>
        ) : (
          <p className="text-xs text-neutral-400">Apenas gestores podem alterar o status.</p>
        )}
      </div>

      {/* Candidate sites */}
      <div className="rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-neutral-900">Sítios Candidatos ({detail.sites.length})</h3>
        {canManage && (
          <form onSubmit={handleLinkSite} className="mb-4 flex items-end gap-2">
            <Input
              label="Vincular sítio (ID do assessment)"
              type="number"
              value={assessmentId}
              onChange={(e) => setAssessmentId(e.target.value)}
              min={1}
            />
            <Button type="submit" size="sm" disabled={busy || !assessmentId}>
              Vincular
            </Button>
          </form>
        )}
        {detail.sites.length === 0 ? (
          <p className="text-sm text-neutral-400">Nenhum sítio vinculado.</p>
        ) : (
          <ul className="divide-y divide-neutral-100">
            {detail.sites.map((s) => (
              <li key={s.id} className="flex items-center justify-between py-2 text-sm">
                <span className="font-medium text-neutral-800">{sanitize(s.site_name)}</span>
                <span className="text-xs text-neutral-500">
                  {sanitize(s.site_status)}
                  {s.avoidance_violation ? ' · ⚠ violação' : ''}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
