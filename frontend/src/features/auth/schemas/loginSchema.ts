/**
 * Login form validation schema (Zod).
 *
 * Defense in Depth: Client-side validation as an additional security layer.
 * The backend MUST also validate all inputs independently.
 *
 * Security measures:
 * - Username: strict alphanumeric + limited special chars, bounded length
 * - Password: bounded length to prevent payload overload
 * - Regex prevents XSS payloads in form fields
 */
import { z } from 'zod';
import {
  USERNAME_MIN_LENGTH,
  USERNAME_MAX_LENGTH,
  PASSWORD_MAX_LENGTH,
} from '@/lib/constants';

export const loginSchema = z.object({
  username: z
    .string()
    .min(USERNAME_MIN_LENGTH, `Mínimo de ${USERNAME_MIN_LENGTH} caracteres`)
    .max(USERNAME_MAX_LENGTH, `Máximo de ${USERNAME_MAX_LENGTH} caracteres`)
    .regex(
      /^[a-zA-Z0-9._-]+$/,
      'Apenas letras, números, pontos, hífens e underscores são permitidos'
    ),
  // Login is not revalidated against the new-password policy — only bounded, so
  // pre-existing accounts (any length) can still sign in.
  password: z
    .string()
    .min(1, 'Informe a senha')
    .max(PASSWORD_MAX_LENGTH, `Máximo de ${PASSWORD_MAX_LENGTH} caracteres`),
});

export type LoginFormData = z.infer<typeof loginSchema>;
