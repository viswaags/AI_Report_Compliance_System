import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import api from "@/lib/api";

export const eventKeys = {
  all: ["events"] as const,
  lists: () => [...eventKeys.all, "list"] as const,
  list: () => [...eventKeys.lists()] as const,
  myEvents: () => [...eventKeys.lists(), "my"] as const,
  byClub: (clubId: number) => [...eventKeys.lists(), "club", clubId] as const,
  categories: () => [...eventKeys.all, "categories"] as const,
  details: () => [...eventKeys.all, "detail"] as const,
  detail: (eventId: number) => [...eventKeys.details(), eventId] as const,
  stats: (eventId: number) => [...eventKeys.detail(eventId), "stats"] as const,
};

export function useEvents() {
  return useQuery({
    queryKey: eventKeys.list(),
    queryFn: () => api.getEvents(),
  });
}

export function useEvent(eventId: number | undefined) {
  return useQuery({
    queryKey: eventKeys.detail(eventId ?? 0),
    queryFn: () => api.getEvent(eventId as number),
    enabled: typeof eventId === "number",
  });
}

export function useMyEvents() {
  return useQuery({
    queryKey: eventKeys.myEvents(),
    queryFn: () => api.getMyEvents(),
  });
}

export function useEventsByClub(clubId: number | undefined) {
  return useQuery({
    queryKey: eventKeys.byClub(clubId ?? 0),
    queryFn: () => api.getEventsByClub(clubId as number),
    enabled: typeof clubId === "number",
  });
}

export function useEventCategories() {
  return useQuery({
    queryKey: eventKeys.categories(),
    queryFn: () => api.getEventCategories(),
  });
}

export function useEventStats(eventId: number | undefined) {
  return useQuery({
    queryKey: eventKeys.stats(eventId ?? 0),
    queryFn: () => api.getEventStats(eventId as number),
    enabled: typeof eventId === "number",
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      club_id: number;
      event_title: string;
      event_category?: string;
      event_date?: string;
    }) => api.createEvent(data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: eventKeys.all });
      void queryClient.invalidateQueries({
        queryKey: eventKeys.byClub(variables.club_id),
      });
    },
  });
}
