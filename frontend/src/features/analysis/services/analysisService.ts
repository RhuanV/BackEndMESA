/**
 * Analysis API service for GeoAvia.
 *
 * Handles communication with the backend for MESA analysis operations.
 * All data is validated by Zod before reaching this service.
 */
import apiClient from '@/lib/api/axiosInstance';
import type { AnalysisConfig } from '@/features/analysis/schemas/analysisSchema';

export interface AnalysisStatusResponse {
  readonly id: string;
  readonly status: 'pending' | 'processing' | 'completed' | 'failed';
  readonly progress: number; // 0-100
  readonly resultUrl?: string;
  readonly error?: string;
}

/**
 * Submits an MCDA analysis configuration to the backend.
 * Returns an analysis job ID for progress tracking.
 */
export async function submitAnalysis(config: AnalysisConfig): Promise<{ id: string }> {
  const response = await apiClient.post<{ id: string }>('/analysis/run', config);
  return response.data;
}

/**
 * Polls the status of an ongoing analysis job.
 */
export async function getAnalysisStatus(id: string): Promise<AnalysisStatusResponse> {
  const response = await apiClient.get<AnalysisStatusResponse>(`/analysis/status/${id}`);
  return response.data;
}

/**
 * Downloads analysis results as a blob (for Shapefile/GeoTIFF export).
 */
export async function downloadExport(
  format: 'shapefile' | 'geotiff',
  options?: { analysisId?: string; codigoIbge?: string },
): Promise<Blob> {
  const params: Record<string, string> = {};
  if (options?.analysisId) params['analysisId'] = options.analysisId;
  // GeoTIFF is the MCDA suitability raster for a município (Fase 5).
  if (options?.codigoIbge) params['codigo_ibge'] = options.codigoIbge;
  const response = await apiClient.get(`/export/${format}`, {
    params,
    responseType: 'blob',
    timeout: 60000, // 60s for large exports
  });
  return response.data as Blob;
}
