import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/auth/LoginPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { UsersPage } from '@/pages/UsersPage';
import { ClubsPage } from '@/pages/ClubsPage';
import { EventsPage } from '@/pages/EventsPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { ReviewsPage } from '@/pages/ReviewsPage';
import { TemplatesPage } from '@/pages/TemplatesPage';
import { RepositoryPage } from '@/pages/RepositoryPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { AccountPage } from '@/pages/AccountPage';
import { Toaster } from '@/components/ui/sonner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/app/dashboard" replace />} />

            <Route path="/auth">
              <Route path="login" element={<LoginPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
              <Route path="reset-password" element={<ResetPasswordPage />} />
            </Route>

            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route
                path="users"
                element={
                  <ProtectedRoute roles={['ADMIN', 'CLUB_COORDINATOR']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />
              <Route path="clubs" element={<ClubsPage />} />
              <Route path="events" element={<EventsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route
                path="reviews"
                element={
                  <ProtectedRoute roles={['ADMIN', 'CLUB_COORDINATOR']}>
                    <ReviewsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="templates" element={<TemplatesPage />} />
              <Route path="repository" element={<RepositoryPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="account" element={<AccountPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
          </Routes>
          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
