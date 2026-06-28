import { cn } from '@/lib/utils';

interface LoadingProps {
  text?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Loading({ text = 'Loading...', className, size = 'md' }: LoadingProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className={cn('flex flex-col items-center justify-center py-12', className)}>
      <div
        className={cn(
          'animate-spin rounded-full border-4 border-primary border-t-transparent',
          sizeClasses[size]
        )}
      />
      {text && <p className="mt-4 text-sm text-muted-foreground">{text}</p>}
    </div>
  );
}

export default Loading;
