import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertTriangle, Lock, LogOut, Mail, Shield, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useChangePassword, useCurrentUser } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';

type BackendUser = {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  must_change_password?: boolean;
};

export function AccountPage() {
  const { logout } = useAuth();
  const [searchParams] = useSearchParams();
  const currentUserQuery = useCurrentUser();
  const changePassword = useChangePassword();
  const user = currentUserQuery.data as BackendUser | undefined;
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  const handleChangePassword = () => {
    setPasswordMessage(null);

    if (newPassword !== confirmPassword) {
      setPasswordMessage('New passwords do not match.');
      return;
    }

    changePassword.mutate(
      {
        oldPassword: currentPassword,
        newPassword,
      },
      {
        onSuccess: () => {
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
          setPasswordMessage('Password changed successfully. Redirecting to sign in...');
          toast.success('Password changed successfully. Please sign in again.');
          logout();
        },
        onError: () => {
          setPasswordMessage('Unable to change password.');
          toast.error('Unable to change password.');
        },
      }
    );
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      ADMIN: 'Administrator',
      CLUB_COORDINATOR: 'Club Coordinator',
      FACULTY_REPRESENTATIVE: 'Faculty Representative',
      STUDENT_REPRESENTATIVE: 'Student Representative',
    };
    return labels[role] || role;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Account Settings</h1>
        <p className="text-muted-foreground">Manage your profile and security settings</p>
      </div>

      {user?.must_change_password && (
        <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800 dark:text-amber-300">Password change required</p>
              <p className="text-sm text-amber-700 dark:text-amber-400">
                Update your password from the Security tab before continuing regular account use.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue={searchParams.get('tab') === 'security' || user?.must_change_password ? 'security' : 'profile'} className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">
            <User className="mr-2 h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security">
            <Lock className="mr-2 h-4 w-4" />
            Security
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>Your backend account details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {currentUserQuery.isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading account...</p>
                ) : currentUserQuery.isError || !user ? (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    Unable to load account details.
                  </p>
                ) : (
                  <>
                    <div className="flex items-center gap-6">
                      <Avatar className="h-20 w-20">
                        <AvatarFallback className="bg-primary text-2xl text-primary-foreground">
                          {user.name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <h3 className="text-xl font-semibold">{user.name}</h3>
                        <p className="text-muted-foreground">{user.email}</p>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Name</Label>
                        <Input value={user.name} disabled />
                      </div>
                      <div className="space-y-2">
                        <Label>Email</Label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                          <Input value={user.email} disabled className="pl-10" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Role</Label>
                        <Input value={getRoleLabel(user.role)} disabled />
                      </div>
                      <div className="space-y-2">
                        <Label>Active Status</Label>
                        <div>
                          <Badge
                            variant={user.is_active ? 'default' : 'secondary'}
                            className="mt-1 py-1.5"
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Role & Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Shield className="h-5 w-5 text-primary" />
                    <div>
                      <p className="font-medium">{user ? getRoleLabel(user.role) : 'Unavailable'}</p>
                      <p className="text-sm text-muted-foreground">
                        {user?.is_active ? 'Account is active' : 'Account is inactive'}
                      </p>
                    </div>
                  </div>
                  {user && (
                    <Badge
                      variant={user.role === 'ADMIN' ? 'default' : 'secondary'}
                      className="w-full justify-center py-2"
                    >
                      {user.role}
                    </Badge>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button variant="outline" className="w-full justify-start" asChild>
                    <a href="/app/notifications">
                      <Mail className="mr-2 h-4 w-4" />
                      View Notifications
                    </a>
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full justify-start"
                    onClick={logout}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="security">
          <div className="max-w-2xl">
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>
                  Update your password using your current password
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Current Password</Label>
                  <Input
                    id="current-password"
                    type="password"
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                    placeholder="Enter your current password"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input
                    id="new-password"
                    type="password"
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    placeholder="Enter new password"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Confirm new password"
                  />
                </div>

                {passwordMessage && (
                  <p
                    className={
                      passwordMessage.includes('success')
                        ? 'text-sm text-emerald-600'
                        : 'text-sm text-destructive'
                    }
                  >
                    {passwordMessage}
                  </p>
                )}

                <Button
                  onClick={handleChangePassword}
                  disabled={
                    !currentPassword ||
                    !newPassword ||
                    !confirmPassword ||
                    changePassword.isPending
                  }
                >
                  <Lock className="mr-2 h-4 w-4" />
                  {changePassword.isPending ? 'Changing Password...' : 'Change Password'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AccountPage;
