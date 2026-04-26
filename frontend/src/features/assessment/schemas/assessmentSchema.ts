/**
 * MESA Assessment validation schema (Zod).
 *
 * Defense in Depth: Client-side validation as the first barrier.
 * The backend MUST validate all inputs independently.
 *
 * Security measures per field:
 * - Strict type enforcement (number vs string)
 * - Min/max bounds to prevent negative values and payload overload
 * - Regex patterns on strings to block XSS payloads
 * - Character length limits to prevent buffer/payload overflow
 *
 * Based on Manual de Apoio 2021 classificatory criteria:
 * - Declividade Média (Average Slope)
 * - Distância de Centros Urbanos (Urban Center Distance)
 * - Presença de Obstáculos (Obstacle Presence)
 * - Custo Estimado (Estimated Cost)
 */
import { z } from 'zod';
import { SITE_NAME_MAX_LENGTH, DESCRIPTION_MAX_LENGTH } from '@/lib/constants';

/**
 * Regex for safe text input.
 * Allows: letters (including accented), numbers, spaces, and common punctuation.
 * Blocks: angle brackets, script tags, event handlers, and other XSS vectors.
 */
const SAFE_TEXT_REGEX = /^[\w\sÀ-ÿ.,;:!?()/-]*$/u;

export const assessmentSchema = z.object({
  /** Nome do sítio aeroportuário */
  siteName: z
    .string()
    .min(3, 'Nome do sítio deve ter pelo menos 3 caracteres')
    .max(SITE_NAME_MAX_LENGTH, `Nome do sítio deve ter no máximo ${SITE_NAME_MAX_LENGTH} caracteres`)
    .regex(SAFE_TEXT_REGEX, 'Nome contém caracteres não permitidos'),

  /** Declividade Média (%) — classificatory criterion */
  averageSlope: z
    .number({ error: 'Declividade deve ser um número' })
    .min(0, 'Declividade não pode ser negativa')
    .max(100, 'Declividade máxima é 100%'),

  /** Distância de Centros Urbanos (km) — classificatory criterion */
  urbanCenterDistance: z
    .number({ error: 'Distância deve ser um número' })
    .min(0, 'Distância não pode ser negativa')
    .max(10000, 'Distância máxima é 10.000 km'),

  /** Presença de Obstáculos — classificatory criterion */
  hasObstacles: z.boolean(),

  /** Descrição dos obstáculos (optional, only if hasObstacles is true) */
  obstacleDescription: z
    .string()
    .max(DESCRIPTION_MAX_LENGTH, `Descrição deve ter no máximo ${DESCRIPTION_MAX_LENGTH} caracteres`)
    .regex(SAFE_TEXT_REGEX, 'Descrição contém caracteres não permitidos')
    .optional()
    .or(z.literal('')),

  /** Custo Estimado (R$) — classificatory criterion */
  estimatedCost: z
    .number({ error: 'Custo deve ser um número' })
    .min(0, 'Custo não pode ser negativo')
    .max(999_999_999_999, 'Valor excede o limite permitido'),

  /** Latitude — geographic coordinate */
  latitude: z
    .number({ error: 'Latitude deve ser um número' })
    .min(-90, 'Latitude mínima é -90°')
    .max(90, 'Latitude máxima é 90°'),

  /** Longitude — geographic coordinate */
  longitude: z
    .number({ error: 'Longitude deve ser um número' })
    .min(-180, 'Longitude mínima é -180°')
    .max(180, 'Longitude máxima é 180°'),
});

export type AssessmentFormData = z.infer<typeof assessmentSchema>;
