/**
 * RecoveryCodeModal — presentational dialog that shows a single-use access code
 * (first access or password recovery) for the admin to relay. State lives in the
 * parent page.
 */
import { Button } from '@/components/ui';
import { sanitize } from '@/lib/security/sanitize';

interface RecoveryCodeModalProps {
  readonly username: string;
  readonly code: string | null;
  readonly expiresAt: string | null;
  readonly error: string | null;
  readonly isSubmitting: boolean;
  readonly copied: boolean;
  readonly onCopy: () => void;
  readonly onClose: () => void;
}

export function RecoveryCodeModal({
  username,
  code,
  expiresAt,
  error,
  isSubmitting,
  copied,
  onCopy,
  onClose,
}: RecoveryCodeModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/40 p-4 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-xl border border-neutral-200 bg-white p-6 shadow-xl animate-scale-in">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-neutral-900">
            Código de acesso — {sanitize(username)}
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

        {isSubmitting && <p className="text-sm text-neutral-500">Gerando código...</p>}

        {error && (
          <div role="alert" className="text-sm text-danger-600 animate-fade-in">
            {error}
          </div>
        )}

        {code && (
          <div className="space-y-4">
            <p className="text-sm text-neutral-600">
              Repasse este código de uso único ao usuário. Ele expira em ~30 minutos e permite
              definir a senha na tela de login (primeiro acesso ou recuperação).
            </p>
            <div className="flex items-center justify-between gap-3 rounded-lg border border-neutral-300 bg-neutral-50 px-4 py-3">
              <code className="select-all text-lg font-semibold tracking-widest text-neutral-900">
                {code}
              </code>
              <Button variant="ghost" size="sm" type="button" onClick={onCopy}>
                {copied ? 'Copiado!' : 'Copiar'}
              </Button>
            </div>
            {expiresAt && (
              <p className="text-xs text-neutral-400">
                Expira em: {new Date(expiresAt).toLocaleString('pt-BR')}
              </p>
            )}
          </div>
        )}

        <div className="flex justify-end pt-4">
          <Button variant="ghost" type="button" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </div>
    </div>
  );
}
