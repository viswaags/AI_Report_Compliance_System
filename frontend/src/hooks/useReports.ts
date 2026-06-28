import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const reportKeys = {
  all: ["reports"] as const,
  lists: () => [...reportKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number }) =>
    [...reportKeys.lists(), params] as const,
  myReports: () => [...reportKeys.lists(), "my"] as const,
  details: () => [...reportKeys.all, "detail"] as const,
  detail: (reportId: number) => [...reportKeys.details(), reportId] as const,
  status: (reportId: number) => [...reportKeys.detail(reportId), "status"] as const,
  summary: (reportId: number) => [...reportKeys.detail(reportId), "summary"] as const,
  history: (reportId: number) => [...reportKeys.detail(reportId), "history"] as const,
  versions: (reportId: number) => [...reportKeys.detail(reportId), "versions"] as const,
  compliance: (reportId: number) =>
    [...reportKeys.detail(reportId), "compliance"] as const,
  feedback: (reportId: number) => [...reportKeys.detail(reportId), "feedback"] as const,
  emailDraft: (reportId: number) =>
    [...reportKeys.detail(reportId), "email-draft"] as const,
  latestReview: (reportId: number) =>
    [...reportKeys.detail(reportId), "latest-review"] as const,
  templateStatus: (reportId: number) =>
    [...reportKeys.detail(reportId), "template-status"] as const,
};

export function useReports(params: { skip?: number; limit?: number } = {}) {
  const normalizedParams = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 20,
  };

  return useQuery({
    queryKey: reportKeys.list(normalizedParams),
    queryFn: () => api.getReports(normalizedParams.skip, normalizedParams.limit),
  });
}

export function useReport(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.detail(reportId ?? 0),
    queryFn: () => api.getReport(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useMyReports() {
  return useQuery({
    queryKey: reportKeys.myReports(),
    queryFn: () => api.getMyReports(),
  });
}

export function useReportStatus(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.status(reportId ?? 0),
    queryFn: () => api.getReportStatus(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportSummary(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.summary(reportId ?? 0),
    queryFn: () => api.getReportSummary(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportHistory(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.history(reportId ?? 0),
    queryFn: () => api.getReportHistory(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportVersions(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.versions(reportId ?? 0),
    queryFn: () => api.getReportVersions(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportCompliance(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.compliance(reportId ?? 0),
    queryFn: () => api.getReportCompliance(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportFeedback(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.feedback(reportId ?? 0),
    queryFn: () => api.getReportFeedback(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportEmailDraft(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.emailDraft(reportId ?? 0),
    queryFn: () => api.getReportEmailDraft(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportLatestReview(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.latestReview(reportId ?? 0),
    queryFn: () => api.getReportLatestReview(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReportTemplateStatus(reportId: number | undefined) {
  return useQuery({
    queryKey: reportKeys.templateStatus(reportId ?? 0),
    queryFn: () => api.getReportTemplateStatus(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useSubmitReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { eventId: string; file: File }) => api.submitReport(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
    },
  });
}

export function useResubmitReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { reportId: number; file: File }) =>
      api.resubmitReport(variables.reportId, variables.file),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
      void queryClient.invalidateQueries({
        queryKey: reportKeys.detail(variables.reportId),
      });
    },
  });
}

export function useGenerateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (validationResultId: number) =>
      api.generateFeedback(validationResultId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
    },
  });
}

export function useGenerateFeedbackBundle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (validationResultId: number) =>
      api.generateFeedbackBundle(validationResultId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
    },
  });
}
