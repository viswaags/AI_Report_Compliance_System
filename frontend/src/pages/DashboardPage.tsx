import { Bell, ClipboardCheck, FileText, Gauge, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { KPICard } from '@/components/KPICard';
import { StatusBadge } from '@/components/StatusBadge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useCurrentUser } from '@/hooks/useAuth';
import {
  useAdminDashboard,
  useAdminReportSummary,
  useAdminRepositoryStats,
  useClubPerformance,
  useCoordinatorDashboard,
  useFacultyDashboard,
  useRecentNotifications,
  useRecentReports,
  useStudentDashboard,
} from '@/hooks/useDashboard';

type BackendUser = {
  name: string;
  role: 'ADMIN' | 'CLUB_COORDINATOR' | 'FACULTY_REPRESENTATIVE' | 'STUDENT_REPRESENTATIVE';
};

type ReportItem = {
  id?: number;
  report_id?: number;
  event_title?: string | null;
  status?: string;
  current_version?: number;
};

type NotificationItem = {
  id: number;
  title: string;
  message: string;
  notification_type?: string;
  is_read?: boolean;
  created_at?: string;
};

type ClubPerformance = {
  club_id: number;
  club_name: string;
  total_events: number;
  approved_events: number;
  approval_rate: number;
};

const kpiLabels: Record<string, string> = {
  total_users: 'Total Users',
  total_clubs: 'Total Clubs',
  total_events: 'Total Events',
  total_reports: 'Total Reports',
  approved_reports: 'Approved Reports',
  repository_records: 'Repository Records',
  total_notifications: 'Total Notifications',
  unread_notifications: 'Unread Notifications',
  managed_clubs: 'Managed Clubs',
  pending_reviews: 'Pending Reviews',
  total_participants: 'Total Participants',
  clubs: 'Clubs',
  events: 'Events',
  reports: 'Reports',
  records: 'Records',
  approved: 'Approved',
  compliance_passed: 'Compliance Passed',
  correction_required: 'Correction Required',
  revision_required: 'Revision Required',
};

const icons = [Users, FileText, ClipboardCheck, Bell, Gauge];

function titleize(value: string) {
  return kpiLabels[value] ?? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function numericEntries(data: unknown) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return [];

  return Object.entries(data as Record<string, unknown>)
    .filter(([, value]) => typeof value === 'number')
    .map(([key, value]) => ({ key, label: titleize(key), value: value as number }));
}

function reportId(report: ReportItem) {
  return report.id ?? report.report_id ?? Math.random();
}

function useRoleDashboardQuery(role?: BackendUser['role']) {
  const student = useStudentDashboard(role === 'STUDENT_REPRESENTATIVE');
  const coordinator = useCoordinatorDashboard(role === 'CLUB_COORDINATOR');
  const faculty = useFacultyDashboard(role === 'FACULTY_REPRESENTATIVE');
  const admin = useAdminDashboard(role === 'ADMIN');

  if (role === 'ADMIN') return admin;
  if (role === 'CLUB_COORDINATOR') return coordinator;
  if (role === 'FACULTY_REPRESENTATIVE') return faculty;
  return student;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const currentUserQuery = useCurrentUser();
  const user = currentUserQuery.data as BackendUser | undefined;
  const dashboardQuery = useRoleDashboardQuery(user?.role);
  const hasRole = Boolean(user?.role);
  const isAdmin = user?.role === 'ADMIN';
  const recentReportsQuery = useRecentReports(hasRole);
  const recentNotificationsQuery = useRecentNotifications(hasRole);
  const adminReportSummaryQuery = useAdminReportSummary(isAdmin);
  const clubPerformanceQuery = useClubPerformance(isAdmin);
  const repositoryStatsQuery = useAdminRepositoryStats(isAdmin);

  const dashboardData = dashboardQuery.data as Record<string, unknown> | undefined;
  const dashboardKpis = numericEntries(dashboardData);
  const adminReportSummary = isAdmin ? numericEntries(adminReportSummaryQuery.data) : [];
  const repositoryStats = isAdmin ? numericEntries(repositoryStatsQuery.data) : [];
  const recentReports = Array.isArray(recentReportsQuery.data)
    ? (recentReportsQuery.data as ReportItem[])
    : Array.isArray(dashboardData?.reports)
      ? (dashboardData.reports as ReportItem[])
      : Array.isArray(dashboardData?.pending_review_reports)
        ? (dashboardData.pending_review_reports as ReportItem[])
        : [];
  const recentNotifications = Array.isArray(recentNotificationsQuery.data)
    ? (recentNotificationsQuery.data as NotificationItem[])
    : [];
  const clubPerformance = Array.isArray(clubPerformanceQuery.data)
    ? (clubPerformanceQuery.data as ClubPerformance[])
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.name ?? 'there'}!</p>
      </div>

      {dashboardQuery.isError ? (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Unable to load dashboard.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {dashboardQuery.isLoading ? (
            <Card className="xl:col-span-4">
              <CardContent className="py-8 text-center text-muted-foreground">Loading dashboard...</CardContent>
            </Card>
          ) : (
            dashboardKpis.map((item, index) => (
              <KPICard
                key={item.key}
                title={item.label}
                value={item.value}
                icon={icons[index % icons.length]}
              />
            ))
          )}
        </div>
      )}

      {isAdmin && (adminReportSummary.length > 0 || repositoryStats.length > 0) && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[...adminReportSummary, ...repositoryStats].map((item, index) => (
            <KPICard
              key={`admin-${item.key}`}
              title={item.label}
              value={item.value}
              icon={icons[index % icons.length]}
            />
          ))}
        </div>
      )}

      {isAdmin && clubPerformance.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Club Performance</CardTitle>
            <CardDescription>Backend club event approval metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={clubPerformance}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="club_name" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="approval_rate" fill="hsl(212, 100%, 35%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {recentReports.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Reports</CardTitle>
              <CardDescription>Latest backend report activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentReports.map((report) => (
                  <div
                    key={reportId(report)}
                    className="flex cursor-pointer items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                    onClick={() => navigate('/app/reports')}
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{report.event_title ?? `Report #${reportId(report)}`}</p>
                      {report.current_version && (
                        <p className="text-xs text-muted-foreground">Version {report.current_version}</p>
                      )}
                    </div>
                    {report.status && <StatusBadge status={report.status} />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {recentNotifications.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Notifications</CardTitle>
              <CardDescription>Your latest backend notifications</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                    onClick={() => navigate('/app/notifications')}
                  >
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium">{notification.title}</p>
                      <p className="line-clamp-2 text-xs text-muted-foreground">{notification.message}</p>
                      {notification.created_at && (
                        <p className="text-xs text-muted-foreground">
                          {new Date(notification.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <Badge variant={notification.is_read ? 'secondary' : 'default'}>
                      {notification.notification_type ?? (notification.is_read ? 'Read' : 'Unread')}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default DashboardPage;
