/**
 * Password-recovery form validation schema (Zod).
 *
 * Mirrors the backend contract for POST /password-reset: username + admin-issued
 * recovery code + new password (min 8). Client-side validation is Defense in
 * Depth; the backend validates independently.
 */
import { z } from 'zod';
import { USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH, RECOVERY_CODE_LENGTH } from '@/lib/constants';
import { strongPasswordSchema } from '@/lib/validation/password';

export const resetPasswordSchema = z.object({
  username: z
    .string()
    .min(USERNAME_MIN_LENGTH, `Mínimo de ${USERNAME_MIN_LENGTH} caracteres`)
    .max(USERNAME_MAX_LENGTH, `Máximo de ${USERNAME_MAX_LENGTH} caracteres`)
    .regex(
      /^[a-zA-Z0-9._-]+$/,
      'Apenas letras, números, pontos, hífens e underscores são permitidos'
    ),
  code: z
    .string()
    .length(RECOVERY_CODE_LENGTH, 'Código de recuperação inválido'),
  newPassword: strongPasswordSchema,
});

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
