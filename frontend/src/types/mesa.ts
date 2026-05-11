/**
 * MESA assessment type definitions for GeoAvia.
 *
 * Based on the Manual de Apoio 2021 classificatory criteria.
 * All numeric fields are bounded to prevent logic bugs and payload overload.
 */

/** MESA site assessment data submitted through the evaluation form */
export interface MesaAssessment {
  readonly id?: number;
  readonly siteName: string;
  readonly averageSlope: number;
  readonly urbanCenterDistance: number;
  readonly hasObstacles: boolean;
  readonly obstacleDescription?: string;
  readonly estimatedCost: number;
  readonly latitude: number;
  readonly longitude: number;
  readonly createdAt?: string;
}

/** MESA ranking result returned by the backend */
export interface MesaRankingResult {
  readonly rank: number;
  readonly siteName: string;
  readonly totalScore: number;
  readonly slopeScore: number;
  readonly distanceScore: number;
  readonly obstacleScore: number;
  readonly costScore: number;
  readonly latitude: number;
  readonly longitude: number;
}
