/**
 * Regions API client (Sprint 5 RF02).
 *
 * Wraps the read-only /regions endpoints used by MunicipalitySelector to build
 * dependent state → municipality dropdowns.
 */
import apiClient from '@/lib/api/axiosInstance';

export interface StateOption {
  readonly codigo_ibge: string;
  readonly sigla_estado: string;
  readonly nome_estado: string;
}

export interface MunicipalityOption {
  readonly codigo_ibge: string;
  readonly nome_municipio: string;
}

export async function listStates(): Promise<StateOption[]> {
  const response = await apiClient.get<{ states: StateOption[] }>('/regions/states');
  return response.data.states;
}

export async function listMunicipalitiesByState(sigla: string): Promise<MunicipalityOption[]> {
  const response = await apiClient.get<{
    sigla_estado: string;
    municipalities: MunicipalityOption[];
  }>(`/regions/states/${encodeURIComponent(sigla)}/municipalities`);
  return response.data.municipalities;
}
