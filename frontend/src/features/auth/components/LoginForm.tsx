/**
 * LoginForm — Secure login form component.
 *
 * Security features:
 * - React Hook Form + Zod validation (Defense in Depth)
 * - Generic error messages to prevent user enumeration
 * - Rate-limit visual feedback with progressive backoff
 * - Loading state prevents double submission
 * - No autocomplete on password for shared computers
 * - No sensitive data in DOM or console
 */
import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema } from '@/features/auth/schemas/loginSchema';
import type { LoginFormData } from '@/features/auth/schemas/loginSchema';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { Button, Input } from '@/components/ui';
import { LOGIN_COOLDOWN_BASE_MS, LOGIN_MAX_ATTEMPTS } from '@/lib/constants';

interface LoginFormProps {
  readonly onForgotPassword?: () => void;
}

export function LoginForm({ onForgotPassword }: LoginFormProps = {}) {
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [cooldownActive, setCooldownActive] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  });

  const startCooldown = useCallback(
    (attempts: number) => {
      // Progressive backoff: 3s, 6s, 9s, 12s, 15s...
      const cooldownMs = LOGIN_COOLDOWN_BASE_MS * Math.min(attempts, LOGIN_MAX_ATTEMPTS);
      setCooldownActive(true);
      setTimeout(() => setCooldownActive(false), cooldownMs);
    },
    []
  );

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);

    try {
      await login(data.username, data.password);
      // Successful login — navigation is handled by the router
      setFailedAttempts(0);
    } catch {
      // Security: ALWAYS show generic error message
      // Never reveal if the username exists or if the password was wrong
      const newAttempts = failedAttempts + 1;
      setFailedAttempts(newAttempts);
      setServerError('Credenciais inválidas. Tente novamente.');
      startCooldown(newAttempts);
    }
  };

  const isDisabled = isSubmitting || cooldownActive;

  return (
    <form
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="w-full max-w-sm space-y-5"
      noValidate
      aria-label="Formulário de login"
    >
      {/* Server error banner — generic message only */}
      {serverError && (
        <div
          role="alert"
          className="animate-fade-in rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {serverError}
        </div>
      )}

      <Input
        label="Usuário"
        placeholder="Digite seu usuário"
        autoComplete="username"
        maxLength={50}
        error={errors.username?.message}
        disabled={isDisabled}
        {...register('username')}
      />

      <Input
        label="Senha"
        type="password"
        placeholder="Digite sua senha"
        autoComplete="new-password"
        maxLength={128}
        error={errors.password?.message}
        disabled={isDisabled}
        {...register('password')}
      />

      <Button
        type="submit"
        isLoading={isSubmitting}
        disabled={isDisabled}
        className="w-full"
        size="lg"
      >
        {cooldownActive ? 'Aguarde...' : 'Entrar'}
      </Button>

      {failedAttempts >= LOGIN_MAX_ATTEMPTS && (
        <p className="animate-fade-in text-center text-xs text-neutral-500">
          Muitas tentativas. Aguarde antes de tentar novamente.
        </p>
      )}

      {onForgotPassword && (
        <button
          type="button"
          onClick={onForgotPassword}
          disabled={isDisabled}
          className="w-full text-center text-sm text-primary-600 hover:underline disabled:opacity-50"
        >
          Esqueceu sua senha?
        </button>
      )}
    </form>
  );
}
