/**
 * CaseListPage — lists MESA cases (Caso/Projeto) and creates new ones.
 *
 * Access (Router): operador, administrador, desenvolvedor (read). Creating a
 * case is gated to administrador/desenvolvedor on the backend (CASE_CREATE_ROLES);
 * the create form is shown to those roles as defense in depth.
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button, Input } from '@/components/ui';
import { extractErrorDetail } from '@/lib/api/errors';
import { sanitize } from '@/lib/security/sanitize';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { createCase, listCases, type CaseSummary } from '@/features/cases/services/casesApi';
import { STATUS_COLORS, STATUS_LABELS } from '@/features/cases/constants';

export function CaseListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canCreate = user?.role === 'administrador' || user?.role === 'desenvolvedor';

  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [nome, setNome] = useState('');
  const [descricao, setDescricao] = useState('');
  const [uf, setUf] = useState('');
  const [ibge, setIbge] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCases = useCallback(async () => {
    try {
      setCases(await listCases());
      setError(null);
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Erro ao carregar casos.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load on mount
    void fetchCases();
  }, [fetchCases]);

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      const created = await createCase({
        nome: nome.trim(),
        descricao: descricao.trim() || undefined,
        estado_uf: uf.trim() || undefined,
        municipio_ibge_code: ibge.trim() || undefined,
      });
      setNome('');
      setDescricao('');
      setUf('');
      setIbge('');
      await fetchCases();
      navigate(`/dashboard/cases/${created.id}`);
    } catch (err) {
      setFormError(extractErrorDetail(err) ?? 'Não foi possível criar o caso.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Casos (Projetos)</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Gerencie os casos de prospecção de sítios aeroportuários e seu ciclo de vida.
        </p>
      </div>

      {canCreate && (
        <div className="mb-8 rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-neutral-900">Novo Caso</h3>
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
            <Input label="Nome" value={nome} onChange={(e) => setNome(e.target.value)} required minLength={1} />
            <Input label="Descrição" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
            <Input label="UF (alvo)" value={uf} onChange={(e) => setUf(e.target.value)} maxLength={2} />
            <Input label="Município (código IBGE)" value={ibge} onChange={(e) => setIbge(e.target.value)} maxLength={7} />
            <div className="sm:col-span-2 flex items-center justify-between gap-4">
              <div className="text-sm" aria-live="polite">
                {formError && <p role="alert" className="text-danger-600">{formError}</p>}
              </div>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Criando...' : 'Criar Caso'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-surface shadow-sm">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Lista de casos">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Caso</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Município</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Status</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Sítios</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr
                  key={c.id}
                  className="cursor-pointer border-b border-neutral-100 hover:bg-neutral-50"
                  onClick={() => navigate(`/dashboard/cases/${c.id}`)}
                >
                  <td className="px-4 py-3 font-medium text-neutral-900">{sanitize(c.nome)}</td>
                  <td className="px-4 py-3 text-neutral-500">{sanitize(c.municipioIbgeCode ?? '—')}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_COLORS[c.status]}`}>
                      {STATUS_LABELS[c.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-neutral-500">{c.siteCount}</td>
                </tr>
              ))}
              {cases.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-neutral-400">Nenhum caso cadastrado.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
