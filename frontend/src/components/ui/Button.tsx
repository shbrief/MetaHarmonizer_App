import { Loader2 } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/cn';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}

const VARIANT: Record<Variant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
  danger: 'btn-danger',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className,
  children,
  disabled,
  ...rest
}: Props) {
  // Size the spinner to match the icon box so the icon↔spinner swap doesn't
  // change the button's width (which would otherwise make the row "jump").
  const spinner = (
    <Loader2 className={cn('animate-spin', size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
  );
  return (
    <button
      className={cn(VARIANT[variant], size === 'sm' && 'btn-sm', className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? spinner : icon}
      {children}
    </button>
  );
}
