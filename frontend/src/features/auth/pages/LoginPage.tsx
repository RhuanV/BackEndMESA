/**
 * LoginPage — Full-page login screen for GeoAvia.
 *
 * Professional governmental design with GeoAvia branding.
 * Redirects to dashboard if already authenticated.
 */
import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { PasswordResetForm } from '@/features/auth/components/PasswordResetForm';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { LoadingSpinner } from '@/components/ui';
import { APP_NAME, APP_DESCRIPTION } from '@/lib/constants';

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [showReset, setShowReset] = useState(false);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <LoadingSpinner size="lg" label="Verificando sessão..." />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard/map" replace />;
  }

  return (
    <main className="flex min-h-screen">
      {/* Left panel — Branding */}
      <div className="hidden lg:flex lg:w-1/2 lg:flex-col lg:items-center lg:justify-center bg-gradient-to-br from-primary-700 via-primary-600 to-primary-800 p-12 text-white">
        <div className="max-w-md text-center animate-fade-in">
          {/* Logo / Icon */}
          <div className="mb-8 flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="h-10 w-10 text-accent-300"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"
                />
              </svg>
            </div>
          </div>
          <h1 className="mb-3 text-3xl font-bold tracking-tight">
            {APP_NAME}
          </h1>
          <p className="text-lg text-primary-200 leading-relaxed">
            {APP_DESCRIPTION}
          </p>
          <div className="mt-8 flex justify-center gap-2">
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-primary-200 border border-white/10">
              SAC
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-primary-200 border border-white/10">
              ANAC
            </span>
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-primary-200 border border-white/10">
              ITA
            </span>
          </div>
        </div>
      </div>

      {/* Right panel — Login Form */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-1/2 bg-neutral-50">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Mobile-only logo */}
          <div className="mb-8 text-center lg:hidden">
            <div className="mb-4 flex justify-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary-600">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="h-7 w-7 text-white"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"
                  />
                </svg>
              </div>
            </div>
            <h1 className="text-xl font-bold text-neutral-900">{APP_NAME}</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-neutral-900">
              {showReset ? 'Recuperar Senha' : 'Acesso ao Sistema'}
            </h2>
            <p className="mt-2 text-sm text-neutral-500">
              {showReset
                ? 'Redefina sua senha com o código fornecido por um administrador.'
                : 'Entre com suas credenciais para acessar o painel.'}
            </p>
          </div>

          {showReset ? (
            <PasswordResetForm onBackToLogin={() => setShowReset(false)} />
          ) : (
            <LoginForm onForgotPassword={() => setShowReset(true)} />
          )}

          <p className="mt-8 text-center text-xs text-neutral-400">
            Sistema restrito a usuários autorizados.
            <br />
            Acesso monitorado por segurança.
          </p>
        </div>
      </div>
    </main>
  );
}
