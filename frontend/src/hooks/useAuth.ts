import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const authKeys = {
  all: ["auth"] as const,
  currentUser: () => [...authKeys.all, "current-user"] as const,
};

export function useCurrentUser() {
  return useQuery({
    queryKey: authKeys.currentUser(),
    queryFn: () => api.getCurrentUser(),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { email: string; password: string }) =>
      api.login(variables.email, variables.password),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.all });
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => api.forgotPassword(email),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (variables: { token: string; newPassword: string }) =>
      api.resetPassword(variables.token, variables.newPassword),
  });
}

export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { oldPassword: string; newPassword: string }) =>
      api.changePassword(variables.oldPassword, variables.newPassword),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.currentUser() });
    },
  });
}

export function useAdminResetPassword() {
  return useMutation({
    mutationFn: (variables: { userId: number; newPassword: string }) =>
      api.adminResetPassword(variables.userId, variables.newPassword),
  });
}
