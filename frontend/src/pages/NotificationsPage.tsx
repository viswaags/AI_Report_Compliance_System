import { Bell, Check, CheckCheck } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  useLatestNotifications,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotificationStats,
  useNotifications,
  useUnreadNotificationCount,
} from '@/hooks/useNotifications';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

type BackendNotification = {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at?: string | null;
};

type NotificationStats = {
  total?: number;
  unread?: number;
  read?: number;
};

function formatDate(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function NotificationList({
  notifications,
  isLoading,
  onMarkRead,
  markingId,
}: {
  notifications: BackendNotification[];
  isLoading: boolean;
  onMarkRead: (id: number) => void;
  markingId?: number;
}) {
  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">Loading notifications...</div>;
  }

  if (notifications.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <CheckCheck className="mx-auto mb-4 h-12 w-12" />
        <p>No notifications available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={cn(
            'flex items-start gap-3 rounded-lg border border-border p-4 transition-colors',
            !notification.is_read && 'border-primary/30 bg-primary/5'
          )}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Bell className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className={cn('font-medium', !notification.is_read && 'text-primary')}>
                {notification.title}
              </p>
              <Badge variant="outline">{notification.notification_type}</Badge>
              <StatusBadge status={notification.is_read ? 'READ' : 'UNREAD'} />
            </div>
            <p className="text-sm text-muted-foreground">{notification.message}</p>
            {formatDate(notification.created_at) && (
              <p className="text-xs text-muted-foreground">{formatDate(notification.created_at)}</p>
            )}
          </div>
          {!notification.is_read && (
            <Button
              variant="ghost"
              size="sm"
              disabled={markingId === notification.id}
              onClick={() => onMarkRead(notification.id)}
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}

export function NotificationsPage() {
  const notificationsQuery = useNotifications();
  const latestNotificationsQuery = useLatestNotifications();
  const unreadCountQuery = useUnreadNotificationCount();
  const statsQuery = useNotificationStats();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const notifications = Array.isArray(notificationsQuery.data)
    ? (notificationsQuery.data as BackendNotification[])
    : [];
  const unreadNotifications = notifications.filter((notification) => !notification.is_read);
  const latestNotifications = Array.isArray(latestNotificationsQuery.data)
    ? (latestNotificationsQuery.data as BackendNotification[])
    : [];
  const stats = (statsQuery.data ?? {}) as NotificationStats;
  const unreadCount =
    typeof (unreadCountQuery.data as { unread_count?: unknown } | undefined)?.unread_count === 'number'
      ? ((unreadCountQuery.data as { unread_count: number }).unread_count)
      : unreadNotifications.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Notifications</h1>
          <p className="text-muted-foreground">Stay updated with system notifications and alerts</p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            onClick={() => markAllRead.mutate(undefined, {
              onSuccess: () => toast.success('All notifications marked as read.'),
              onError: () => toast.error('Unable to mark notifications as read.'),
            })}
            disabled={markAllRead.isPending}
          >
            <CheckCheck className="mr-2 h-4 w-4" />
            {markAllRead.isPending ? 'Marking...' : 'Mark All as Read'}
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Notifications</p>
                <p className="text-2xl font-bold">{stats.total ?? notifications.length}</p>
              </div>
              <Bell className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Unread</p>
                <p className="text-2xl font-bold text-primary">{stats.unread ?? unreadCount}</p>
              </div>
              <Badge variant="destructive" className="h-8">New</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Read</p>
                <p className="text-2xl font-bold text-muted-foreground">
                  {stats.read ?? notifications.length - unreadNotifications.length}
                </p>
              </div>
              <Check className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {notificationsQuery.isError ? (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Unable to load notifications.
        </p>
      ) : (
        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">
              All
              <Badge variant="secondary" className="ml-2">{notifications.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="latest">
              Latest
              <Badge variant="secondary" className="ml-2">{latestNotifications.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="unread">
              Unread
              {unreadCount > 0 && <Badge variant="destructive" className="ml-2">{unreadCount}</Badge>}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <Card>
              <CardHeader>
                <CardTitle>All Notifications</CardTitle>
                <CardDescription>Your notification history</CardDescription>
              </CardHeader>
              <CardContent>
                <NotificationList
                  notifications={notifications}
                  isLoading={notificationsQuery.isLoading}
                  onMarkRead={(id) => markRead.mutate(id, {
                    onSuccess: () => toast.success('Notification marked as read.'),
                    onError: () => toast.error('Unable to mark notification as read.'),
                  })}
                  markingId={markRead.variables}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="latest">
            <Card>
              <CardHeader>
                <CardTitle>Latest Notifications</CardTitle>
                <CardDescription>Most recent backend notifications</CardDescription>
              </CardHeader>
              <CardContent>
                <NotificationList
                  notifications={latestNotifications}
                  isLoading={latestNotificationsQuery.isLoading}
                  onMarkRead={(id) => markRead.mutate(id, {
                    onSuccess: () => toast.success('Notification marked as read.'),
                    onError: () => toast.error('Unable to mark notification as read.'),
                  })}
                  markingId={markRead.variables}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="unread">
            <Card>
              <CardHeader>
                <CardTitle>Unread Notifications</CardTitle>
                <CardDescription>Notifications you have not read yet</CardDescription>
              </CardHeader>
              <CardContent>
                <NotificationList
                  notifications={unreadNotifications}
                  isLoading={notificationsQuery.isLoading}
                  onMarkRead={(id) => markRead.mutate(id, {
                    onSuccess: () => toast.success('Notification marked as read.'),
                    onError: () => toast.error('Unable to mark notification as read.'),
                  })}
                  markingId={markRead.variables}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}

export default NotificationsPage;
