/**
 * Ranking API service for GeoAvia.
 *
 * Sprint 2: fetches the scored ranking of stored MESA assessments from the
 * backend. The scoring is currently a deterministic mock on the server
 * (mesa_service._score) — the real MCDA/AHP arrives with EP-13.
 */
import apiClient from '@/lib/api/axiosInstance';
import type { MesaRankingResult } from '@/types';

export async function getRanking(): Promise<MesaRankingResult[]> {
  const response = await apiClient.get<MesaRankingResult[]>('/ranking');
  return response.data;
}
