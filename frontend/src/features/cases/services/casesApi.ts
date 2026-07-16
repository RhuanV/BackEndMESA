/**
 * Cases (Caso/Projeto) API client — MESA case lifecycle.
 *
 * Authenticated via the shared axios instance; the backend gates create/manage
 * on the case roles and audits status transitions.
 */
import apiClient from '@/lib/api/axiosInstance';

export type CaseStatus = 'iniciado' | 'em_analise' | 'campo' | 'concluido';

export interface CaseSummary {
  readonly id: number;
  readonly nome: string;
  readonly descricao: string | null;
  readonly coordenadorId: number | null;
  readonly estadoUf: string | null;
  readonly municipioIbgeCode: string | null;
  readonly status: CaseStatus;
  readonly siteCount: number;
  readonly createdAt: string | null;
  readonly updatedAt: string | null;
}

export interface CaseSite {
  readonly id: number;
  readonly site_name: string;
  readonly site_status: string;
  readonly avoidance_violation: boolean;
  readonly observacao: string | null;
  readonly latitude: number;
  readonly longitude: number;
}

export interface CaseDetail extends CaseSummary {
  readonly sites: readonly CaseSite[];
}

export interface CreateCasePayload {
  readonly nome: string;
  readonly descricao?: string;
  readonly estado_uf?: string;
  readonly municipio_ibge_code?: string;
  readonly coordenador_id?: number | null;
}

export async function listCases(status?: CaseStatus): Promise<CaseSummary[]> {
  const res = await apiClient.get<{ cases: CaseSummary[] }>('/cases', {
    params: status ? { status } : undefined,
  });
  return res.data.cases;
}

export async function getCase(id: number): Promise<CaseDetail> {
  const res = await apiClient.get<CaseDetail>(`/cases/${id}`);
  return res.data;
}

export async function createCase(payload: CreateCasePayload): Promise<CaseSummary> {
  const res = await apiClient.post<CaseSummary>('/cases', payload);
  return res.data;
}

export async function changeCaseStatus(id: number, status: CaseStatus): Promise<CaseDetail> {
  const res = await apiClient.post<CaseDetail>(`/cases/${id}/status`, { status });
  return res.data;
}

export async function linkCaseSite(id: number, assessmentId: number): Promise<void> {
  await apiClient.post(`/cases/${id}/sites`, { assessment_id: assessmentId });
}
