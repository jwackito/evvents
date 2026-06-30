export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "operator" | "checkin_staff";
  organization_id: string | null;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  settings: Record<string, unknown>;
}

export interface Event {
  id: string;
  organization_id: string;
  title: string;
  description: string | null;
  date: string;
  location: string | null;
  capacity: number;
  status: "draft" | "published" | "cancelled" | "completed";
  seating_type: "general" | "assigned";
  slug: string;
  cover_image: string | null;
  ticket_types: TicketType[];
}

export interface TicketType {
  id: string;
  event_id: string;
  name: string;
  description: string | null;
  price: number;
  capacity: number;
  max_per_order: number;
}

export interface Order {
  id: string;
  event_id: string;
  status: "pending" | "confirmed" | "cancelled";
  created_at: string;
}

export interface Ticket {
  id: string;
  order_id: string;
  ticket_type_id: string;
  attendee_id: string;
  qr_hash: string;
  seat: string | null;
  checked_in: boolean;
  checked_in_at: string | null;
}

export interface Attendee {
  id: string;
  name: string;
  email: string;
  telegram_chat_id: number | null;
  telegram_linked: boolean;
}

export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}
