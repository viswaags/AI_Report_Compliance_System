import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User, UserRole } from '../types';
import { useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

function mapBackendUser(user: any): User {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role as UserRole,
    is_active: user.is_active,
    must_change_password: user.must_change_password,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  useEffect(() => {

    const handleAuthExpired = () => {
      api.clearToken();
      localStorage.removeItem("user");
      setUser(null);
      queryClient.clear();
      navigate("/auth/login", { replace: true });
    };

    window.addEventListener(
      "auth:expired",
      handleAuthExpired
    );

    const initializeAuth = async () => {

      try {

        const token = localStorage.getItem("token");

        if (!token) {
          setIsLoading(false);
          return;
        }

        const backendUser = await api.getCurrentUser();

        const frontendUser = mapBackendUser(
          backendUser
        );

        setUser(frontendUser);

        localStorage.setItem(
          "user",
          JSON.stringify(frontendUser)
        );

      } catch {

        localStorage.removeItem("token");
        localStorage.removeItem("user");

        setUser(null);

      } finally {

        setIsLoading(false);

      }
    };

    initializeAuth();

    return () => {
      window.removeEventListener(
        "auth:expired",
        handleAuthExpired
      );
    };

  }, [navigate, queryClient]);

  const login = useCallback(

    async (
      email: string,
      password: string
    ) => {

      setIsLoading(true);

      try {

        await api.login(
          email,
          password
        );

        const backendUser =
          await api.getCurrentUser();

        const frontendUser =
          mapBackendUser(
            backendUser
          );

        localStorage.setItem(
          "user",
          JSON.stringify(
            frontendUser
          )
        );

        setUser(
          frontendUser
        );

        const from = frontendUser.must_change_password
          ? '/app/account?tab=security'
          : location.state?.from?.pathname ||
            getDefaultRoute(
              frontendUser.role
            );

        navigate(
          from,
          { replace: true }
        );

      } finally {

        setIsLoading(false);

      }
    },

    [
      navigate,
      location
    ]

  );

  const logout = useCallback(() => {
    api.clearToken();
    localStorage.removeItem('user');
    setUser(null);
    queryClient.clear();
    navigate('/auth/login');
  }, [navigate, queryClient]);

  const hasRole = useCallback(
    (roles: UserRole | UserRole[]) => {
      if (!user) return false;
      const roleArray = Array.isArray(roles) ? roles : [roles];
      return roleArray.includes(user.role);
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

function getDefaultRoute(role: UserRole): string {
  switch (role) {
    case 'ADMIN':
      return '/app/dashboard';
    case 'CLUB_COORDINATOR':
      return '/app/dashboard';
    case 'FACULTY_REPRESENTATIVE':
      return '/app/dashboard';
    case 'STUDENT_REPRESENTATIVE':
      return '/app/dashboard';
    default:
      return '/app/dashboard';
  }
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
