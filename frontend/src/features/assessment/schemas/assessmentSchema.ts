/**
 * MESA assessment validation schema (Zod) — first-barrier client validation;
 * the backend validates independently.
 */
import { z } from 'zod';
import { SITE_NAME_MAX_LENGTH, DESCRIPTION_MAX_LENGTH } from '@/lib/constants';

// Blocks angle brackets/script/event-handler chars (XSS vectors); allows
// letters (accented), numbers, spaces and common punctuation.
const SAFE_TEXT_REGEX = /^[\w\sÀ-ÿ.,;:!?()/-]*$/u;

export const assessmentSchema = z.object({
  siteName: z
    .string()
    .min(3, 'Nome do sítio deve ter pelo menos 3 caracteres')
    .max(SITE_NAME_MAX_LENGTH, `Nome do sítio deve ter no máximo ${SITE_NAME_MAX_LENGTH} caracteres`)
    .regex(SAFE_TEXT_REGEX, 'Nome contém caracteres não permitidos'),

  averageSlope: z
    .number({ error: 'Declividade deve ser um número' })
    .min(0, 'Declividade não pode ser negativa')
    .max(100, 'Declividade máxima é 100%'),

  urbanCenterDistance: z
    .number({ error: 'Distância deve ser um número' })
    .min(0, 'Distância não pode ser negativa')
    .max(10000, 'Distância máxima é 10.000 km'),

  hasObstacles: z.boolean(),

  obstacleDescription: z
    .string()
    .max(DESCRIPTION_MAX_LENGTH, `Descrição deve ter no máximo ${DESCRIPTION_MAX_LENGTH} caracteres`)
    .regex(SAFE_TEXT_REGEX, 'Descrição contém caracteres não permitidos')
    .optional()
    .or(z.literal('')),

  estimatedCost: z
    .number({ error: 'Custo deve ser um número' })
    .min(0, 'Custo não pode ser negativo')
    .max(999_999_999_999, 'Valor excede o limite permitido'),

  latitude: z
    .number({ error: 'Latitude deve ser um número' })
    .min(-90, 'Latitude mínima é -90°')
    .max(90, 'Latitude máxima é 90°'),

  longitude: z
    .number({ error: 'Longitude deve ser um número' })
    .min(-180, 'Longitude mínima é -180°')
    .max(180, 'Longitude máxima é 180°'),

  widthM: z
    .number({ error: 'Largura deve ser um número' })
    .min(1, 'Largura mínima é 1 m')
    .max(10000, 'Largura máxima é 10.000 m'),

  heightM: z
    .number({ error: 'Comprimento deve ser um número' })
    .min(1, 'Comprimento mínimo é 1 m')
    .max(50000, 'Comprimento máximo é 50.000 m'),

  angleDeg: z
    .number({ error: 'Ângulo deve ser um número' })
    .min(0, 'Ângulo mínimo é 0°')
    .max(359.9, 'Ângulo máximo é 359,9°'),
});

export type AssessmentFormData = z.infer<typeof assessmentSchema>;
