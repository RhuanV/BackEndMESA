/**
 * Password-strength policy — the single source of truth on the frontend.
 *
 * Mirrors the backend policy in core/passwords.py. Client-side validation is
 * UX/Defense-in-Depth only; the backend validates every new password independently.
 *
 * Policy: at least PASSWORD_MIN_LENGTH characters, with at least one uppercase
 * letter, one lowercase letter, one digit and one special character.
 */
import { z } from 'zod';
import { PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH } from '@/lib/constants';

export const PASSWORD_POLICY = {
  minLength: PASSWORD_MIN_LENGTH,
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digit: /\d/,
  special: /[^A-Za-z0-9]/,
} as const;

/** Returns a list of human-readable policy violations (empty means valid). */
export function getPasswordStrengthErrors(password: string): string[] {
  const errors: string[] = [];
  if (password.length < PASSWORD_POLICY.minLength) {
    errors.push(`Mínimo de ${PASSWORD_POLICY.minLength} caracteres`);
  }
  if (!PASSWORD_POLICY.uppercase.test(password)) {
    errors.push('Pelo menos uma letra maiúscula');
  }
  if (!PASSWORD_POLICY.lowercase.test(password)) {
    errors.push('Pelo menos uma letra minúscula');
  }
  if (!PASSWORD_POLICY.digit.test(password)) {
    errors.push('Pelo menos um número');
  }
  if (!PASSWORD_POLICY.special.test(password)) {
    errors.push('Pelo menos um caractere especial');
  }
  return errors;
}

export function isPasswordStrong(password: string): boolean {
  return getPasswordStrengthErrors(password).length === 0;
}

/** Reusable Zod schema for a strong new password. */
export const strongPasswordSchema = z
  .string()
  .max(PASSWORD_MAX_LENGTH, `Máximo de ${PASSWORD_MAX_LENGTH} caracteres`)
  .superRefine((value, ctx) => {
    for (const message of getPasswordStrengthErrors(value)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message });
    }
  });
