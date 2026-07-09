/**
 * Password-recovery form validation schema (Zod).
 *
 * Mirrors the backend contract for POST /password-reset: username + admin-issued
 * recovery code + new password (min 8). Client-side validation is Defense in
 * Depth; the backend validates independently.
 */
import { z } from 'zod';
import { USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH } from '@/lib/constants';

const RESET_PASSWORD_MIN_LENGTH = 8;

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
    .min(6, 'Informe o código de recuperação')
    .max(32, 'Código inválido'),
  newPassword: z
    .string()
    .min(RESET_PASSWORD_MIN_LENGTH, `Mínimo de ${RESET_PASSWORD_MIN_LENGTH} caracteres`)
    .max(PASSWORD_MAX_LENGTH, `Máximo de ${PASSWORD_MAX_LENGTH} caracteres`),
});

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
