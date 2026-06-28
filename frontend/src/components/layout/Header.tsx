import { Bell, LogOut, User, Menu } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback} from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface HeaderProps {
  sidebarCollapsed: boolean;
  onMenuClick?: () => void;
  unreadCount?: number;
}

export function Header({ sidebarCollapsed, onMenuClick, unreadCount = 0 }: HeaderProps) {
  const { user, logout } = useAuth();

  const getInitials = () => {
    if (!user) return 'U';
    return user.name.split(" ").map(part => part[0]).join("").substring(0, 2).toUpperCase();
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
    <header
      className={cn(
        'fixed top-0 right-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 transition-all duration-200',
        sidebarCollapsed ? 'left-[70px]' : 'left-64'
      )}
    >
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" className="md:hidden" onClick={onMenuClick}>
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <Link to="/app/notifications">
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -right-1 -top-1 h-5 min-w-5 rounded-full px-1 text-xs flex items-center justify-center"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </Badge>
            )}
          </Button>
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                  {getInitials()}
                </AvatarFallback>
              </Avatar>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-foreground">
                  {user?.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {user && getRoleLabel(user.role)}
                </p>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/app/account" className="flex items-center cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                Profile Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/app/notifications" className="flex items-center cursor-pointer">
                <Bell className="mr-2 h-4 w-4" />
                Notifications
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={logout}
              className="text-red-600 focus:text-red-600 cursor-pointer"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export default Header;
