// JARVIS App — Loading Spinner
import { Loader2 } from 'lucide-react';

interface Props {
  fullPage?: boolean;
  size?: number;
  className?: string;
}

export default function LoadingSpinner({ fullPage = false, size = 24, className = '' }: Props) {
  if (fullPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 size={40} className="animate-spin text-[var(--color-brand)]" />
      </div>
    );
  }
  return (
    <Loader2
      size={size}
      className={`animate-spin text-[var(--color-brand)] ${className}`}
    />
  );
}
