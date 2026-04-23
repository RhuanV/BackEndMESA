/**
 * Slider — Range input for MCDA weight configuration.
 *
 * Accessible with keyboard support and live value display.
 */
import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  readonly label: string;
  readonly value: number;
  readonly min?: number;
  readonly max?: number;
  readonly step?: number;
  readonly unit?: string;
  readonly error?: string;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  ({ label, value, min = 0, max = 100, step = 1, unit = '%', error, id, ...rest }, ref) => {
    const inputId = id ?? `slider-${label.toLowerCase().replace(/\s+/g, '-')}`;
    const percentage = ((value - min) / (max - min)) * 100;

    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label htmlFor={inputId} className="text-sm font-medium text-neutral-700">
            {label}
          </label>
          <span className="rounded-md bg-primary-600/10 px-2 py-0.5 text-xs font-semibold text-primary-700">
            {value}{unit}
          </span>
        </div>
        <input
          ref={ref}
          id={inputId}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          className="w-full h-2 rounded-full appearance-none cursor-pointer bg-neutral-200
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-600
            [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:hover:scale-110
            [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4
            [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary-600
            [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:shadow-md"
          style={{
            background: `linear-gradient(to right, var(--color-primary-600) 0%, var(--color-primary-600) ${percentage}%, var(--color-neutral-200) ${percentage}%, var(--color-neutral-200) 100%)`,
          }}
          aria-valuenow={value}
          aria-valuemin={min}
          aria-valuemax={max}
          {...rest}
        />
        {error && (
          <p role="alert" className="text-xs text-danger-600 animate-fade-in">{error}</p>
        )}
      </div>
    );
  }
);

Slider.displayName = 'Slider';
