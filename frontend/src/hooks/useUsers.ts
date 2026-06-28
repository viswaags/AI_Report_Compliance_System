import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const userKeys = {
  all: ["users"] as const,

  lists: () => [...userKeys.all, "list"] as const,

  list: () => [...userKeys.lists()] as const,

  membershipList: () =>
    [...userKeys.lists(), "membership"] as const,

  details: () => [...userKeys.all, "detail"] as const,

  detail: (userId: number) =>
    [...userKeys.details(), userId] as const,

  byRole: (role: string) =>
    [...userKeys.lists(), "role", role] as const,
};

export function useUsers(enabled = true) {
  return useQuery({
    queryKey: userKeys.list(),
    queryFn: () => api.getUsers(),
    enabled,
  });
}

export function useUsersForMembership(enabled = true) {
  return useQuery({
    queryKey: userKeys.membershipList(),
    queryFn: () => api.getUsersForMembership(),
    enabled,
  });
}

export function useUser(userId: number | undefined) {
  return useQuery({
    queryKey: userKeys.detail(userId ?? 0),
    queryFn: () => api.getUser(userId as number),
    enabled: typeof userId === "number",
  });
}

export function useUsersByRole(role: string | undefined) {
  return useQuery({
    queryKey: userKeys.byRole(role ?? ""),
    queryFn: () => api.getUsersByRole(role as string),
    enabled: Boolean(role),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      email: string;
      password: string;
      role: string;
    }) => api.createUser(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: number) => api.activateUser(userId),
    onSuccess: (_, userId) => {
      void queryClient.invalidateQueries({ queryKey: userKeys.all });
      void queryClient.invalidateQueries({ queryKey: userKeys.detail(userId) });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: number) => api.deactivateUser(userId),
    onSuccess: (_, userId) => {
      void queryClient.invalidateQueries({ queryKey: userKeys.all });
      void queryClient.invalidateQueries({ queryKey: userKeys.detail(userId) });
    },
  });
}
