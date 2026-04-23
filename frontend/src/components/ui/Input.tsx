/**
 * Input — Shared form input component.
 *
 * Designed for use with React Hook Form. Displays validation errors
 * with accessible ARIA attributes. Never exposes technical error details.
 */
import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  readonly label: string;
  readonly error?: string;
  readonly helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, className = '', ...rest }, ref) => {
    const inputId = id ?? `input-${label.toLowerCase().replace(/\s+/g, '-')}`;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    return (
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-neutral-700"
        >
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className={`
            w-full rounded-lg border px-4 py-2.5
            text-sm text-neutral-900
            placeholder:text-neutral-400
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-1
            ${
              error
                ? 'border-danger-500 focus:ring-danger-500'
                : 'border-neutral-300 focus:border-accent-500 focus:ring-accent-500'
            }
            disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400
            ${className}
          `}
          {...rest}
        />
        {error && (
          <p id={errorId} role="alert" className="text-xs text-danger-600 animate-fade-in">
            {error}
          </p>
        )}
        {!error && helperText && (
          <p id={helperId} className="text-xs text-neutral-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
