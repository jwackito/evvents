import { useMutation, useQuery } from "@tanstack/react-query";
import { get, post } from "@/services/api";
import type { Ticket } from "@/types";

export function useTicketByQr(qrHash: string | null) {
  return useQuery({
    queryKey: ["ticket", qrHash],
    queryFn: () => get<{ data: Ticket }>(`/api/v1/tickets/${qrHash}`),
    enabled: !!qrHash,
  });
}

export function useCheckIn() {
  return useMutation({
    mutationFn: (qrHash: string) =>
      post<{ data: Ticket }>(`/api/v1/tickets/${qrHash}/check-in`),
  });
}
