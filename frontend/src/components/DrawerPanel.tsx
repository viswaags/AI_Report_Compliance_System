import { X } from 'lucide-react';
import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface DrawerPanelProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
}

const widthClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-3xl',
};

export function DrawerPanel({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  width = 'lg',
  className,
}: DrawerPanelProps) {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/50 transition-opacity"
        onClick={onClose}
      />
      <div
        className={cn(
          'fixed inset-y-0 right-0 z-50 flex w-full flex-col bg-background shadow-2xl',
          widthClasses[width],
          className
        )}
      >
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-foreground">{title}</h2>
            )}
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
        <ScrollArea className="flex-1 px-6">
          <div className="py-6">{children}</div>
        </ScrollArea>
        {footer && (
          <div className="border-t border-border px-6 py-4">{footer}</div>
        )}
      </div>
    </>
  );
}

export default DrawerPanel;
