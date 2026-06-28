import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: number | string;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
    positive?: boolean;
  };
  className?: string;
}

export function KPICard({ title, value, description, icon: Icon, trend, className }: KPICardProps) {
  return (
    <div
      className={cn(
        'bg-card rounded-lg border border-border p-6 shadow-sm transition-all hover:shadow-md',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1.5">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold text-foreground">{value}</p>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
          {trend && (
            <p
              className={cn(
                'text-xs font-medium',
                trend.positive ? 'text-emerald-600' : 'text-red-600'
              )}
            >
              {trend.positive ? '+' : ''}
              {trend.value}% {trend.label}
            </p>
          )}
        </div>
        {Icon && (
          <div className="rounded-lg bg-primary/10 p-3">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        )}
      </div>
    </div>
  );
}

export default KPICard;
