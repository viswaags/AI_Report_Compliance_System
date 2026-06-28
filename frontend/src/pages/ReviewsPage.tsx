import { useState } from 'react';
import { CheckCircle, ClipboardCheck, Clock, FileText, History, MessageSquare, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import {
  useApproveReview,
  useLatestReview,
  usePendingReviews,
  useRequestRevision,
  useReviewHistory,
  useReviewReportDetails,
  useReviewStats,
} from '@/hooks/useReviews';
import { cn } from '@/lib/utils';

type ReviewStatus =
  | 'VALIDATING'
  | 'COMPLIANT'
  | 'COMPLIANCE_PASSED'
  | 'NON_COMPLIANT'
  | 'REVISION_REQUIRED'
  | 'APPROVED'
  | string;

type PendingReview = {
  report_id: number;
  event_title?: string | null;
  current_version?: number | null;
  status: ReviewStatus;
  drive_url?: string | null;
};

type ReviewRow = {
  id: string;
  reportId: number;
  eventTitle?: string | null;
  currentVersion?: number | null;
  status: ReviewStatus;
  driveUrl?: string | null;
};

type ReportDetails = {
  report_id?: number;
  drive_url?: string | null;
  version?: {
    version_no?: number;
  };
  extraction?: unknown;
  validation?: {
    id?: number;
    compliance_score?: number;
    issues_json?: unknown;
  } | null;
};

type ReviewRecord = {
  id?: number;
  report_id: number;
  reviewer_id?: number;
  status: ReviewStatus;
  comments?: string | null;
};

type ReviewStats = {
  pending_reviews?: number;
  approved?: number;
  revision_required?: number;
};

const revisionReasonOptions = [
  'Missing required event details',
  'Compliance score needs correction',
  'Budget or attendance information is incomplete',
  'Images, signatures, or proof documents are missing',
  'Formatting does not match the active template',
];

const approvalConfirmationOptions = [
  'Report uses the correct template',
  'Required event details are complete',
  'Compliance result is acceptable',
  'Supporting documents are sufficient',
  'Final report is ready for repository archival',
];

const statusStyles: Record<string, string> = {
  VALIDATING: 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300',
  COMPLIANT: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300',
  NON_COMPLIANT: 'border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300',
  REVISION_REQUIRED: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300',
  APPROVED: 'border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950/40 dark:text-green-300',
};

function normalizeStatus(status: ReviewStatus) {
  return status === 'COMPLIANCE_PASSED' ? 'COMPLIANT' : status;
}

function formatStatus(status: ReviewStatus) {
  return normalizeStatus(status).replace(/_/g, ' ');
}

function ReviewStatusBadge({ status, className }: { status: ReviewStatus; className?: string }) {
  const normalized = normalizeStatus(status);

  return (
    <Badge
      variant="outline"
      className={cn(
        'font-semibold uppercase tracking-normal',
        statusStyles[normalized] ?? 'border-slate-200 bg-slate-50 text-slate-700',
        className
      )}
    >
      {formatStatus(status)}
    </Badge>
  );
}

function asReviewRow(review: PendingReview): ReviewRow {
  return {
    id: String(review.report_id),
    reportId: review.report_id,
    eventTitle: review.event_title,
    currentVersion: review.current_version,
    status: review.status,
    driveUrl: review.drive_url,
  };
}

function renderJson(value: unknown) {
  if (!value) return 'No data available.';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

function ComplianceScoreCell({ reportId }: { reportId: number }) {
  const detailsQuery = useReviewReportDetails(reportId);
  const details = detailsQuery.data as ReportDetails | undefined;

  if (detailsQuery.isLoading) return <span className="text-muted-foreground">Loading...</span>;
  if (detailsQuery.isError || typeof details?.validation?.compliance_score !== 'number') {
    return <span className="text-muted-foreground">Unavailable</span>;
  }

  return <span className="font-medium">{Math.round(details.validation.compliance_score)}%</span>;
}

function LastReviewCell({ reportId }: { reportId: number }) {
  const latestReviewQuery = useLatestReview(reportId);
  const latestReview = latestReviewQuery.data as ReviewRecord | null | undefined;

  if (latestReviewQuery.isLoading) return <span className="text-muted-foreground">Loading...</span>;
  if (latestReviewQuery.isError || !latestReview?.status) {
    return <span className="text-muted-foreground">No review</span>;
  }

  return <ReviewStatusBadge status={latestReview.status} className="text-xs" />;
}

function ReviewDialog({
  review,
  open,
  onOpenChange,
}: {
  review: ReviewRow | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reviewComment, setReviewComment] = useState('');
  const [revisionReasons, setRevisionReasons] = useState<string[]>([]);
  const [approvalConfirmations, setApprovalConfirmations] = useState<string[]>([]);
  const reportId = review?.reportId;
  const detailsQuery = useReviewReportDetails(reportId);
  const historyQuery = useReviewHistory(reportId);
  const latestReviewQuery = useLatestReview(reportId);
  const approveReview = useApproveReview();
  const requestRevision = useRequestRevision();
  const details = detailsQuery.data as ReportDetails | undefined;
  const history = Array.isArray(historyQuery.data) ? (historyQuery.data as ReviewRecord[]) : [];
  const latestReview = latestReviewQuery.data as ReviewRecord | null | undefined;

  const closeDialog = () => {
    setReviewComment('');
    setRevisionReasons([]);
    setApprovalConfirmations([]);
    onOpenChange(false);
  };

  const toggleSelection = (
    value: string,
    selectedValues: string[],
    setSelectedValues: (values: string[]) => void
  ) => {
    setSelectedValues(
      selectedValues.includes(value)
        ? selectedValues.filter((item) => item !== value)
        : [...selectedValues, value]
    );
  };

  const buildReviewComments = (items: string[], label: string) => {
    const sections = [];
    if (items.length > 0) {
      sections.push(`${label}:\n${items.map((item) => `- ${item}`).join('\n')}`);
    }
    if (reviewComment.trim()) {
      sections.push(`Comments:\n${reviewComment.trim()}`);
    }
    return sections.join('\n\n');
  };

  const handleApprove = () => {
    if (!review) return;

    approveReview.mutate(
      {
        reportId: review.reportId,
        comments: buildReviewComments(approvalConfirmations, 'Approval confirmations'),
      },
      {
        onSuccess: () => {
          toast.success('Report approved successfully.');
          closeDialog();
        },
        onError: () => {
          toast.error('Unable to approve report.');
        },
      }
    );
  };

  const handleRequestRevision = () => {
    if (!review) return;

    requestRevision.mutate(
      {
        reportId: review.reportId,
        comments: buildReviewComments(revisionReasons, 'Revision reasons'),
      },
      {
        onSuccess: () => {
          toast.success('Revision requested successfully.');
          closeDialog();
        },
        onError: () => {
          toast.error('Unable to request revision.');
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => (nextOpen ? onOpenChange(true) : closeDialog())}>
      <DialogContent className="flex max-h-[90vh] w-[calc(100vw-2rem)] max-w-4xl flex-col overflow-hidden sm:w-full">
        <DialogHeader>
          <DialogTitle>{review?.eventTitle ?? 'Review Report'}</DialogTitle>
          <DialogDescription>
            {review ? `Version ${review.currentVersion ?? details?.version?.version_no ?? 1}` : undefined}
          </DialogDescription>
        </DialogHeader>

        {review && (
          <div className="min-h-0 flex-1 space-y-6 overflow-y-auto pr-1">
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground">Event Title</p>
                <p className="text-sm font-medium">{review.eventTitle ?? 'Unavailable'}</p>
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground">Status</p>
                <ReviewStatusBadge status={review.status} className="mt-1 text-xs" />
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground">Version</p>
                <p className="text-sm font-medium">
                  v{details?.version?.version_no ?? review.currentVersion ?? 1}
                </p>
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs text-muted-foreground">Last Review</p>
                {latestReviewQuery.isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading...</p>
                ) : latestReview?.status ? (
                  <ReviewStatusBadge status={latestReview.status} className="mt-1 text-xs" />
                ) : (
                  <p className="text-sm text-muted-foreground">No review</p>
                )}
              </div>
            </div>

            <Tabs defaultValue="details" className="space-y-4">
              <TabsList className="flex-wrap">
                <TabsTrigger value="details">
                  <ClipboardCheck className="mr-2 h-4 w-4" />
                  Details
                </TabsTrigger>
                <TabsTrigger value="extraction">
                  <FileText className="mr-2 h-4 w-4" />
                  Extraction
                </TabsTrigger>
                <TabsTrigger value="history">
                  <History className="mr-2 h-4 w-4" />
                  History
                </TabsTrigger>
              </TabsList>

              <TabsContent value="details">
                <Card>
                  <CardHeader>
                    <CardTitle>Review Details</CardTitle>
                    <CardDescription>Latest report version and validation result</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {detailsQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading report details...</p>
                    ) : detailsQuery.isError ? (
                      <p className="text-sm text-muted-foreground">No report details available.</p>
                    ) : (
                      <>
                        {details?.drive_url && (
                          <Button asChild variant="outline">
                            <a href={details.drive_url} target="_blank" rel="noreferrer">
                              Open Report File
                            </a>
                          </Button>
                        )}
                        <div className="rounded-lg border border-border p-3">
                          <p className="text-xs text-muted-foreground">Compliance Score</p>
                          <p className="text-sm font-medium">
                            {typeof details?.validation?.compliance_score === 'number'
                              ? `${Math.round(details.validation.compliance_score)}%`
                              : 'Unavailable'}
                          </p>
                        </div>
                        <pre className="max-h-64 overflow-auto rounded-lg border border-border bg-muted/30 p-3 text-xs">
                          {renderJson(details?.validation?.issues_json)}
                        </pre>
                      </>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="extraction">
                <Card>
                  <CardHeader>
                    <CardTitle>Extracted Report Data</CardTitle>
                    <CardDescription>Structured extraction from the latest report version</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <pre className="max-h-96 overflow-auto rounded-lg border border-border bg-muted/30 p-3 text-xs">
                      {renderJson(details?.extraction)}
                    </pre>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="history">
                <Card>
                  <CardHeader>
                    <CardTitle>Review History</CardTitle>
                    <CardDescription>Previous review decisions for this report</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {historyQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading history...</p>
                    ) : history.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No review history available.</p>
                    ) : (
                      history.map((item) => (
                        <div key={item.id ?? `${item.report_id}-${item.status}`} className="rounded-lg border border-border p-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-medium">
                              Reviewer {item.reviewer_id ? `#${item.reviewer_id}` : 'unavailable'}
                            </p>
                            <ReviewStatusBadge status={item.status} />
                          </div>
                          {item.comments && (
                            <p className="mt-2 text-sm text-muted-foreground">{item.comments}</p>
                          )}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Revision Reasons</CardTitle>
                  <CardDescription>Select common issues before requesting changes</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {revisionReasonOptions.map((reason) => (
                    <div key={reason} className="flex items-start gap-2">
                      <Checkbox
                        id={`revision-${reason}`}
                        checked={revisionReasons.includes(reason)}
                        onCheckedChange={() => toggleSelection(reason, revisionReasons, setRevisionReasons)}
                      />
                      <Label htmlFor={`revision-${reason}`} className="text-sm font-normal leading-snug">
                        {reason}
                      </Label>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Approval Confirmations</CardTitle>
                  <CardDescription>Confirm the report is ready before approval</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {approvalConfirmationOptions.map((confirmation) => (
                    <div key={confirmation} className="flex items-start gap-2">
                      <Checkbox
                        id={`approval-${confirmation}`}
                        checked={approvalConfirmations.includes(confirmation)}
                        onCheckedChange={() => toggleSelection(confirmation, approvalConfirmations, setApprovalConfirmations)}
                      />
                      <Label htmlFor={`approval-${confirmation}`} className="text-sm font-normal leading-snug">
                        {confirmation}
                      </Label>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <div>
              <Label htmlFor="review-comment">Optional Comments</Label>
              <Textarea
                id="review-comment"
                placeholder="Add any additional notes..."
                value={reviewComment}
                onChange={(event) => setReviewComment(event.target.value)}
                className="mt-2"
                rows={4}
              />
            </div>

            {(approveReview.isError || requestRevision.isError) && (
              <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                Unable to submit review action.
              </p>
            )}
          </div>
        )}

        <DialogFooter className="sticky bottom-0 -mx-6 -mb-6 border-t border-border bg-background px-6 py-4 sm:justify-end">
          <Button
            variant="outline"
            className="w-full text-amber-600 border-amber-600 hover:bg-amber-50 sm:w-auto"
            disabled={requestRevision.isPending || approveReview.isPending}
            onClick={handleRequestRevision}
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Request Revision
          </Button>
          <Button
            className="w-full bg-emerald-600 hover:bg-emerald-700 sm:w-auto"
            disabled={requestRevision.isPending || approveReview.isPending}
            onClick={handleApprove}
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            Approve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ReviewsPage() {
  const [selectedReview, setSelectedReview] = useState<ReviewRow | null>(null);
  const pendingQuery = usePendingReviews();
  const statsQuery = useReviewStats();
  const stats = (statsQuery.data ?? {}) as ReviewStats;
  const pendingReviews = (Array.isArray(pendingQuery.data) ? (pendingQuery.data as PendingReview[]) : [])
    .map(asReviewRow);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Reviews</h1>
        <p className="text-muted-foreground">Review and approve submitted reports</p>
      </div>

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="pending">
            <Clock className="mr-2 h-4 w-4" />
            Pending Reviews
            {pendingReviews.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {pendingReviews.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="pending">
          <Card>
            <CardHeader>
              <CardTitle>Pending Reviews</CardTitle>
              <CardDescription>Reports awaiting approval or revision feedback</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load pending reviews.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event Title</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Compliance Score</TableHead>
                      <TableHead>Last Review Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingQuery.isLoading ? (
                      <TableRow>
                        <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                          Loading pending reviews...
                        </TableCell>
                      </TableRow>
                    ) : pendingReviews.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                          No pending reviews
                        </TableCell>
                      </TableRow>
                    ) : (
                      pendingReviews.map((review) => (
                        <TableRow key={review.id}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                <FileText className="h-5 w-5 text-primary" />
                              </div>
                              <span className="font-medium">{review.eventTitle ?? 'Event unavailable'}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <ReviewStatusBadge status={review.status} className="text-xs" />
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">v{review.currentVersion ?? 1}</Badge>
                          </TableCell>
                          <TableCell>
                            <ComplianceScoreCell reportId={review.reportId} />
                          </TableCell>
                          <TableCell>
                            <LastReviewCell reportId={review.reportId} />
                          </TableCell>
                          <TableCell className="text-right">
                            <Button size="sm" variant="outline" onClick={() => setSelectedReview(review)}>
                              Review
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics">
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="h-4 w-4" />
                  Pending
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">{statsQuery.isLoading ? '-' : stats.pending_reviews ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle className="h-4 w-4" />
                  Approved
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">{statsQuery.isLoading ? '-' : stats.approved ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <RefreshCcw className="h-4 w-4" />
                  Revision Required
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">{statsQuery.isLoading ? '-' : stats.revision_required ?? 0}</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <ReviewDialog
        review={selectedReview}
        open={!!selectedReview}
        onOpenChange={(open) => !open && setSelectedReview(null)}
      />
    </div>
  );
}

export default ReviewsPage;
