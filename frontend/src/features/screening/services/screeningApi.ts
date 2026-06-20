/**
 * Screening API client (Sprint 4 HU-29 + Sprint 5 HU-26).
 *
 * Wraps POST /screening — classifies a point as viavel / intermediario / restrito
 * given the target municipality (IBGE 7-digit code).
 */
import apiClient from '@/lib/api/axiosInstance';

export type ScreeningStatus = 'viavel' | 'intermediario' | 'restrito';

export interface IntermediateReason {
  readonly layer: string;
  readonly buffer_meters: number;
}

export interface ScreeningResult {
  readonly status: ScreeningStatus;
  readonly code: 0 | 1 | 2;
  readonly reasons: readonly string[];
  readonly intermediate_reasons: readonly IntermediateReason[];
  readonly validation: {
    readonly srid: number;
    readonly target_municipality_ibge_code: string;
    readonly layers_checked: readonly string[];
    readonly buffers_applied_m: Readonly<Record<string, number>>;
  };
}

export interface ScreeningRequest {
  readonly latitude: number;
  readonly longitude: number;
  readonly target_municipality_ibge_code: string;
}

export async function runScreening(payload: ScreeningRequest): Promise<ScreeningResult> {
  const response = await apiClient.post<ScreeningResult>('/screening', payload);
  return response.data;
}
