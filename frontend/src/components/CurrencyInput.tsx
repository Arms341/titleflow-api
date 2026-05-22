// JARVIS App — Currency Input
// Formats value as $X,XXX.XX as the user types.
// Stores value as string (Decimal-safe, never float).
// Compatible with react-hook-form via forwardRef.
import React, { forwardRef, useCallback } from 'react';

interface CurrencyInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value'> {
  value?: string | number;
  onChange?: (value: string) => void;
  label?: string;
  error?: string;
  hint?: string;
}

function formatDisplay(raw: string): string {
  // Strip everything except digits and decimal point
  const clean = raw.replace(/[^0-9.]/g, '');
  const parts = clean.split('.');
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  if (parts.length > 1) {
    return intPart + '.' + parts[1].slice(0, 2);
  }
  return intPart;
}

function toDecimalString(display: string): string {
  return display.replace(/,/g, '');
}

const CurrencyInput = forwardRef<HTMLInputElement, CurrencyInputProps>(
  ({ value = '', onChange, label, error, hint, className = '', ...props }, ref) => {
    const displayValue = value !== '' ? '$' + formatDisplay(String(value)) : '';

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value.replace(/^\$/, '');
        const decimal = toDecimalString(raw);
        onChange?.(decimal);
      },
      [onChange]
    );

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <input
          {...props}
          ref={ref}
          type="text"
          inputMode="decimal"
          value={displayValue}
          onChange={handleChange}
          className={[
            'w-full px-3 py-2 border rounded-lg font-mono',
            'focus:outline-none focus:ring-2',
            error
              ? 'border-red-400 focus:ring-red-400'
              : 'border-gray-300 focus:ring-[var(--color-brand)]',
            className,
          ].join(' ')}
          placeholder="$0.00"
        />
        {hint && !error && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
    );
  }
);

CurrencyInput.displayName = 'CurrencyInput';
export default CurrencyInput;
