import { useEffect, useMemo, useState } from 'react';
import { Plus, Power, PowerOff, UserPlus, UsersRound } from 'lucide-react';
import { toast } from 'sonner';
import { useQueries } from '@tanstack/react-query';
import { DataTable, Column } from '@/components/DataTable';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { User, UserRole } from '@/types';
import {
  useActivateUser,
  useCreateUser,
  useDeactivateUser,
  useUsers,
  useUsersForMembership,
} from "@/hooks/useUsers";
import {
  clubKeys,
  useAssignMembership,
  useBulkAssignMembership,
  useClubs,
  useMemberships,
  useMyClubs,
} from '@/hooks/useClubs';
import api from '@/lib/api';

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
  created_at?: string;

  user: User;

  club: BackendClub;
};

type AssignableRole = 'CLUB_COORDINATOR' | 'FACULTY_REPRESENTATIVE' | 'STUDENT_REPRESENTATIVE';

type UserRow = Omit<User, 'id'> & {
  id: string;
  backendId: number;
};

type MembershipRow = Omit<BackendMembership, 'id'> & {
  id: string;
  backendId: number;
  user?: User;
  club?: BackendClub;
  status: 'ACTIVE' | 'INACTIVE';
};

const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: 'Administrator',
  CLUB_COORDINATOR: 'Club Coordinator',
  FACULTY_REPRESENTATIVE: 'Faculty Representative',
  STUDENT_REPRESENTATIVE: 'Student Representative',
};

const createUserSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  role: z.enum(['CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE']),
});

const assignMembershipSchema = z.object({
  userId: z.string().min(1, 'User is required'),
  clubIds: z.array(z.string()).min(1, 'Select at least one club'),
  role: z.enum([
    'CLUB_COORDINATOR',
    'FACULTY_REPRESENTATIVE',
    'STUDENT_REPRESENTATIVE',
  ]),
});

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error) return error.message;
  return fallback;
}

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [assignMembershipOpen, setAssignMembershipOpen] = useState(false);

  const isAdmin = currentUser?.role === 'ADMIN';
  const isCoordinator = currentUser?.role === 'CLUB_COORDINATOR';

  const roleOptions = useMemo<AssignableRole[]>(() => {
    if (isAdmin) return ['CLUB_COORDINATOR'];
    if (isCoordinator) return ['FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'];
    return [];
  }, [isAdmin, isCoordinator]);

  const usersQuery = useUsers();
  const usersForMembershipQuery = useUsersForMembership();
  const membershipsQuery = useMemberships(isAdmin);
  const allClubsQuery = useClubs(isAdmin);
  const myClubsQuery = useMyClubs(isCoordinator);
  const createUser = useCreateUser();
  const activateUser = useActivateUser();
  const deactivateUser = useDeactivateUser();
  const assignMembership = useAssignMembership();
  const bulkAssignMembership = useBulkAssignMembership();

  const visibleClubs = (Array.isArray(isAdmin ? allClubsQuery.data : myClubsQuery.data)
    ? (isAdmin ? allClubsQuery.data : myClubsQuery.data) as BackendClub[]
    : []);
  const coordinatorClubMembers = useQueries({
    queries: isCoordinator
      ? visibleClubs.map((club) => ({
          queryKey: clubKeys.members(club.id),
          queryFn: () => api.getClubMembers(club.id),
        }))
      : [],
  });

  const users: User[] =
  Array.isArray(usersQuery.data)
    ? (usersQuery.data as User[])
    : [];

  const membershipUsers: User[] =
  Array.isArray(usersForMembershipQuery.data)
    ? (usersForMembershipQuery.data as User[])
    : [];

  const memberships: BackendMembership[] = isAdmin && Array.isArray(membershipsQuery.data)
    ? (membershipsQuery.data as BackendMembership[])
    : coordinatorClubMembers.flatMap((query) => (
        Array.isArray(query.data) ? (query.data as BackendMembership[]) : []
      ));

  const createUserForm = useForm<z.infer<typeof createUserSchema>>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      role: roleOptions[0] ?? 'STUDENT_REPRESENTATIVE',
    },
  });

  const assignMembershipForm = useForm<z.infer<typeof assignMembershipSchema>>({
    resolver: zodResolver(assignMembershipSchema),
    defaultValues: {
      userId: '',
      clubIds: [],
      role: roleOptions[0] ?? 'STUDENT_REPRESENTATIVE',
    },
  });

  useEffect(() => {
    const defaultRole = roleOptions[0];
    if (!defaultRole) return;
    createUserForm.setValue('role', defaultRole);
    assignMembershipForm.setValue('role', defaultRole);
  }, [assignMembershipForm, createUserForm, roleOptions]);

  const userColumns: Column<UserRow>[] = [
    {
      key: 'name',
      header: 'User',
      sortable: true,
      render: (_, user) => (
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback>{user.name.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{user.name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      sortable: true,
      render: (value) => <Badge variant="secondary">{ROLE_LABELS[value as UserRole]}</Badge>,
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (value) => <StatusBadge status={value ? 'ACTIVE' : 'INACTIVE'} />,
    },
    ...(isAdmin
      ? [
          {
            key: 'actions',
            header: 'Actions',
            render: (_: unknown, user: UserRow) => (
              user.is_active ? (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={user.backendId === currentUser?.id || deactivateUser.isPending}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleDeactivateUser(user);
                  }}
                >
                  <PowerOff className="mr-2 h-4 w-4" />
                  Deactivate
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={activateUser.isPending}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleActivateUser(user);
                  }}
                >
                  <Power className="mr-2 h-4 w-4" />
                  Activate
                </Button>
              )
            ),
          } as Column<UserRow>,
        ]
      : []),
  ];

  const membershipColumns: Column<MembershipRow>[] = [
    {
      key: 'user',
      header: 'Member',
      sortable: true,
      render: (_, m) => (
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback>{m.user?.name?.charAt(0) ?? '?'}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{m.user?.name ?? `User #${m.user_id}`}</p>
            <p className="text-xs text-muted-foreground">{m.user?.email ?? 'Email unavailable'}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'club_id',
      header: 'Club',
      sortable: true,
      render: (_, m) => m.club?.club_name ?? `Club #${m.club_id}`,
    },
    {
      key: 'role',
      header: 'Position',
      sortable: true,
      render: (value) => (
        <Badge variant="outline">{ROLE_LABELS[value as UserRole]}</Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (value) => <StatusBadge status={value as string} />,
    },
    {
      key: 'created_at',
      header: 'Joined',
      sortable: true,
      render: (value) => value ? new Date(value as string).toLocaleDateString() : '-',
    },
  ];

  const userRows: UserRow[] = users.map((u) => ({ ...u, id: String(u.id), backendId: Number(u.id) }));
  const membershipRows: MembershipRow[] =
  memberships.map((m) => ({
    ...m,
    id: String(m.id),
    backendId: m.id,
    user: m.user,
    club: m.club,
    status: m.is_active ? "ACTIVE" : "INACTIVE",
  }));

  const assignableUsers =
  membershipUsers.filter(
    (u) =>
      roleOptions.some(
        (role) => role === u.role
      )
  );
  const isSubmittingMembership = assignMembership.isPending || bulkAssignMembership.isPending;
  const membershipLoading = isAdmin
    ? membershipsQuery.isLoading
    : coordinatorClubMembers.some((query) => query.isLoading);
  const membershipError = isAdmin
    ? membershipsQuery.isError
    : coordinatorClubMembers.some((query) => query.isError);

  const handleCreateUser = async (data: z.infer<typeof createUserSchema>) => {
    try {
      await createUser.mutateAsync(data);
      await usersQuery.refetch();
      toast.success("User created successfully.");
      setCreateUserOpen(false);
      createUserForm.reset({
        name: '',
        email: '',
        password: '',
        role: roleOptions[0] ?? 'STUDENT_REPRESENTATIVE',
      });
    } catch (error) {
      toast.error(getErrorMessage(error, 'Unable to create user.'));
    }
  };

  const handleActivateUser = async (user: UserRow) => {
    try {
      await activateUser.mutateAsync(user.backendId);
      toast.success('User activated successfully.');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Unable to activate user.'));
    }
  };

  const handleDeactivateUser = async (user: UserRow) => {
    try {
      await deactivateUser.mutateAsync(user.backendId);
      toast.success('User deactivated successfully.');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Unable to deactivate user.'));
    }
  };

  const handleAssignMembership = async (data: z.infer<typeof assignMembershipSchema>) => {
    try {
      const payload = {
        user_id: Number(data.userId),
        role: data.role,
      };

      if (data.clubIds.length === 1) {
        await assignMembership.mutateAsync({
          ...payload,
          club_id: Number(data.clubIds[0]),
        });
      } else {
        await bulkAssignMembership.mutateAsync({
          ...payload,
          club_ids: data.clubIds.map(Number),
        });
      }

      toast.success(data.clubIds.length === 1
        ? 'Membership assigned successfully.'
        : 'Memberships assigned successfully.');
      setAssignMembershipOpen(false);
      assignMembershipForm.reset({
        userId: "",
        clubIds: [],
        role: roleOptions[0] ?? "STUDENT_REPRESENTATIVE",
      });
    } catch (error) {
      toast.error(getErrorMessage(error, 'Unable to assign membership.'));
    }
  };

  const usersErrorMessage = getErrorMessage(usersQuery.error, 'Unable to load users.');
  const membershipsErrorMessage = getErrorMessage(
    isAdmin ? membershipsQuery.error : coordinatorClubMembers.find((query) => query.error)?.error,
    'Unable to load memberships.'
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Users & Memberships</h1>
          <p className="text-muted-foreground">Manage users and club memberships</p>
        </div>
      </div>

      <Tabs defaultValue="users" className="space-y-4">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="users">
              <UsersRound className="mr-2 h-4 w-4" />
              Users
            </TabsTrigger>
            <TabsTrigger value="memberships">Memberships</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <Dialog open={assignMembershipOpen} onOpenChange={setAssignMembershipOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" disabled={visibleClubs.length === 0 || roleOptions.length === 0}>
                  <UserPlus className="mr-2 h-4 w-4" />
                  Assign Membership
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Assign Membership</DialogTitle>
                  <DialogDescription>
                    Add a user to one or more clubs with a matching role.
                  </DialogDescription>
                </DialogHeader>
                <Form {...assignMembershipForm}>
                  <form onSubmit={assignMembershipForm.handleSubmit(handleAssignMembership)} className="space-y-4">
                    <FormField
                      control={assignMembershipForm.control}
                      name="userId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>User</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select user" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {assignableUsers.map((u) => (
                                <SelectItem key={u.id} value={String(u.id)}>
                                  {u.name} ({u.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={assignMembershipForm.control}
                      name="clubIds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Clubs</FormLabel>
                          <div className="max-h-48 space-y-2 overflow-y-auto rounded-md border border-border p-3">
                            {visibleClubs.map((club) => {
                              const clubId = String(club.id);
                              const checked = field.value.includes(clubId);
                              return (
                                <label key={club.id} className="flex items-center gap-2 text-sm">
                                  <Checkbox
                                    checked={checked}
                                    onCheckedChange={(value) => {
                                      const nextValue = value
                                        ? [...field.value, clubId]
                                        : field.value.filter((id) => id !== clubId);
                                      field.onChange(nextValue);
                                    }}
                                  />
                                  <span>{club.club_name}</span>
                                </label>
                              );
                            })}
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={assignMembershipForm.control}
                      name="role"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Role</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {roleOptions.map((role) => (
                                <SelectItem key={role} value={role}>
                                  {ROLE_LABELS[role]}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <DialogFooter>
                      <Button type="submit" disabled={isSubmittingMembership}>
                        {isSubmittingMembership ? 'Assigning...' : 'Assign Membership'}
                      </Button>
                    </DialogFooter>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>

            <Dialog open={createUserOpen} onOpenChange={setCreateUserOpen}>
              <DialogTrigger asChild>
                <Button disabled={roleOptions.length === 0}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create User
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New User</DialogTitle>
                  <DialogDescription>
                    Add a new user to the system.
                  </DialogDescription>
                </DialogHeader>
                <Form {...createUserForm}>
                  <form onSubmit={createUserForm.handleSubmit(handleCreateUser)} className="space-y-4">
                    <FormField
                      control={createUserForm.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={createUserForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input type="email" placeholder="Enter email" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={createUserForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Temporary Password</FormLabel>
                          <FormControl>
                            <Input type="password" autoComplete="new-password" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={createUserForm.control}
                      name="role"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Role</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {roleOptions.map((role) => (
                                <SelectItem key={role} value={role}>
                                  {ROLE_LABELS[role]}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <DialogFooter>
                      <Button type="submit" disabled={createUser.isPending}>
                        {createUser.isPending ? 'Creating...' : 'Create User'}
                      </Button>
                    </DialogFooter>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>
                {isAdmin ? 'All registered users in the system' : 'Users created by you'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {usersQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {usersErrorMessage}
                </p>
              ) : (
                <DataTable
                  data={userRows}
                  columns={userColumns}
                  searchPlaceholder="Search users..."
                  searchKeys={['name', 'email', 'role']}
                  loading={usersQuery.isLoading}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="memberships">
          <Card>
            <CardHeader>
              <CardTitle>Memberships</CardTitle>
              <CardDescription>Club membership assignments</CardDescription>
            </CardHeader>
            <CardContent>
              {membershipError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {membershipsErrorMessage}
                </p>
              ) : (
                <DataTable
                  data={membershipRows}
                  columns={membershipColumns}
                  searchPlaceholder="Search memberships..."
                  searchKeys={['role', 'status']}
                  loading={membershipLoading}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default UsersPage;
