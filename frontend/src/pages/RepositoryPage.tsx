import { useMemo, useState } from 'react';
import {
  Archive,
  Calendar,
  FileText,
  Tag,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, Column } from '@/components/DataTable';
import { DrawerPanel } from '@/components/DrawerPanel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useQueries } from '@tanstack/react-query';
import api from '@/lib/api';
import { useClubs, useMyClubs } from '@/hooks/useClubs';
import { useAuth } from '@/contexts/AuthContext';

type BackendClub = {
  id: number;
  club_name: string;
  description?: string | null;
};

type RepositoryRecordRow = {
  id: string;
  backendId: number;
  club_id: number;
  event_id: number;
  report_id: number;
  event_title: string;
  event_category?: string | null;
  event_date?: string | null;
  coordinators_organizers?: string | null;
  venue?: string | null;
  participant_count?: number | null;
  approved_by: number;
  approved_at?: string | null;
  created_at?: string | null;
  clubName: string;
};

const categoryColors = ['#0d4f8b', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6'];

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

export function RepositoryPage() {
  const { user } = useAuth();
  const [selectedRecord, setSelectedRecord] = useState<RepositoryRecordRow | null>(null);
  const isAdmin = user?.role === 'ADMIN';

  const recordsQuery = useQuery({
    queryKey: ['repository', 'records'],
    queryFn: () => api.getRepositoryRecords(),
    enabled: isAdmin,
  });
  const statsQuery = useQuery({
    queryKey: ['repository', 'stats'],
    queryFn: () => api.getRepositoryStats(),
    enabled: isAdmin,
  });
  const allClubsQuery = useClubs(isAdmin);
  const myClubsQuery = useMyClubs(!isAdmin);

  const clubsSource = isAdmin ? allClubsQuery.data : myClubsQuery.data;
  const clubs = Array.isArray(clubsSource) ? (clubsSource as BackendClub[]) : [];
  const accessibleClubIds = useMemo(
    () => new Set(clubs.map((club) => club.id)),
    [clubs]
  );
  const clubRecordQueries = useQueries({
    queries: !isAdmin
      ? clubs.map((club) => ({
          queryKey: ['repository', 'club', club.id],
          queryFn: () => api.getClubRepositoryRecords(club.id),
        }))
      : [],
  });
  const clubNames = useMemo(
    () => new Map(clubs.map((club) => [club.id, club.club_name])),
    [clubs]
  );

  const rawRecords = isAdmin
    ? (Array.isArray(recordsQuery.data) ? recordsQuery.data : [])
    : clubRecordQueries.flatMap((query) => (Array.isArray(query.data) ? query.data : []));
  const repositoryLoading = isAdmin
    ? recordsQuery.isLoading || allClubsQuery.isLoading
    : myClubsQuery.isLoading || clubRecordQueries.some((query) => query.isLoading);
  const repositoryError = isAdmin
    ? recordsQuery.isError
    : myClubsQuery.isError || clubRecordQueries.some((query) => query.isError);

  const records: RepositoryRecordRow[] = rawRecords
    .filter((record: any) => isAdmin || accessibleClubIds.has(record.club_id))
    .map((record: any) => ({
      id: String(record.id),
      backendId: record.id,
      club_id: record.club_id,
      event_id: record.event_id,
      report_id: record.report_id,
      event_title: record.event_title,
      event_category: record.event_category,
      event_date: record.event_date,
      coordinators_organizers: record.coordinators_organizers,
      venue: record.venue,
      participant_count: record.participant_count,
      approved_by: record.approved_by,
      approved_at: record.approved_at,
      created_at: record.created_at,
      clubName: clubNames.get(record.club_id) ?? `Club #${record.club_id}`,
    }));

  const recordColumns: Column<RepositoryRecordRow>[] = [
    {
      key: 'event_title',
      header: 'Event',
      sortable: true,
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-medium">{record.event_title}</p>
            <p className="text-xs text-muted-foreground">Report #{record.report_id}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'clubName',
      header: 'Club',
      sortable: true,
    },
    {
      key: 'event_category',
      header: 'Category',
      sortable: true,
      render: (value) => value ? <Badge variant="secondary">{String(value)}</Badge> : 'Unavailable',
    },
    {
      key: 'event_date',
      header: 'Event Date',
      sortable: true,
      render: (value) => formatDate(value as string | null),
    },
    {
      key: 'participant_count',
      header: 'Participants',
      sortable: true,
      render: (value) => value == null ? 'Unavailable' : String(value),
    },
  ];

  const recordsByClub = clubs.map((club) => ({
    club: club.club_name,
    records: records.filter((record) => record.club_id === club.id).length,
  }));

  const recordsByCategory = records.reduce((acc, record) => {
    const category = record.event_category || 'Uncategorized';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const categoryData = Object.entries(recordsByCategory).map(([category, count]) => ({
    name: category,
    value: count,
  }));

  const repositoryStats = statsQuery.data as { total_records?: number; total_participants?: number } | undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Repository</h1>
          <p className="text-muted-foreground">Access approved reports and archived event records</p>
        </div>
      </div>

      <Tabs defaultValue="records" className="space-y-4">
        <TabsList>
          <TabsTrigger value="records">
            <Archive className="mr-2 h-4 w-4" />
            Records
          </TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="records">
          <Card>
            <CardHeader>
              <CardTitle>Archived Records</CardTitle>
              <CardDescription>Approved event records returned by the backend</CardDescription>
            </CardHeader>
            <CardContent>
              {repositoryError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load repository records.
                </p>
              ) : (
                <DataTable
                  data={records}
                  columns={recordColumns}
                  searchPlaceholder="Search records..."
                  searchKeys={['event_title', 'event_category', 'venue', 'clubName']}
                  loading={repositoryLoading}
                  emptyMessage="No repository records available"
                  onRowClick={(record) => setSelectedRecord(record)}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics">
          <div className="grid gap-6 lg:grid-cols-2">
            {user?.role === 'ADMIN' && (
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Repository Totals</CardTitle>
                  <CardDescription>Backend repository summary</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-lg border border-border p-4">
                    <p className="text-sm text-muted-foreground">Total Records</p>
                    <p className="text-2xl font-semibold">
                      {statsQuery.isLoading ? '...' : repositoryStats?.total_records ?? records.length}
                    </p>
                  </div>
                  <div className="rounded-lg border border-border p-4">
                    <p className="text-sm text-muted-foreground">Total Participants</p>
                    <p className="text-2xl font-semibold">
                      {statsQuery.isLoading ? '...' : repositoryStats?.total_participants ?? 'Unavailable'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Records by Club</CardTitle>
                <CardDescription>Distribution of archived records</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={recordsByClub}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="club" className="text-xs" />
                    <YAxis className="text-xs" allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="records" fill="hsl(212, 100%, 35%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Records by Category</CardTitle>
                <CardDescription>Event categories in repository</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {categoryData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={categoryColors[index % categoryColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 flex flex-wrap justify-center gap-4">
                  {categoryData.map((item, index) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: categoryColors[index % categoryColors.length] }}
                      />
                      <span className="text-sm">{item.name}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <DrawerPanel
        open={!!selectedRecord}
        onClose={() => setSelectedRecord(null)}
        title="Record Details"
        width="lg"
      >
        {selectedRecord && (
          <div className="space-y-6">
            <div className="rounded-lg border border-border p-4">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">{selectedRecord.event_title}</p>
                  <p className="text-sm text-muted-foreground">Report #{selectedRecord.report_id}</p>
                </div>
              </div>

              <div className="grid gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Club:</span>
                  <span className="font-medium">{selectedRecord.clubName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Approved:</span>
                  <span className="font-medium">{formatDate(selectedRecord.approved_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Approved By:</span>
                  <span className="font-medium">User #{selectedRecord.approved_by}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="mb-3 flex items-center gap-2 font-medium">
                <Tag className="h-4 w-4" />
                Category
              </h4>
              <Badge variant="secondary">{selectedRecord.event_category || 'Uncategorized'}</Badge>
            </div>

            <div>
              <h4 className="mb-3 flex items-center gap-2 font-medium">
                <Calendar className="h-4 w-4" />
                Event Information
              </h4>
              <div className="space-y-2 rounded-lg border border-border p-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Event Date:</span>
                  <span className="font-medium">{formatDate(selectedRecord.event_date)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Venue:</span>
                  <span className="font-medium">{selectedRecord.venue || 'Unavailable'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Participants:</span>
                  <span className="font-medium">{selectedRecord.participant_count ?? 'Unavailable'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Organizers:</span>
                  <span className="font-medium">{selectedRecord.coordinators_organizers || 'Unavailable'}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </DrawerPanel>
    </div>
  );
}

export default RepositoryPage;
