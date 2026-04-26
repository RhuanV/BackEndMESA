/**
 * Assessment API service for GeoAvia.
 *
 * Handles API communication for MESA site assessments.
 * All data is validated by Zod before reaching this service.
 */
import apiClient from '@/lib/api/axiosInstance';
import type { MesaAssessment } from '@/types/mesa';
import type { AssessmentFormData } from '@/features/assessment/schemas/assessmentSchema';

/**
 * Submits a new MESA site assessment to the backend.
 */
export async function submitAssessment(data: AssessmentFormData): Promise<MesaAssessment> {
  const response = await apiClient.post<MesaAssessment>('/assessments', data);
  return response.data;
}

/**
 * Retrieves all MESA site assessments.
 */
export async function getAssessments(): Promise<MesaAssessment[]> {
  const response = await apiClient.get<MesaAssessment[]>('/assessments');
  return response.data;
}
