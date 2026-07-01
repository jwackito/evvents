import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { get, post } from "@/services/api";
import { useToast } from "@/stores/toast";

type CheckinEvent = {
  id: string;
  title: string;
  slug: string;
  date: string;
};

type ScanResult = {
  ticket_id: string;
  attendee_name: string;
  ticket_type: string;
  checked_in: boolean;
  checked_in_at: string | null;
};

type CheckinHistoryItem = {
  id: string;
  attendee_name: string;
  ticket_type: string;
  checked_in_at: string;
};

type SearchResult = {
  id: string;
  attendee_name: string;
  ticket_type: string;
  qr_hash: string;
  checked_in: boolean;
};

export function useCheckinEvents() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["checkin-events"],
    queryFn: () => get<{ data: CheckinEvent[] }>("/api/v1/check-in/events"),
    enabled: !!token,
  });
}

export function useScanTicket() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (qrHash: string) =>
      post<{ data: ScanResult }>("/api/v1/check-in/scan", { qr_hash: qrHash }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["checkin-history"] });
      queryClient.invalidateQueries({ queryKey: ["checkin-stats"] });
      toast.success(`Checked in: ${res.data.attendee_name}`);
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useUndoCheckin() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (qrHash: string) =>
      post<{ data: ScanResult }>("/api/v1/check-in/undo", { qr_hash: qrHash }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["checkin-history"] });
      queryClient.invalidateQueries({ queryKey: ["checkin-stats"] });
      toast.success(`Undid check-in for: ${res.data.attendee_name}`);
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useCheckinHistory(eventId: string, page = 1) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["checkin-history", eventId, page],
    queryFn: () =>
      get<{ data: CheckinHistoryItem[]; total: number }>(
        `/api/v1/check-in/events/${eventId}/history?page=${page}&per_page=20`,
      ),
    enabled: !!token && !!eventId,
  });
}

export function useCheckinSearch(eventId: string, query: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["checkin-search", eventId, query],
    queryFn: () =>
      get<{ data: SearchResult[] }>(
        `/api/v1/check-in/events/${eventId}/search?q=${encodeURIComponent(query)}`,
      ),
    enabled: !!token && !!eventId && query.length > 0,
  });
}

export function useCheckinStats(eventId: string) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["checkin-stats", eventId],
    queryFn: () =>
      get<Record<string, unknown>>(`/api/v1/check-in/events/${eventId}/stats`),
    enabled: !!token && !!eventId,
  });
}
