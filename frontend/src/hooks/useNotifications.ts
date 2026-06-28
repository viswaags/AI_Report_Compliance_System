import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const notificationKeys = {
  all: ["notifications"] as const,
  lists: () => [...notificationKeys.all, "list"] as const,
  list: () => [...notificationKeys.lists()] as const,
  latest: () => [...notificationKeys.lists(), "latest"] as const,
  unreadCount: () => [...notificationKeys.all, "unread-count"] as const,
  stats: () => [...notificationKeys.all, "stats"] as const,
};

export function useNotifications() {
  return useQuery({
    queryKey: notificationKeys.list(),
    queryFn: () => api.getNotifications(),
  });
}

export function useLatestNotifications() {
  return useQuery({
    queryKey: notificationKeys.latest(),
    queryFn: () => api.getLatestNotifications(),
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: () => api.getUnreadNotificationCount(),
  });
}

export function useNotificationStats() {
  return useQuery({
    queryKey: notificationKeys.stats(),
    queryFn: () => api.getNotificationStats(),
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: number) => api.markNotificationRead(notificationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
