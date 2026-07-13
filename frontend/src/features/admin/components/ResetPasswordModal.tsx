/**
 * ResetPasswordModal — presentational dialog for the developer-only direct
 * password reset. All state and the submit logic live in the parent page.
 */
import type { FormEvent } from 'react';
import { Button } from '@/components/ui';
import { sanitize } from '@/lib/security/sanitize';
import { PASSWORD_MAX_LENGTH } from '@/lib/constants';

interface ResetPasswordModalProps {
  readonly username: string;
  readonly newPassword: string;
  readonly onNewPasswordChange: (value: string) => void;
  readonly error: string | null;
  readonly success: string | null;
  readonly isSubmitting: boolean;
  readonly onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  readonly onClose: () => void;
}

export function ResetPasswordModal({
  username,
  newPassword,
  onNewPasswordChange,
  error,
  success,
  isSubmitting,
  onSubmit,
  onClose,
}: ResetPasswordModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/40 p-4 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-xl border border-neutral-200 bg-surface p-6 shadow-xl animate-scale-in">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-neutral-900">
            Alterar Senha de {sanitize(username)}
          </h3>
          <button
            type="button"
            className="text-neutral-400 hover:text-neutral-600 transition-colors"
            onClick={onClose}
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-neutral-700 block mb-1.5">Senha Atual</label>
            <input
              type="password"
              value="••••••••"
              disabled
              className="w-full rounded-lg border border-neutral-300 bg-neutral-100 px-4 py-2 text-sm text-neutral-400 cursor-not-allowed select-none"
              aria-label="Senha atual oculta"
            />
            <span className="text-xs text-neutral-400 mt-1 block">
              A senha atual é protegida e não pode ser revelada.
            </span>
          </div>

          <div>
            <label
              htmlFor="new-reset-password"
              className="text-sm font-medium text-neutral-700 block mb-1.5"
            >
              Nova Senha
            </label>
            <input
              id="new-reset-password"
              type="password"
              value={newPassword}
              onChange={(e) => onNewPasswordChange(e.target.value)}
              required
              maxLength={PASSWORD_MAX_LENGTH}
              autoComplete="new-password"
              placeholder="Mín. 8: maiúscula, minúscula, número e especial"
              className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm text-neutral-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-neutral-100 disabled:text-neutral-400"
              disabled={isSubmitting || success !== null}
            />
          </div>

          {error && (
            <div role="alert" className="text-sm text-danger-600 animate-fade-in">
              {error}
            </div>
          )}

          {success && <div className="text-sm text-emerald-600 animate-fade-in">{success}</div>}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" type="button" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isSubmitting} disabled={success !== null}>
              Confirmar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
