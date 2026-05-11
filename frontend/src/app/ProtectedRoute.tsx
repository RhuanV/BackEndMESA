/**
 * ProtectedRoute — Route guard with non-overlapping RBAC.
 *
 * Security:
 * - Validates authentication state before rendering
 * - Supports allowedRoles ARRAY (roles are silos, not hierarchy)
 * - Loading state prevents flash of login page
 * - Generic "access denied" on role mismatch
 */
import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { UserRole } from '@/types/auth';

interface ProtectedRouteProps {
  readonly children: ReactNode;
  readonly allowedRoles?: UserRole[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <LoadingSpinner size="lg" label="Validando sessão..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Role-based access: check if user's role is in the allowedRoles array
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-8">
        <div className="max-w-md text-center animate-fade-in">
          <div className="mb-4 text-5xl" aria-hidden="true">🔒</div>
          <h1 className="mb-2 text-xl font-semibold text-neutral-800">
            Acesso Restrito
          </h1>
          <p className="mb-6 text-neutral-500">
            Você não possui permissão para acessar esta página.
          </p>
          <Navigate to="/dashboard/map" replace />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
