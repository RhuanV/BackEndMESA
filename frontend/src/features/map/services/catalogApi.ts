/**
 * Metadata Catalog API client (RF01).
 *
 * Fetches layer metadata from the backend catalog (mesa_a.layer_catalog),
 * which is populated from the metadata spreadsheet — the single source of
 * truth. The frontend keeps only the visual configuration (paint/colors/order);
 * metadata (source, last update, EPSG, periodicity, notes, address) comes from
 * this API.
 *
 * Security: values are sanitized at render time (MetadataModal) via DOMPurify.
 */
import apiClient from '@/lib/api/axiosInstance';

export type CatalogGroup = 'base' | 'analysis' | 'exclusion';
export type CatalogDataType = 'vector' | 'raster';

export interface CatalogLayer {
  readonly id: number;
  readonly layer_key: string;
  readonly tema: string | null;
  readonly plano_informacao: string | null;
  readonly fonte: string | null;
  readonly fonte_principal: boolean;
  readonly data_atualizacao_fonte: string | null;
  readonly periodicidade: string | null;
  readonly segregacao: string | null;
  readonly datum: string | null;
  readonly epsg: string | null;
  readonly formato: string | null;
  readonly geometria: string | null;
  readonly observacoes: string | null;
  readonly endereco: string | null;
  readonly grupo: CatalogGroup | null;
  readonly data_type: CatalogDataType;
  readonly backend_table: string | null;
  readonly available: boolean;
}

interface CatalogListResponse {
  readonly layers: readonly CatalogLayer[];
}

export interface CatalogFilters {
  readonly tema?: string;
  readonly grupo?: CatalogGroup;
}

/** Lists catalog entries, optionally filtered by tema/grupo. */
export async function listCatalogLayers(filters?: CatalogFilters): Promise<CatalogLayer[]> {
  const params: Record<string, string> = {};
  if (filters?.tema) params['tema'] = filters.tema;
  if (filters?.grupo) params['grupo'] = filters.grupo;

  const response = await apiClient.get<CatalogListResponse>('/catalog/layers', { params });
  return [...response.data.layers];
}

/** Fetches a single catalog entry by its layer_key. */
export async function getCatalogLayer(layerKey: string): Promise<CatalogLayer> {
  const response = await apiClient.get<CatalogLayer>(
    `/catalog/layers/${encodeURIComponent(layerKey)}`,
  );
  return response.data;
}
