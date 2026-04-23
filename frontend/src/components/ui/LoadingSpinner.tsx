/**
 * LoadingSpinner — Shared loading indicator component.
 *
 * Used across the application for async operations (login, data fetching, etc.).
 * Accessible with proper ARIA attributes.
 */

interface LoadingSpinnerProps {
  readonly size?: 'sm' | 'md' | 'lg';
  readonly label?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
} as const;

export function LoadingSpinner({ size = 'md', label = 'Carregando...' }: LoadingSpinnerProps) {
  return (
    <div className="flex items-center justify-center gap-3" role="status" aria-label={label}>
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-accent-500 border-t-transparent`}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}
