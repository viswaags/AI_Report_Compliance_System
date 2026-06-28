import { useState } from 'react';
import { AlertTriangle, CheckCircle, ExternalLink, Eye, FileCheck, FileStack, FileText, History, MessageSquare, RefreshCcw, Upload } from 'lucide-react';
import { FileUpload } from '@/components/FileUpload';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from "@/components/ui/scroll-area";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useMyEvents } from '@/hooks/useEvents';
import { useCurrentUser } from '@/hooks/useAuth';
import {
  useReportCompliance,
  useReportFeedback,
  useReportHistory,
  useReportLatestReview,
  useReportSummary,
  useReportTemplateStatus,
  useReportVersions,
  useReports,
  useResubmitReport,
  useSubmitReport,
} from '@/hooks/useReports';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

type ReportStatus =
  | 'VALIDATING'
  | 'COMPLIANT'
  | 'COMPLIANCE_PASSED'
  | 'NON_COMPLIANT'
  | 'REVISION_REQUIRED'
  | 'APPROVED'
  | string;

type BackendReport = {
  id?: number;
  report_id?: number;
  event_id?: number;
  event_title?: string | null;
  status: ReportStatus;
  current_version?: number;
  version_no?: number;
  template_version?: string | number | null;
  template_id?: number | null;
  submitted_at?: string | null;
  created_at?: string | null;

  drive_url?: string | null;
  current_report_drive_url?: string | null;

  file_url?: string | null;
  file_path?: string | null;
};

type BackendEvent = {
  id: number;
  event_title?: string | null;
  title?: string | null;
};

type ReportRow = {
  id: string;
  reportId: number;
  eventId?: number;
  eventTitle?: string | null;
  status: ReportStatus;
  currentVersion?: number;
  templateVersion?: string | number | null;
  templateId?: number | null;
  submittedAt?: string | null;
  originalFileUrl?: string | null;
  originalFileLabel?: string | null;
};

type ComplianceResult = {
  validation_result_id?: number;
  compliance_score?: number;
  issues_json?: unknown;
  created_at?: string | null;
};

type FeedbackResult = {
  id?: number;
  feedback_text?: string;
  model_used?: string;
};

type ReviewResult = {
  id?: number;
  status?: string;
  comments?: string | null;
};

type HistoryEntry = {
  version?: {
    id?: number;
    version_no?: number;
  };
  validation?: ComplianceResult | null;
  feedback?: FeedbackResult | null;
  review?: ReviewResult | null;
};

type ReportVersion = {
  id?: number;
  version_no?: number;
  template_id?: number;
  template_version?: string | number | null;
  file_path?: string | null;
  drive_url?: string | null;
  file_url?: string | null;
  drive_file_id?: string | null;
  uploaded_at?: string | null;
  created_at?: string | null;
};

type ReportSummary = {
  event_title?: string | null;
  status?: ReportStatus;
  current_version?: number;
  template_id?: number | null;
};

type TemplateStatus = {
  is_latest?: boolean;
  current_template?: number | null;
  latest_template?: number | null;
  latest_version?: string | null;
};

const statusStyles: Record<string, string> = {
  VALIDATING: 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300',
  COMPLIANT: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300',
  NON_COMPLIANT: 'border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300',
  REVISION_REQUIRED: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300',
  APPROVED: 'border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950/40 dark:text-green-300',
};

function normalizeStatus(status: ReportStatus) {
  return status === 'COMPLIANCE_PASSED' ? 'COMPLIANT' : status;
}

function formatStatus(status: ReportStatus) {
  return normalizeStatus(status).replace(/_/g, ' ');
}

function ReportStatusBadge({ status, className }: { status: ReportStatus; className?: string }) {
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

function getEventTitle(event: BackendEvent) {
  return event.event_title ?? event.title ?? 'Untitled event';
}

function asReportRow(report: BackendReport, eventTitles: Map<number, string>): ReportRow {
  const reportId = report.id ?? report.report_id ?? 0;
  const eventTitle = report.event_title ?? (report.event_id ? eventTitles.get(report.event_id) : undefined);
  const originalFile = getFileTarget(report);

  return {
    id: String(reportId),
    reportId,
    eventId: report.event_id,
    eventTitle,
    status: report.status,
    currentVersion: report.current_version ?? report.version_no,
    templateVersion: report.template_version,
    templateId: report.template_id,
    submittedAt: report.submitted_at ?? report.created_at,
    originalFileUrl: originalFile.url,
    originalFileLabel: originalFile.label,
  };
}

function getFileTarget(record: {
  current_report_drive_url?: string | null;
  drive_url?: string | null;
  file_url?: string | null;
  file_path?: string | null;
}) {

  const target =
    record.current_report_drive_url ??
    record.drive_url ??
    record.file_url ??
    record.file_path ??
    null;

  if (!target) return { url: null, label: null };

  const isUrl = /^https?:\/\//i.test(target);

  return {
    url: isUrl ? target : null,
    label: target,
  };
}

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatReportVersion(version?: number | null) {
  return typeof version === 'number' ? `v${version}` : 'Unavailable';
}

function formatTemplateVersion(value?: string | number | null) {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  return typeof value === 'number' ? `Template #${value}` : String(value);
}

function isResubmissionAllowed(status: ReportStatus) {
  return ['REVISION_REQUIRED', 'CORRECTION_REQUIRED', 'NON_COMPLIANT'].includes(normalizeStatus(status));
}

function getComplianceIssueSummary(value: unknown): string[] {
  if (!value) return [];

  if (typeof value === 'string') {
    try {
      return getComplianceIssueSummary(JSON.parse(value));
    } catch {
      return [value];
    }
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const issue = item as Record<string, unknown>;
          return String(issue.message ?? issue.issue ?? issue.field ?? 'Compliance issue found');
        }
        return null;
      })
      .filter((item): item is string => Boolean(item));
  }

  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const nested = record.issues ?? record.errors ?? record.missing_fields ?? record.warnings;
    if (nested) return getComplianceIssueSummary(nested);
    return Object.entries(record)
      .filter(([, entry]) => Boolean(entry))
      .map(([key, entry]) => `${key.replace(/_/g, ' ')}: ${String(entry)}`);
  }

  return [];
}

function ComplianceScoreCell({ reportId }: { reportId: number }) {
  const complianceQuery = useReportCompliance(reportId);
  const compliance = complianceQuery.data as ComplianceResult | undefined;

  if (complianceQuery.isLoading) return <span className="text-muted-foreground">Loading...</span>;
  if (complianceQuery.isError || typeof compliance?.compliance_score !== 'number') {
    return <span className="text-muted-foreground">Unavailable</span>;
  }

  return <span className="font-medium">{Math.round(compliance.compliance_score)}%</span>;
}

function LastReviewCell({ reportId }: { reportId: number }) {
  const reviewQuery = useReportLatestReview(reportId);
  const review = reviewQuery.data as ReviewResult | null | undefined;

  if (reviewQuery.isLoading) return <span className="text-muted-foreground">Loading...</span>;
  if (reviewQuery.isError || !review?.status) return <span className="text-muted-foreground">No review</span>;

  return <div className="min-h-[28px] flex items-center">
    <ReportStatusBadge status={review.status} className="text-xs" />;
    </div>
}

function ReportActions({
  report,
  onViewDetails,
  onResubmit,
  canResubmit,
}: {
  report: ReportRow;
  onViewDetails: (report: ReportRow) => void;
  onResubmit: (report: ReportRow) => void;
  canResubmit: boolean;
}) {
  const canShowResubmit =
    canResubmit && isResubmissionAllowed(report.status);

  return (
    <div className="w-[250px] space-y-2">

      <div className="grid grid-cols-2 gap-2">

        {report.originalFileUrl ? (
          <Button size="sm" variant="outline" asChild>
            <a
              href={report.originalFileUrl}
              target="_blank"
              rel="noreferrer"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View Report
            </a>
          </Button>
        ) : (
          <Button size="sm" variant="outline" disabled>
            <ExternalLink className="mr-2 h-4 w-4" />
            View Report
          </Button>
        )}

        <Button
          size="sm"
          variant="outline"
          onClick={() => onViewDetails(report)}
        >
          <Eye className="mr-2 h-4 w-4" />
          View Details
        </Button>

      </div>

      <Button
        size="sm"
        className="w-full"
        disabled={!canShowResubmit}
        onClick={() => onResubmit(report)}
      >
        <RefreshCcw className="mr-2 h-4 w-4" />
        Resubmit Report
      </Button>

    </div>
  );
}

function ReportTableRow({
  report,
  onViewDetails,
  onResubmit,
  canResubmit,
}: {
  report: ReportRow;
  onViewDetails: (report: ReportRow) => void;
  onResubmit: (report: ReportRow) => void;
  canResubmit: boolean;
}) {
  const summaryQuery = useReportSummary(report.reportId);
  const versionsQuery = useReportVersions(report.reportId);
  const summary = summaryQuery.data as ReportSummary | undefined;
  const versions = Array.isArray(versionsQuery.data) ? (versionsQuery.data as ReportVersion[]) : [];
  const latestVersion = versions[0];
  const latestFile = latestVersion ? getFileTarget(latestVersion) : { url: null, label: null };
  const displayReport: ReportRow = {
    ...report,
    eventTitle: report.eventTitle ?? summary?.event_title,
    status: summary?.status ?? report.status,
    currentVersion: report.currentVersion ?? summary?.current_version ?? latestVersion?.version_no,
    templateVersion: report.templateVersion ?? latestVersion?.template_version,
    templateId: report.templateId ?? summary?.template_id ?? latestVersion?.template_id ?? null,
    submittedAt: report.submittedAt ?? latestVersion?.uploaded_at ?? latestVersion?.created_at,
    originalFileUrl: report.originalFileUrl ?? latestFile.url,
    originalFileLabel: report.originalFileLabel ?? latestFile.label,
  };

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <span className="font-medium">
            {summaryQuery.isLoading && !displayReport.eventTitle
              ? 'Loading event...'
              : displayReport.eventTitle ?? 'Event unavailable'}
          </span>
        </div>
      </TableCell>
      <TableCell>
        <ReportStatusBadge status={displayReport.status} className="text-xs" />
      </TableCell>
      <TableCell>
        <Badge variant="outline">{formatReportVersion(displayReport.currentVersion)}</Badge>
      </TableCell>
      <TableCell>
        <span className="text-sm">
          {formatTemplateVersion(displayReport.templateVersion ?? displayReport.templateId)}
        </span>
      </TableCell>
      <TableCell>
        <ComplianceScoreCell reportId={displayReport.reportId} />
      </TableCell>
      <TableCell>
        <LastReviewCell reportId={displayReport.reportId} />
      </TableCell>
      <TableCell>
        <span className="text-sm text-muted-foreground">{formatDate(displayReport.submittedAt)}</span>
      </TableCell>
      <TableCell className="w-[260px] align-top">
        <ReportActions
          report={displayReport}
          onViewDetails={onViewDetails}
          onResubmit={onResubmit}
          canResubmit={canResubmit}
        />
      </TableCell>
    </TableRow>
  );
}

function ReportDetailsDialog({
  report,
  open,
  onOpenChange,
}: {
  report: ReportRow | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const reportId = report?.reportId;
  const complianceQuery = useReportCompliance(reportId);
  const feedbackQuery = useReportFeedback(reportId);
  const historyQuery = useReportHistory(reportId);
  const latestReviewQuery = useReportLatestReview(reportId);
  const versionsQuery = useReportVersions(reportId);
  const templateStatusQuery = useReportTemplateStatus(reportId);
  const compliance = complianceQuery.data as ComplianceResult | undefined;
  const feedback = feedbackQuery.data as FeedbackResult | undefined;
  const latestReview = latestReviewQuery.data as ReviewResult | null | undefined;
  const history = Array.isArray(historyQuery.data) ? (historyQuery.data as HistoryEntry[]) : [];
  const versions = Array.isArray(versionsQuery.data) ? (versionsQuery.data as ReportVersion[]) : [];
  const templateStatus = templateStatusQuery.data as TemplateStatus | undefined;
  const latestVersion = versions[0];
  const latestFile = latestVersion ? getFileTarget(latestVersion) : { url: null, label: null };
  const originalFileUrl = report?.originalFileUrl ?? latestFile.url;
  const originalFileLabel = report?.originalFileLabel ?? latestFile.label;
  const complianceIssues = getComplianceIssueSummary(compliance?.issues_json);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] max-w-5xl flex-col overflow-hidden">
        <DialogHeader>
          <DialogTitle>{report?.eventTitle ?? 'Report Details'}</DialogTitle>
          <DialogDescription>
            {report ? `Report ${report.reportId} - Version ${report.currentVersion ?? 1}` : undefined}
          </DialogDescription>
        </DialogHeader>

        {report && (
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList className="h-auto flex-wrap justify-start">
                <TabsTrigger value="overview">
                  <FileText className="mr-2 h-4 w-4" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="compliance">
                  <FileCheck className="mr-2 h-4 w-4" />
                  Compliance
                </TabsTrigger>
                <TabsTrigger value="feedback">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Feedback
                </TabsTrigger>
                <TabsTrigger value="history">
                  <History className="mr-2 h-4 w-4" />
                  Review History
                </TabsTrigger>
                <TabsTrigger value="versions">
                  <FileStack className="mr-2 h-4 w-4" />
                  Report Versions
                </TabsTrigger>
                <TabsTrigger value="template">
                  <FileStack className="mr-2 h-4 w-4" />
                  Template Status
                </TabsTrigger>
              </TabsList>

              <TabsContent value="overview">
                <Card>
                  <CardHeader>
                    <CardTitle>Overview</CardTitle>
                    <CardDescription>Core report lifecycle information</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Event Title</p>
                      <p className="text-sm font-medium">{report.eventTitle ?? 'Unavailable'}</p>
                    </div>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Report Status</p>
                      <ReportStatusBadge status={report.status} className="mt-1 text-xs" />
                    </div>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Report Version</p>
                      <p className="text-sm font-medium">
                        {formatReportVersion(report.currentVersion ?? latestVersion?.version_no)}
                      </p>
                    </div>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Template Version</p>
                      <p className="text-sm font-medium">
                        {formatTemplateVersion(report.templateVersion ?? report.templateId ?? latestVersion?.template_version ?? latestVersion?.template_id)}
                      </p>
                    </div>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Submitted Date</p>
                      <p className="text-sm font-medium">{formatDate(report.submittedAt ?? latestVersion?.created_at)}</p>
                    </div>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-xs text-muted-foreground">Latest Review Status</p>
                      {latestReviewQuery.isLoading ? (
                        <p className="text-sm text-muted-foreground">Loading...</p>
                      ) : latestReview?.status ? (
                        <ReportStatusBadge status={latestReview.status} className="mt-1 text-xs" />
                      ) : (
                        <p className="text-sm text-muted-foreground">No review</p>
                      )}
                    </div>
                    <div className="rounded-lg border border-border p-3 sm:col-span-2 lg:col-span-3">
                      <p className="text-xs text-muted-foreground">Original Report</p>
                      {originalFileUrl ? (
                        <Button asChild variant="outline" size="sm" className="mt-2">
                          <a href={originalFileUrl} target="_blank" rel="noreferrer">
                            <ExternalLink className="mr-2 h-4 w-4" />
                            Open Original Report
                          </a>
                        </Button>
                      ) : originalFileLabel ? (
                        <p className="mt-1 break-all text-sm text-muted-foreground">{originalFileLabel}</p>
                      ) : (
                        <p className="mt-1 text-sm text-muted-foreground">No original report link available.</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="compliance">
                <Card>
                  <CardHeader>
                    <CardTitle>Compliance</CardTitle>
                    <CardDescription>Latest backend compliance result</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {complianceQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading compliance...</p>
                    ) : complianceQuery.isError ? (
                      <p className="text-sm text-muted-foreground">No compliance result available.</p>
                    ) : (
                      <>
                        <div className="flex items-center gap-3">
                          {typeof compliance?.compliance_score === 'number' && compliance.compliance_score >= 80 ? (
                            <CheckCircle className="h-5 w-5 text-emerald-500" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                          )}
                          <div>
                            <p className="text-sm text-muted-foreground">Compliance Score</p>
                            <p className="text-2xl font-semibold">
                              {typeof compliance?.compliance_score === 'number'
                                ? `${Math.round(compliance.compliance_score)}%`
                                : 'Unavailable'}
                            </p>
                          </div>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="rounded-lg border border-border p-3">
                            <p className="text-xs text-muted-foreground">Result</p>
                            <p className="text-sm font-medium">
                              {typeof compliance?.compliance_score === 'number' && compliance.compliance_score >= 80
                                ? 'Passed'
                                : 'Needs attention'}
                            </p>
                          </div>
                          <div className="rounded-lg border border-border p-3">
                            <p className="text-xs text-muted-foreground">Issues Found</p>
                            <p className="text-sm font-medium">{complianceIssues.length}</p>
                          </div>
                          <div className="rounded-lg border border-border p-3">
                            <p className="text-xs text-muted-foreground">Checked At</p>
                            <p className="text-sm font-medium">{formatDate(compliance?.created_at)}</p>
                          </div>
                        </div>
                        {complianceIssues.length > 0 ? (
                          <div className="rounded-lg border border-border p-4">
                            <p className="text-sm font-medium">Key Compliance Issues</p>

                                <ScrollArea className="mt-3 h-44 pr-3">
                                  <ul className="space-y-2 text-sm text-muted-foreground">
                                    {complianceIssues.map((issue, index) => (
                                      <li
                                        key={`${issue}-${index}`}
                                        className="list-disc ml-5"
                                      >
                                        {issue}
                                      </li>
                                      ))}
                                    </ul>
                                  </ScrollArea>
                                </div>
                        ) : (
                          <p className="rounded-lg border border-border p-4 text-sm text-muted-foreground">
                            No compliance issues were reported.
                          </p>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="feedback">
                <Card>
                  <CardHeader>
                    <CardTitle>Feedback</CardTitle>
                    <CardDescription>Latest backend feedback for this report</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {feedbackQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading feedback...</p>
                    ) : feedbackQuery.isError || !feedback?.feedback_text ? (
                      <p className="text-sm text-muted-foreground">No feedback available.</p>
                    ) : (
                      <div className="rounded-lg border border-border p-4">
                        <p className="whitespace-pre-wrap text-sm">{feedback.feedback_text}</p>
                        {feedback.model_used && (
                          <p className="mt-3 text-xs text-muted-foreground">Model: {feedback.model_used}</p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="history">
                <Card>
                  <CardHeader>
                    <CardTitle>Report History</CardTitle>
                    <CardDescription>Versions, feedback, and review actions</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {historyQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading history...</p>
                    ) : history.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No history available.</p>
                    ) : (
                      history.map((entry, index) => (
                        <div key={entry.version?.id ?? index} className="rounded-lg border border-border p-4">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-medium">Version {entry.version?.version_no ?? index + 1}</p>
                            {entry.review?.status && <ReportStatusBadge status={entry.review.status} />}
                          </div>
                          {typeof entry.validation?.compliance_score === 'number' && (
                            <p className="mt-2 text-sm text-muted-foreground">
                              Compliance score: {Math.round(entry.validation.compliance_score)}%
                            </p>
                          )}
                          {entry.feedback?.feedback_text && (
                            <p className="mt-2 text-sm">{entry.feedback.feedback_text}</p>
                          )}
                          {entry.review?.comments && (
                            <p className="mt-2 text-sm text-muted-foreground">{entry.review.comments}</p>
                          )}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="versions">
                <Card>
                  <CardHeader>
                    <CardTitle>Report Versions</CardTitle>
                    <CardDescription>Backend report version records</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {versionsQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading versions...</p>
                    ) : versions.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No versions available.</p>
                    ) : (
                      versions.map((version, index) => (
                        <div key={version.id ?? index} className="rounded-lg border border-border p-4">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-medium">Version {version.version_no ?? index + 1}</p>
                            {(version.template_version || version.template_id) && (
                              <Badge variant="outline">
                                {formatTemplateVersion(version.template_version ?? version.template_id)}
                              </Badge>
                            )}
                          </div>
                          {version.file_path && (
                            <p className="mt-2 break-all text-sm text-muted-foreground">{version.file_path}</p>
                          )}
                          {(version.drive_url || version.file_url) && (
                            <Button asChild variant="outline" size="sm" className="mt-3">
                              <a href={(version.drive_url ?? version.file_url) as string} target="_blank" rel="noreferrer">
                                <ExternalLink className="mr-2 h-4 w-4" />
                                Open File
                              </a>
                            </Button>
                          )}
                          {(version.uploaded_at || version.created_at) && (
                            <p className="mt-2 text-xs text-muted-foreground">
                              {formatDate(version.uploaded_at ?? version.created_at)}
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="template">
                <Card>
                  <CardHeader>
                    <CardTitle>Template Status</CardTitle>
                    <CardDescription>Whether this report used the current active template</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {templateStatusQuery.isLoading ? (
                      <p className="text-sm text-muted-foreground">Loading template status...</p>
                    ) : templateStatusQuery.isError ? (
                      <p className="text-sm text-muted-foreground">Template status unavailable.</p>
                    ) : (
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div className="rounded-lg border border-border p-3">
                          <p className="text-xs text-muted-foreground">Status</p>
                          <p className="text-sm font-medium">{templateStatus?.is_latest ? 'Current' : 'Outdated'}</p>
                        </div>
                        <div className="rounded-lg border border-border p-3">
                          <p className="text-xs text-muted-foreground">Report Template</p>
                          <p className="text-sm font-medium">
                            {formatTemplateVersion(report.templateVersion ?? report.templateId ?? templateStatus?.current_template)}
                          </p>
                        </div>
                        <div className="rounded-lg border border-border p-3">
                          <p className="text-xs text-muted-foreground">Active Template</p>
                          <p className="text-sm font-medium">
                            {formatTemplateVersion(templateStatus?.latest_version ?? templateStatus?.latest_template)}
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<ReportRow | null>(null);
  const [resubmitReportRow, setResubmitReportRow] = useState<ReportRow | null>(null);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [submitFile, setSubmitFile] = useState<File | null>(null);
  const [resubmitFile, setResubmitFile] = useState<File | null>(null);

  const currentUserQuery = useCurrentUser();
  const reportsQuery = useReports({ limit: 100 });
  const myEventsQuery = useMyEvents();
  const submitReport = useSubmitReport();
  const resubmitReport = useResubmitReport();
  const currentUser = currentUserQuery.data as { role?: string } | undefined;
  const canSubmitReports = currentUser?.role === 'STUDENT_REPRESENTATIVE';

  const myEvents = Array.isArray(myEventsQuery.data) ? (myEventsQuery.data as BackendEvent[]) : [];
  const eventTitles = new Map(myEvents.map((event) => [event.id, getEventTitle(event)]));
  const reports = (Array.isArray(reportsQuery.data) ? (reportsQuery.data as BackendReport[]) : [])
    .map((report) => asReportRow(report, eventTitles))
    .filter((report) => report.reportId > 0);

  const handleSubmitReport = () => {
    if (!submitFile || !selectedEventId) return;

    submitReport.mutate(
      { eventId: selectedEventId, file: submitFile },
      {
        onSuccess: () => {
          setSelectedEventId('');
          setSubmitFile(null);
          toast.success('Report submitted successfully.');
        },
        onError: () => {
          toast.error('Unable to submit report.');
        },
      }
    );
  };

  const handleResubmitReport = () => {
  if (!resubmitReportRow || !resubmitFile) return;

  resubmitReport.mutate(
    {
      reportId: resubmitReportRow.reportId,
      file: resubmitFile,
    },
    {
      onSuccess: () => {
          toast.success("Report resubmitted successfully.");
      },

      onError: () => {
          toast.error("Unable to resubmit report.");
      },

      onSettled: async () => {
          setResubmitFile(null);
          setResubmitReportRow(null);

          resubmitReport.reset();

          await reportsQuery.refetch();
      },
    }
  );
};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Reports</h1>
        <p className="text-muted-foreground">Submit, validate, and track event reports</p>
      </div>

      <Tabs defaultValue="list" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="list">
            <FileText className="mr-2 h-4 w-4" />
            Report List
          </TabsTrigger>
          {canSubmitReports && (
            <TabsTrigger value="submit">
              <Upload className="mr-2 h-4 w-4" />
              Submit Report
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="list">
          <Card>
            <CardHeader>
              <CardTitle>All Reports</CardTitle>
              <CardDescription>Backend report status, compliance, and review state</CardDescription>
            </CardHeader>
            <CardContent>
              {reportsQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load reports.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-64">Event Title</TableHead>
                      <TableHead className="w-36">Report Status</TableHead>
                      <TableHead className="w-36">Report Version</TableHead>
                      <TableHead className="w-36">Template Version</TableHead>
                      <TableHead className="w-24">Compliance Score</TableHead>
                      <TableHead className="w-36">Latest Review</TableHead>
                      <TableHead className="w-44">Submitted Date</TableHead>
                      <TableHead className="w-[260px] text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportsQuery.isLoading ? (
                      <TableRow>
                        <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                          Loading reports...
                        </TableCell>
                      </TableRow>
                    ) : reports.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                          No reports available
                        </TableCell>
                      </TableRow>
                    ) : (
                      reports.map((report) => (
                        <ReportTableRow
                          key={report.id}
                          report={report}
                          onViewDetails={setSelectedReport}
                          onResubmit={setResubmitReportRow}
                          canResubmit={canSubmitReports}
                        />
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {canSubmitReports && (
        <TabsContent value="submit">
          <Card>
            <CardHeader>
              <CardTitle>Submit New Report</CardTitle>
              <CardDescription>Choose one of your events and upload the report file</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium">Event</label>
                <Select value={selectedEventId} onValueChange={setSelectedEventId} disabled={myEventsQuery.isLoading}>
                  <SelectTrigger>
                    <SelectValue placeholder={myEventsQuery.isLoading ? 'Loading events...' : 'Select event'} />
                  </SelectTrigger>
                  <SelectContent>
                    {myEvents.map((event) => (
                      <SelectItem key={event.id} value={String(event.id)}>
                        {getEventTitle(event)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {myEventsQuery.isError && (
                  <p className="text-sm text-destructive">Unable to load your events.</p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Upload Report File</label>
                <FileUpload
                  selectedFile={submitFile}
                  onFileSelect={setSubmitFile}
                  onFileRemove={() => setSubmitFile(null)}
                  accept=".pdf,.doc,.docx"
                  disabled={submitReport.isPending}
                />
              </div>

              {submitReport.isError && (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to submit report.
                </p>
              )}

              <div className="flex justify-end">
                <Button
                  disabled={!submitFile || !selectedEventId || submitReport.isPending}
                  onClick={handleSubmitReport}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {submitReport.isPending ? 'Submitting...' : 'Submit Report'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        )}
      </Tabs>

      <ReportDetailsDialog
        report={selectedReport}
        open={!!selectedReport}
        onOpenChange={(open) => !open && setSelectedReport(null)}
      />

      <Dialog
        open={!!resubmitReportRow}
        onOpenChange={(open) => {
          if (!open) {
              setResubmitReportRow(null);
              setResubmitFile(null);

              resubmitReport.reset();
          }
      }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Resubmit Report</DialogTitle>
            <DialogDescription>{resubmitReportRow?.eventTitle ?? 'Upload a revised report file'}</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <FileUpload
              selectedFile={resubmitFile}
              onFileSelect={setResubmitFile}
              onFileRemove={() => setResubmitFile(null)}
              accept=".pdf,.doc,.docx"
              disabled={resubmitReport.isPending}
            />
          </div>
          {resubmitReport.isError && (
            <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              Unable to resubmit report.
            </p>
          )}
          <DialogFooter>
            <Button
              disabled={!resubmitFile || resubmitReport.isPending}
              onClick={handleResubmitReport}
            >
              <RefreshCcw className="mr-2 h-4 w-4" />
              {resubmitReport.isPending ? 'Validating...' : 'Resubmit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ReportsPage;
