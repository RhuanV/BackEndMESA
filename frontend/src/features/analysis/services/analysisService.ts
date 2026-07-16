/**
 * Analysis API service for GeoAvia.
 *
 * Handles communication with the backend for MESA analysis operations.
 * All data is validated by Zod before reaching this service.
 */
import apiClient from '@/lib/api/axiosInstance';
import type { AnalysisConfig } from '@/features/analysis/schemas/analysisSchema';

/** Map-overlay + summary the backend returns when the MCDA job completes. */
export interface AnalysisResult {
  readonly codigoIbge: string;
  readonly bounds: readonly [number, number, number, number];
  readonly pngUrl: string;
  readonly topScore: number | null;
}

export interface AnalysisStatusResponse {
  readonly id: string;
  readonly status: 'pending' | 'processing' | 'completed' | 'failed';
  readonly progress: number; // 0-100
  readonly resultUrl?: string;
  readonly result?: AnalysisResult;
  readonly error?: string;
}

export interface RankedPoint {
  readonly rank: number;
  readonly total_score: number;
  readonly latitude: number;
  readonly longitude: number;
}

export interface SuitabilityMeta {
  readonly codigoIbge: string;
  readonly bounds: readonly [number, number, number, number];
  readonly ranked: readonly RankedPoint[];
  readonly pngUrl: string;
}

/** Maps the MCDA config to the snake_case query params the raster API expects. */
function suitabilityParams(config: AnalysisConfig): Record<string, string> {
  return {
    slope_weight: String(config.slopeWeight),
    land_use_weight: String(config.landUseWeight),
    transport_weight: String(config.transportWeight),
    cost_weight: String(config.costWeight),
    slope_threshold: String(config.slopeThreshold),
    apply_exclusions: String(config.applyExclusions),
  };
}

/** Suitability bounds + ranked points for the map overlay (JSON). */
export async function getSuitabilityMeta(config: AnalysisConfig): Promise<SuitabilityMeta> {
  const response = await apiClient.get<SuitabilityMeta>(
    `/raster/suitability/${config.codigoIbge}`,
    { params: suitabilityParams(config) },
  );
  return response.data;
}

/** Fetches the colorized suitability PNG (authenticated) as an object URL. */
export async function getSuitabilityPngUrl(config: AnalysisConfig): Promise<string> {
  const response = await apiClient.get(`/raster/suitability/${config.codigoIbge}.png`, {
    params: suitabilityParams(config),
    responseType: 'blob',
  });
  return URL.createObjectURL(response.data as Blob);
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
