import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { get, post, put, del } from "@/services/api";
import { useToast } from "@/stores/toast";
import type { Event, TicketType, PaginatedResponse } from "@/types";

export function useOrgEvents(page = 1, perPage = 20, status?: string) {
  const token = useAuthStore((s) => s.token);
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  if (status) params.set("status", status);
  return useQuery({
    queryKey: ["org-events", page, perPage, status],
    queryFn: () => get<PaginatedResponse<Event>>(`/api/v1/org/events?${params}`),
    enabled: !!token,
  });
}

export function useEventDetail(id: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["org-event", id],
    queryFn: () => get<{ data: Event }>(`/api/v1/events/${id}`),
    enabled: !!token && !!id,
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      post<{ data: Event }>("/api/v1/org/events", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-events"] });
      toast.success("Event created successfully");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useUpdateEvent() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      put<{ data: Event }>(`/api/v1/org/events/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-events"] });
      toast.success("Event updated");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useDeleteEvent() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (id: string) => del(`/api/v1/org/events/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["org-events"] });
      toast.success("Event deleted");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useOrgTicketTypes(eventId: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["org-ticket-types", eventId],
    queryFn: () => get<{ data: TicketType[] }>(`/api/v1/org/events/${eventId}/ticket-types`),
    enabled: !!token && !!eventId,
  });
}

export function useCreateTicketType() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ eventId, data }: { eventId: string; data: Record<string, unknown> }) =>
      post<{ data: TicketType }>(`/api/v1/org/events/${eventId}/ticket-types`, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["org-ticket-types", variables.eventId] });
      toast.success("Ticket type added");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useDeleteTicketType() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ eventId, ttId }: { eventId: string; ttId: string }) =>
      del(`/api/v1/org/events/${eventId}/ticket-types/${ttId}`),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["org-ticket-types", variables.eventId] });
      toast.success("Ticket type removed");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useEventStats(eventId: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["org-event-stats", eventId],
    queryFn: () => get<Record<string, unknown>>(`/api/v1/org/events/${eventId}/stats`),
    enabled: !!token && !!eventId,
  });
}

export function useEventOrders(eventId: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["org-event-orders", eventId],
    queryFn: () => get<{ data: unknown[] }>(`/api/v1/org/events/${eventId}/orders`),
    enabled: !!token && !!eventId,
  });
}
