import { useQueries } from "@tanstack/react-query";
import { get } from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import type { Event, PaginatedResponse, User } from "@/types";

export function useDashboard() {
  const token = useAuthStore((s) => s.token);

  const results = useQueries({
    queries: [
      {
        queryKey: ["me"],
        queryFn: () =>
          get<{ data: User }>("/api/v1/auth/me").then((r) => r.data),
        enabled: !!token,
      },
      {
        queryKey: ["events", 1, 5],
        queryFn: () =>
          get<PaginatedResponse<Event>>("/api/v1/events?page=1&per_page=5"),
        enabled: !!token,
      },
    ],
  });

  const [meQuery, eventsQuery] = results;
  const isLoading = meQuery.isLoading || eventsQuery.isLoading;
  const error = meQuery.error ?? eventsQuery.error;

  const me = meQuery.data ?? null;
  const events = eventsQuery.data?.data ?? [];
  const totalEvents = eventsQuery.data?.total ?? 0;
  const upcomingEvents = events.filter(
    (e) => new Date(e.date) > new Date(),
  ).length;

  return {
    me,
    events,
    totalEvents,
    upcomingEvents,
    isLoading,
    error,
  };
}
