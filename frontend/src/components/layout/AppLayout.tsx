import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';
import { useUnreadNotificationCount } from '@/hooks/useNotifications';

type UnreadCountResponse = {
  unread_count?: number;
  count?: number;
};

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const unreadCountQuery = useUnreadNotificationCount();
  const unreadCountData = unreadCountQuery.data as UnreadCountResponse | number | undefined;
  const unreadCount = typeof unreadCountData === 'number'
    ? unreadCountData
    : unreadCountData?.unread_count ?? unreadCountData?.count ?? 0;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <Header sidebarCollapsed={sidebarCollapsed} unreadCount={unreadCount} />
      <main
        className={cn(
          'pt-16 min-h-screen transition-all duration-200',
          sidebarCollapsed ? 'pl-[70px]' : 'pl-64'
        )}
      >
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default AppLayout;
