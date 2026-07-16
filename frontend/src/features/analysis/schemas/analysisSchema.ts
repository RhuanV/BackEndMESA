/**
 * MCDA Analysis configuration schema (Zod).
 *
 * Defense in Depth: Validates all weight inputs and constraints on the client side.
 * Key constraint: ALL weights must sum to exactly 100%.
 *
 * Security:
 * - Bounded numeric ranges (0-100 for weights, domain-specific for thresholds)
 * - Custom refine() ensuring weight sum = 100
 * - No string fields (prevents XSS in config)
 */
import { z } from 'zod';

export const analysisConfigSchema = z
  .object({
    /** Target município (7-digit IBGE code) the MCDA is computed for */
    codigoIbge: z.string().regex(/^\d{7}$/, 'Selecione um município'),

    /** Weight for slope criterion (ANADEM) */
    slopeWeight: z
      .number({ error: 'Peso deve ser um número' })
      .min(0, 'Peso mínimo é 0%')
      .max(100, 'Peso máximo é 100%'),

    /** Slope threshold percentage — filter areas above this */
    slopeThreshold: z
      .number({ error: 'Limiar deve ser um número' })
      .min(0, 'Limiar mínimo é 0%')
      .max(45, 'Limiar máximo é 45%'),

    /** Weight for land use criterion (MapBiomas) */
    landUseWeight: z
      .number({ error: 'Peso deve ser um número' })
      .min(0, 'Peso mínimo é 0%')
      .max(100, 'Peso máximo é 100%'),

    /** Weight for road/rail distance criterion (DNIT) */
    transportWeight: z
      .number({ error: 'Peso deve ser um número' })
      .min(0, 'Peso mínimo é 0%')
      .max(100, 'Peso máximo é 100%'),

    /** Buffer distance in km for roads/railways */
    transportBufferKm: z
      .number({ error: 'Buffer deve ser um número' })
      .min(0, 'Buffer mínimo é 0 km')
      .max(500, 'Buffer máximo é 500 km'),

    /** Weight for cost criterion */
    costWeight: z
      .number({ error: 'Peso deve ser um número' })
      .min(0, 'Peso mínimo é 0%')
      .max(100, 'Peso máximo é 100%'),

    /** Whether to apply exclusion zones (Terras Indígenas + UCs) */
    applyExclusions: z.boolean(),
  })
  .refine(
    (data) => {
      const sum = data.slopeWeight + data.landUseWeight + data.transportWeight + data.costWeight;
      return Math.abs(sum - 100) < 0.01; // Float tolerance
    },
    {
      message: 'A soma dos pesos deve ser exatamente 100%',
      path: ['slopeWeight'], // Show error on the first weight field
    }
  );

export type AnalysisConfig = z.infer<typeof analysisConfigSchema>;

/** Default MCDA configuration (codigoIbge is chosen by the user before running) */
export const DEFAULT_ANALYSIS_CONFIG: AnalysisConfig = {
  codigoIbge: '',
  slopeWeight: 30,
  slopeThreshold: 2,
  landUseWeight: 25,
  transportWeight: 25,
  transportBufferKm: 50,
  costWeight: 20,
  applyExclusions: true,
};
