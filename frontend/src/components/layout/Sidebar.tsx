import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  CalendarDays,
  FileText,
  ClipboardCheck,
  FileStack,
  Archive,
  Bell,
  User,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types';

interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/app/dashboard',
    icon: LayoutDashboard,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Users & Memberships',
    href: '/app/users',
    icon: Users,
    roles: ['ADMIN', 'CLUB_COORDINATOR'],
  },
  {
    label: 'Clubs & Events',
    href: '/app/clubs',
    icon: Building2,
    roles: ['ADMIN'],
  },
  {
    label: 'Clubs & Members',
    href: '/app/clubs',
    icon: Building2,
    roles: ['CLUB_COORDINATOR'],
  },
  {
    label: 'My Clubs',
    href: '/app/clubs',
    icon: Building2,
    roles: ['FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Events',
    href: '/app/events',
    icon: CalendarDays,
    roles: ['CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Reports',
    href: '/app/reports',
    icon: FileText,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Reviews',
    href: '/app/reviews',
    icon: ClipboardCheck,
    roles: ['ADMIN', 'CLUB_COORDINATOR'],
  },
  {
    label: 'Reports & Reviews',
    href: '/app/reports',
    icon: FileText,
    roles: ['CLUB_COORDINATOR'],
  },
  {
    label: 'Templates',
    href: '/app/templates',
    icon: FileStack,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Repository',
    href: '/app/repository',
    icon: Archive,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Notifications',
    href: '/app/notifications',
    icon: Bell,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
  {
    label: 'Account',
    href: '/app/account',
    icon: User,
    roles: ['ADMIN', 'CLUB_COORDINATOR', 'FACULTY_REPRESENTATIVE', 'STUDENT_REPRESENTATIVE'],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { user } = useAuth();
  const location = useLocation();

  const filteredNavItems = navItems.filter(
    (item) => user && item.roles.includes(user.role)
  );

  const uniqueItems = filteredNavItems.filter(
    (item, index, self) => self.findIndex((i) => i.href === item.href) === index
  );

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col bg-card border-r border-border transition-all duration-200',
        collapsed ? 'w-[70px]' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <FileText className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">ClubComply</span>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <FileText className="h-5 w-5 text-primary-foreground" />
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {uniqueItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.href + item.label}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="w-full justify-center"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}

export default Sidebar;
