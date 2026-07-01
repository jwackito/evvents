import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { get, post } from "@/services/api";
import { useToast } from "@/stores/toast";

type OrderResponse = {
  data: {
    order_id: string;
    event_id?: string;
    event_title?: string;
    event_slug?: string;
    event_date?: string;
    status: string;
    created_at?: string;
    attendee: {
      id: string;
      name: string;
      email: string | null;
      link_code: string;
    } | null;
    tickets: Array<{
      id: string;
      qr_hash: string;
      ticket_type: string;
      checked_in?: boolean;
      seat?: string | null;
    }>;
  };
};

type OrderListItem = {
  order_id: string;
  event_id: string;
  event_title: string;
  event_slug: string;
  event_date: string;
  status: string;
  ticket_count: number;
  created_at: string;
};

type MyOrdersResponse = {
  data: OrderListItem[];
};

export function useCreateOrder() {
  const toast = useToast();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      slug,
      data,
    }: {
      slug: string;
      data: {
        ticket_type_id: string;
        quantity: number;
        attendee_name: string;
        attendee_email?: string | null;
      };
    }) => post<OrderResponse>(`/api/v1/events/${slug}/order`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-orders"] });
      toast.success("Order placed successfully!");
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: ["order", id],
    queryFn: () => get<OrderResponse>(`/api/v1/orders/${id}`),
    enabled: !!id,
  });
}

export function useMyOrders() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["my-orders"],
    queryFn: () => get<MyOrdersResponse>("/api/v1/me/orders"),
    enabled: !!token,
  });
}
