import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";
import { reportKeys } from "./useReports";

export const reviewKeys = {
  all: ["reviews"] as const,
  lists: () => [...reviewKeys.all, "list"] as const,
  list: () => [...reviewKeys.lists()] as const,
  pending: () => [...reviewKeys.lists(), "pending"] as const,
  stats: () => [...reviewKeys.all, "stats"] as const,
  report: (reportId: number) => [...reviewKeys.all, "report", reportId] as const,
  reportDetails: (reportId: number) =>
    [...reviewKeys.report(reportId), "details"] as const,
  history: (reportId: number) => [...reviewKeys.report(reportId), "history"] as const,
  latest: (reportId: number) => [...reviewKeys.report(reportId), "latest"] as const,
};

export function useReviews() {
  return useQuery({
    queryKey: reviewKeys.list(),
    queryFn: () => api.getReviews(),
  });
}

export function usePendingReviews() {
  return useQuery({
    queryKey: reviewKeys.pending(),
    queryFn: () => api.getPendingReviews(),
  });
}

export function useReviewStats() {
  return useQuery({
    queryKey: reviewKeys.stats(),
    queryFn: () => api.getReviewStats(),
  });
}

export function useReviewReportDetails(reportId: number | undefined) {
  return useQuery({
    queryKey: reviewKeys.reportDetails(reportId ?? 0),
    queryFn: () => api.getReviewReportDetails(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useReviewHistory(reportId: number | undefined) {
  return useQuery({
    queryKey: reviewKeys.history(reportId ?? 0),
    queryFn: () => api.getReviewHistory(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useLatestReview(reportId: number | undefined) {
  return useQuery({
    queryKey: reviewKeys.latest(reportId ?? 0),
    queryFn: () => api.getLatestReview(reportId as number),
    enabled: typeof reportId === "number",
  });
}

export function useApproveReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { reportId: number; comments: string }) =>
      api.approveReview(variables.reportId, variables.comments),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: reviewKeys.all });
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
      void queryClient.invalidateQueries({
        queryKey: reportKeys.detail(variables.reportId),
      });
    },
  });
}

export function useRequestRevision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { reportId: number; comments: string }) =>
      api.requestRevision(variables.reportId, variables.comments),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: reviewKeys.all });
      void queryClient.invalidateQueries({ queryKey: reportKeys.all });
      void queryClient.invalidateQueries({
        queryKey: reportKeys.detail(variables.reportId),
      });
    },
  });
}
