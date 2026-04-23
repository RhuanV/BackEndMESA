/**
 * Select — Dropdown select for region picker and category filters.
 */
import { forwardRef } from 'react';
import type { SelectHTMLAttributes } from 'react';

interface SelectOption {
  readonly value: string;
  readonly label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  readonly label: string;
  readonly options: readonly SelectOption[];
  readonly placeholder?: string;
  readonly error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, placeholder = 'Selecione...', error, id, className = '', ...rest }, ref) => {
    const selectId = id ?? `select-${label.toLowerCase().replace(/\s+/g, '-')}`;
    const errorId = `${selectId}-error`;

    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={selectId} className="text-sm font-medium text-neutral-700">
          {label}
        </label>
        <select
          ref={ref}
          id={selectId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          className={`
            w-full rounded-lg border px-3 py-2.5 text-sm text-neutral-900
            bg-white appearance-none cursor-pointer
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-1
            ${error
              ? 'border-danger-500 focus:ring-danger-500'
              : 'border-neutral-300 focus:border-accent-500 focus:ring-accent-500'
            }
            disabled:cursor-not-allowed disabled:bg-neutral-100
            ${className}
          `}
          {...rest}
        >
          <option value="">{placeholder}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {error && (
          <p id={errorId} role="alert" className="text-xs text-danger-600 animate-fade-in">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
