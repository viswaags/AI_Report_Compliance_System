import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const clubKeys = {
  all: ["clubs"] as const,
  lists: () => [...clubKeys.all, "list"] as const,
  list: () => [...clubKeys.lists()] as const,
  myClubs: () => [...clubKeys.lists(), "my"] as const,
  memberships: () => [...clubKeys.all, "memberships"] as const,
  myMemberships: () => [...clubKeys.memberships(), "my"] as const,
  details: () => [...clubKeys.all, "detail"] as const,
  detail: (clubId: number) => [...clubKeys.details(), clubId] as const,
  members: (clubId: number) => [...clubKeys.detail(clubId), "members"] as const,
  events: (clubId: number) => [...clubKeys.detail(clubId), "events"] as const,
  stats: (clubId: number) => [...clubKeys.detail(clubId), "stats"] as const,
};

export function useClubs(enabled = true) {
  return useQuery({
    queryKey: clubKeys.list(),
    queryFn: () => api.getClubs(),
    enabled,
  });
}

export function useClub(clubId: number | undefined) {
  return useQuery({
    queryKey: clubKeys.detail(clubId ?? 0),
    queryFn: () => api.getClub(clubId as number),
    enabled: typeof clubId === "number",
  });
}

export function useMyClubs(enabled = true) {
  return useQuery({
    queryKey: clubKeys.myClubs(),
    queryFn: () => api.getMyClubs(),
    enabled,
  });
}

export function useMemberships(enabled = true) {
  return useQuery({
    queryKey: clubKeys.memberships(),
    queryFn: () => api.getMemberships(),
    enabled,
  });
}

export function useMyMemberships(enabled = true) {
  return useQuery({
    queryKey: clubKeys.myMemberships(),
    queryFn: () => api.getMyMemberships(),
    enabled,
  });
}

export function useClubMembers(clubId: number | undefined) {
  return useQuery({
    queryKey: clubKeys.members(clubId ?? 0),
    queryFn: () => api.getClubMembers(clubId as number),
    enabled: typeof clubId === "number",
  });
}

export function useClubEvents(clubId: number | undefined) {
  return useQuery({
    queryKey: clubKeys.events(clubId ?? 0),
    queryFn: () => api.getClubEvents(clubId as number),
    enabled: typeof clubId === "number",
  });
}

export function useClubStats(clubId: number | undefined) {
  return useQuery({
    queryKey: clubKeys.stats(clubId ?? 0),
    queryFn: () => api.getClubStats(clubId as number),
    enabled: typeof clubId === "number",
  });
}

export function useCreateClub() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { club_name: string; description?: string }) =>
      api.createClub(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: clubKeys.all });
    },
  });
}

export function useAssignMembership() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { user_id: number; club_id: number; role: string }) =>
      api.createMembership(data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: clubKeys.memberships() });
      void queryClient.invalidateQueries({ queryKey: clubKeys.members(variables.club_id) });
      void queryClient.invalidateQueries({ queryKey: clubKeys.myClubs() });
    },
  });
}

export function useBulkAssignMembership() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { user_id: number; club_ids: number[]; role: string }) =>
      api.bulkAssignMembership(data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: clubKeys.memberships() });
      void queryClient.invalidateQueries({ queryKey: clubKeys.myClubs() });
      variables.club_ids.forEach((clubId) => {
        void queryClient.invalidateQueries({ queryKey: clubKeys.members(clubId) });
      });
    },
  });
}
