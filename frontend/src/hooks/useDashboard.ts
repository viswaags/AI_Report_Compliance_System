import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";

export const dashboardKeys = {
  all: ["dashboard"] as const,
  recentNotifications: () => [...dashboardKeys.all, "recent-notifications"] as const,
  recentReports: () => [...dashboardKeys.all, "recent-reports"] as const,
  student: () => [...dashboardKeys.all, "student"] as const,
  studentReportStatus: () =>
    [...dashboardKeys.student(), "report-status"] as const,
  coordinator: () => [...dashboardKeys.all, "coordinator"] as const,
  faculty: () => [...dashboardKeys.all, "faculty"] as const,
  admin: () => [...dashboardKeys.all, "admin"] as const,
  adminReportSummary: () => [...dashboardKeys.admin(), "report-summary"] as const,
  clubPerformance: () => [...dashboardKeys.admin(), "club-performance"] as const,
  adminRepositoryStats: () =>
    [...dashboardKeys.admin(), "repository-stats"] as const,
};

export function useRecentNotifications(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.recentNotifications(),
    queryFn: () => api.getRecentNotifications(),
    enabled,
  });
}

export function useRecentReports(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.recentReports(),
    queryFn: () => api.getRecentReports(),
    enabled,
  });
}

export function useStudentDashboard(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.student(),
    queryFn: () => api.getStudentDashboard(),
    enabled,
  });
}

export function useStudentReportStatus(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.studentReportStatus(),
    queryFn: () => api.getStudentReportStatus(),
    enabled,
  });
}

export function useCoordinatorDashboard(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.coordinator(),
    queryFn: () => api.getCoordinatorDashboard(),
    enabled,
  });
}

export function useFacultyDashboard(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.faculty(),
    queryFn: () => api.getFacultyDashboard(),
    enabled,
  });
}

export function useAdminDashboard(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.admin(),
    queryFn: () => api.getAdminDashboard(),
    enabled,
  });
}

export function useAdminReportSummary(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.adminReportSummary(),
    queryFn: () => api.getAdminReportSummary(),
    enabled,
  });
}

export function useClubPerformance(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.clubPerformance(),
    queryFn: () => api.getClubPerformance(),
    enabled,
  });
}

export function useAdminRepositoryStats(enabled = true) {
  return useQuery({
    queryKey: dashboardKeys.adminRepositoryStats(),
    queryFn: () => api.getAdminRepositoryStats(),
    enabled,
  });
}
