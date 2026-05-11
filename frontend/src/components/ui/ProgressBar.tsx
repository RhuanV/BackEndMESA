/**
 * ProgressBar — Determinate and indeterminate progress indicator.
 *
 * For long-running operations up to 30s (RNF02 compliance).
 */

interface ProgressBarProps {
  readonly value?: number;       // 0-100 for determinate, undefined for indeterminate
  readonly label?: string;
  readonly showPercentage?: boolean;
}

export function ProgressBar({ value, label, showPercentage = true }: ProgressBarProps) {
  const isDeterminate = value !== undefined;

  return (
    <div className="w-full space-y-1.5" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      {(label || (isDeterminate && showPercentage)) && (
        <div className="flex items-center justify-between text-xs">
          {label && <span className="font-medium text-neutral-600">{label}</span>}
          {isDeterminate && showPercentage && (
            <span className="font-semibold text-primary-700">{Math.round(value)}%</span>
          )}
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
        {isDeterminate ? (
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary-600 to-accent-500 transition-all duration-500 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          />
        ) : (
          <div className="h-full w-1/3 animate-[slide-progress_1.5s_ease-in-out_infinite] rounded-full bg-gradient-to-r from-primary-600 to-accent-500" />
        )}
      </div>
    </div>
  );
}
