/**
 * PasswordResetForm — reset a password with an admin-issued recovery code.
 *
 * The user provides their username, the recovery code relayed by an
 * administrator, and a new password. On success they are invited to return to
 * the login screen. Error messages are kept generic.
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { resetPasswordSchema } from '@/features/auth/schemas/resetPasswordSchema';
import type { ResetPasswordFormData } from '@/features/auth/schemas/resetPasswordSchema';
import { resetPasswordByCode } from '@/features/auth/services/authService';
import { extractErrorDetail } from '@/lib/api/errors';
import { RECOVERY_CODE_LENGTH, PASSWORD_MAX_LENGTH } from '@/lib/constants';
import { Button, Input } from '@/components/ui';

interface PasswordResetFormProps {
  readonly onBackToLogin: () => void;
}

export function PasswordResetForm({ onBackToLogin }: PasswordResetFormProps) {
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    mode: 'onBlur',
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setServerError(null);
    try {
      await resetPasswordByCode(data.username, data.code.trim(), data.newPassword);
      setSuccess(true);
    } catch (err) {
      setServerError(
        extractErrorDetail(err) ??
          'Não foi possível redefinir a senha. Verifique os dados e tente novamente.'
      );
    }
  };

  if (success) {
    return (
      <div className="w-full max-w-sm space-y-5 text-center">
        <div
          role="status"
          className="animate-fade-in rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700"
        >
          Senha redefinida com sucesso. Você já pode entrar com a nova senha.
        </div>
        <Button type="button" className="w-full" size="lg" onClick={onBackToLogin}>
          Voltar ao login
        </Button>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="w-full max-w-sm space-y-5"
      noValidate
      aria-label="Formulário de recuperação de senha"
    >
      <p className="text-sm text-neutral-500">
        No primeiro acesso ou ao esquecer a senha, use o código fornecido pelo
        administrador para definir sua senha abaixo.
      </p>

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
        disabled={isSubmitting}
        {...register('username')}
      />

      <Input
        label="Código de recuperação"
        placeholder="Código enviado pelo administrador"
        autoComplete="one-time-code"
        maxLength={RECOVERY_CODE_LENGTH}
        error={errors.code?.message}
        disabled={isSubmitting}
        {...register('code')}
      />

      <Input
        label="Nova senha"
        type="password"
        placeholder="Mín. 8 caracteres, com maiúscula, minúscula, número e especial"
        autoComplete="new-password"
        maxLength={PASSWORD_MAX_LENGTH}
        error={errors.newPassword?.message}
        disabled={isSubmitting}
        {...register('newPassword')}
      />

      <Button type="submit" isLoading={isSubmitting} disabled={isSubmitting} className="w-full" size="lg">
        Redefinir senha
      </Button>

      <button
        type="button"
        onClick={onBackToLogin}
        className="w-full text-center text-sm text-primary-600 hover:underline"
      >
        Voltar ao login
      </button>
    </form>
  );
}
