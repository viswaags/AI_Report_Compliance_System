import { useState } from 'react';
import { Plus, Users } from 'lucide-react';
import { toast } from 'sonner';
import { DataTable, Column } from '@/components/DataTable';
import { DrawerPanel } from '@/components/DrawerPanel';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types';
import { useClubMembers, useClubs, useCreateClub, useMyClubs } from '@/hooks/useClubs';

type BackendClub = {
  id: number;
  club_name: string;
  description?: string | null;
};

type BackendMembership = {
  id: number;
  user_id: number;
  club_id: number;
  role: UserRole;
  is_active: boolean;

  user: {
    id: number;
    name: string;
    email: string;
    role: UserRole;
  };

  club: {
    id: number;
    club_name: string;
  };
};

type ClubRow = {
  id: string;
  backendId: number;
  serial: number;
  club_name: string;
  description: string;
};

const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: 'Administrator',
  CLUB_COORDINATOR: 'Club Coordinator',
  FACULTY_REPRESENTATIVE: 'Faculty Representative',
  STUDENT_REPRESENTATIVE: 'Student Representative',
};

const createClubSchema = z.object({
  club_name: z.string().min(1, 'Club name is required'),
  description: z.string().optional(),
});

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error) return error.message;
  return fallback;
}

function MemberList({
  title,
  memberships,
}: {
  title: string;
  memberships: BackendMembership[];
}) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="font-medium">{title}</p>
        <Badge variant="secondary">{memberships.length}</Badge>
      </div>
        {memberships.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No members assigned.</p>
                ) : (
                  <div className="space-y-3">
                    {memberships.map((membership) => (
              <div
                  key={membership.id}
                  className="rounded-md border border-border/70 p-3"
              >
                  <p className="font-medium">
                      {membership.user.name}
                  </p>

                  <p className="text-sm text-muted-foreground">
                      {membership.user.email}
                  </p>
              </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ClubsPage() {
  const { user } = useAuth();
  const [selectedClub, setSelectedClub] = useState<ClubRow | null>(null);
  const [createClubOpen, setCreateClubOpen] = useState(false);

  const isAdmin = user?.role === 'ADMIN';
  const clubsQuery = useClubs(isAdmin);
  const myClubsQuery = useMyClubs(!isAdmin);
  const clubMembersQuery = useClubMembers(selectedClub?.backendId);
  const createClub = useCreateClub();

  const createClubForm = useForm<z.infer<typeof createClubSchema>>({
    resolver: zodResolver(createClubSchema),
    defaultValues: {
      club_name: '',
      description: '',
    },
  });

  const rawClubs = (Array.isArray(isAdmin ? clubsQuery.data : myClubsQuery.data)
    ? (isAdmin ? clubsQuery.data : myClubsQuery.data) as BackendClub[]
    : []);

  const clubs: ClubRow[] = rawClubs.map((club, index) => ({
    id: String(club.id),
    backendId: club.id,
    serial: index + 1,
    club_name: club.club_name,
    description: club.description ?? '',
  }));

  const selectedMemberships = Array.isArray(clubMembersQuery.data)
    ? (clubMembersQuery.data as BackendMembership[])
    : [];

  const facultyRepresentatives = selectedMemberships.filter(
    (membership) => membership.role === 'FACULTY_REPRESENTATIVE'
  );
  const studentRepresentatives = selectedMemberships.filter(
    (membership) => membership.role === 'STUDENT_REPRESENTATIVE'
  );

  const clubColumns: Column<ClubRow>[] = [
    {
      key: 'serial',
      header: '#',
      sortable: true,
      className: 'w-16',
      render: (value) => String(value),
    },
    {
      key: 'club_name',
      header: 'Club Name',
      sortable: true,
      render: (_, club) => (
        <div>
          <p className="font-medium">{club.club_name}</p>
          <p className="text-xs text-muted-foreground">{club.description || 'No description'}</p>
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      sortable: true,
      render: (value) => (
        <span className="text-muted-foreground">{value ? String(value) : 'No description'}</span>
      ),
    },
  ];

  const handleCreateClub = async (data: z.infer<typeof createClubSchema>) => {
    try {
      await createClub.mutateAsync({
        club_name: data.club_name,
        description: data.description?.trim() || undefined,
      });
      toast.success('Club created successfully.');
      setCreateClubOpen(false);
      createClubForm.reset();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Unable to create club.'));
    }
  };

  const activeQuery = isAdmin ? clubsQuery : myClubsQuery;
  const errorMessage = getErrorMessage(activeQuery.error, 'Unable to load clubs.');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Clubs</h1>
          <p className="text-muted-foreground">Manage clubs and view their details</p>
        </div>
        {isAdmin && (
          <Dialog open={createClubOpen} onOpenChange={setCreateClubOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Club
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Club</DialogTitle>
                <DialogDescription>Add a club to the system.</DialogDescription>
              </DialogHeader>
              <Form {...createClubForm}>
                <form onSubmit={createClubForm.handleSubmit(handleCreateClub)} className="space-y-4">
                  <FormField
                    control={createClubForm.control}
                    name="club_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Club Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Club name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={createClubForm.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Brief description" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <DialogFooter>
                    <Button type="submit" disabled={createClub.isPending}>
                      {createClub.isPending ? 'Creating...' : 'Create Club'}
                    </Button>
                  </DialogFooter>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <Tabs defaultValue="clubs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="clubs">
            <Users className="mr-2 h-4 w-4" />
            Clubs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="clubs">
          <Card>
            <CardHeader>
              <CardTitle>{isAdmin ? 'All Clubs' : 'Assigned Clubs'}</CardTitle>
              <CardDescription>
                {isAdmin ? 'Registered clubs in the system' : 'Clubs assigned to your account'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {activeQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {errorMessage}
                </p>
              ) : (
                <DataTable
                  data={clubs}
                  columns={clubColumns}
                  searchPlaceholder="Search clubs..."
                  searchKeys={['club_name', 'description']}
                  loading={activeQuery.isLoading}
                  onRowClick={(club) => setSelectedClub(club)}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <DrawerPanel
        open={!!selectedClub}
        onClose={() => setSelectedClub(null)}
        title={selectedClub?.club_name}
        description={selectedClub?.description}
        width="lg"
      >
        {selectedClub && (
          <div className="space-y-4">
            <div className="rounded-lg border border-border p-4">
              <p className="text-sm text-muted-foreground">Club Name</p>
              <p className="text-lg font-medium">{selectedClub.club_name}</p>
            </div>
            <div className="rounded-lg border border-border p-4">
              <p className="text-sm text-muted-foreground">Description</p>
              <p className="text-sm">{selectedClub.description || 'No description'}</p>
            </div>
            {clubMembersQuery.isError ? (
              <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {getErrorMessage(clubMembersQuery.error, 'Unable to load club members.')}
              </p>
            ) : clubMembersQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading members...</p>
            ) : (
              <>
                <MemberList
                    title={ROLE_LABELS.FACULTY_REPRESENTATIVE}
                    memberships={facultyRepresentatives}
                />
                <MemberList
                    title={ROLE_LABELS.STUDENT_REPRESENTATIVE}
                    memberships={studentRepresentatives}
                />
              </>
            )}
          </div>
        )}
      </DrawerPanel>
    </div>
  );
}

export default ClubsPage;
