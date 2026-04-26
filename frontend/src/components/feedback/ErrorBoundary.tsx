/**
 * React Error Boundary for GeoAvia.
 *
 * Security: Catches rendering errors and displays a generic message.
 * Technical stack traces are NEVER exposed in the DOM — only logged
 * to console in development mode.
 */
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  readonly children: ReactNode;
  readonly fallback?: ReactNode;
}

interface ErrorBoundaryState {
  readonly hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Security: Only log in development. Never expose in the DOM.
    if (import.meta.env.DEV) {
      console.error('[ErrorBoundary] Rendering error caught:', error);
      console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack);
    }
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          className="flex min-h-screen items-center justify-center bg-neutral-50 p-8"
        >
          <div className="max-w-md animate-fade-in text-center">
            <div className="mb-4 text-5xl" aria-hidden="true">⚠️</div>
            <h1 className="mb-2 text-xl font-semibold text-neutral-800">
              Algo deu errado
            </h1>
            <p className="mb-6 text-neutral-500">
              Ocorreu um erro inesperado. Tente recarregar a página.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:ring-2 focus-visible:ring-accent-500"
              type="button"
            >
              Recarregar Página
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
