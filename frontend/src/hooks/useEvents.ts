import { useQuery } from "@tanstack/react-query";
import { get } from "@/services/api";
import type { Event, PaginatedResponse } from "@/types";

export function useEvents(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["events", page, perPage],
    queryFn: () =>
      get<PaginatedResponse<Event>>(
        `/api/v1/events?page=${page}&per_page=${perPage}`,
      ),
  });
}

export function useEvent(slug: string) {
  return useQuery({
    queryKey: ["event", slug],
    queryFn: () => get<{ data: Event }>(`/api/v1/events/${slug}`),
    enabled: !!slug,
  });
}
