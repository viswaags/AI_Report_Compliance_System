import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const statusBadgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        validating: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
        compliance_passed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
        correction_required: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
        revision_required: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
        approved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
        rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
        under_review: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
        draft: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
        archived: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
        active: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
        inactive: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
        pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
        read: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
        unread: 'bg-blue-600 text-white',
        pass: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
        fail: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
        warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
        upcoming: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300',
        ongoing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
        completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
        cancelled: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
      },
    },
    defaultVariants: {
      variant: 'draft',
    },
  }
);

export type StatusVariant = VariantProps<typeof statusBadgeVariants>['variant'];

interface StatusBadgeProps {
  status: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  const variant = getVariantFromStatus(status);
  const formattedStatus = formatStatus(status);

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1',
  };

  return (
    <span className={cn(statusBadgeVariants({ variant }), sizeClasses[size], className)}>
      {formattedStatus}
    </span>
  );
}

function getVariantFromStatus(status: string): StatusVariant {
  const statusMap: Record<string, StatusVariant> = {
    VALIDATING: 'validating',
    COMPLIANCE_PASSED: 'compliance_passed',
    CORRECTION_REQUIRED: 'correction_required',
    REVISION_REQUIRED: 'revision_required',
    APPROVED: 'approved',
    REJECTED: 'rejected',
    UNDER_REVIEW: 'under_review',
    DRAFT: 'draft',
    ARCHIVED: 'archived',
    ACTIVE: 'active',
    INACTIVE: 'inactive',
    PENDING: 'pending',
    READ: 'read',
    UNREAD: 'unread',
    PASS: 'pass',
    FAIL: 'fail',
    WARNING: 'warning',
    UPCOMING: 'upcoming',
    ONGOING: 'ongoing',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
  };

  return statusMap[status] || 'draft';
}

function formatStatus(status: string): string {
  const statusLabels: Record<string, string> = {
    VALIDATING: 'Validating',
    COMPLIANCE_PASSED: 'Passed',
    CORRECTION_REQUIRED: 'Correction Required',
    REVISION_REQUIRED: 'Revision Required',
    APPROVED: 'Approved',
    REJECTED: 'Rejected',
    UNDER_REVIEW: 'Under Review',
    DRAFT: 'Draft',
    ARCHIVED: 'Archived',
    ACTIVE: 'Active',
    INACTIVE: 'Inactive',
    PENDING: 'Pending',
    READ: 'Read',
    UNREAD: 'Unread',
    PASS: 'Pass',
    FAIL: 'Fail',
    WARNING: 'Warning',
    UPCOMING: 'Upcoming',
    ONGOING: 'Ongoing',
    COMPLETED: 'Completed',
    CANCELLED: 'Cancelled',
  };

  return statusLabels[status] || status;
}

export { statusBadgeVariants };
