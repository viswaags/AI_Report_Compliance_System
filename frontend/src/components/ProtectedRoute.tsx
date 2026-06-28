import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: UserRole[];
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading, hasRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  if (user?.must_change_password && location.pathname !== '/app/account') {
    return <Navigate to="/app/account?tab=security" replace />;
  }

  if (roles && !hasRole(roles)) {
    return <Navigate to="/app/dashboard" replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
