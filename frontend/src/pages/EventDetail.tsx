import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useEventDetail, useOrgTicketTypes, useDeleteEvent, useCreateTicketType, useDeleteTicketType, useEventStats, useEventOrders } from "@/hooks/useOrgEvents";
import { useAuthStore } from "@/stores/auth";
import styles from "./EventDetail.module.css";

export default function EventDetail() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState<"overview" | "ticket-types" | "orders">("overview");

  if (!slug) {
    return <div className={styles.page}>Event not found.</div>;
  }

  return (
    <EventDetailInner
      slug={slug}
      tab={tab}
      onTabChange={setTab}
      navigate={navigate}
      user={user}
    />
  );
}

type InnerProps = {
  slug: string;
  tab: "overview" | "ticket-types" | "orders";
  onTabChange: (t: "overview" | "ticket-types" | "orders") => void;
  navigate: ReturnType<typeof useNavigate>;
  user: { role: string } | null;
};

function EventDetailInner({ slug, tab, onTabChange, navigate, user }: InnerProps) {
  const { data: eventDetail, isLoading, error } = useEventDetail(slug);

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.skeleton} style={{ height: 24, width: 120, marginBottom: 16 }} />
        <div className={styles.skeleton} style={{ height: 32, width: 300, marginBottom: 8 }} />
        <div className={styles.skeleton} style={{ height: 60, marginBottom: 8 }} />
        <div className={styles.skeleton} style={{ height: 60 }} />
      </div>
    );
  }

  if (error || !eventDetail) {
    return (
      <div className={styles.page}>
        <Link to="/events" className={styles.backLink}>&larr; Back to Events</Link>
        <p style={{ color: "var(--color-danger)" }}>Event not found.</p>
      </div>
    );
  }

  const event = eventDetail.data;
  const isOrgMember = user?.role === "admin" || user?.role === "operator";

  return (
    <div className={styles.page}>
      <Link to="/events" className={styles.backLink}>&larr; Back to Events</Link>

      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>
            {event.title}
            <span className={`${styles.badge} ${styles[event.status]}`}>
              {event.status}
            </span>
          </h1>
        </div>
        {isOrgMember && (
          <div className={styles.headerActions}>
            <Link
              to={`/events/${event.slug}/edit`}
              className={`${styles.btn} ${styles.btnSecondary}`}
            >
              Edit
            </Link>
            <DeleteEventButton eventId={event.id} navigate={navigate} />
          </div>
        )}
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === "overview" ? styles.active : ""}`}
          onClick={() => onTabChange("overview")}
        >
          Overview
        </button>
        <button
          className={`${styles.tab} ${tab === "ticket-types" ? styles.active : ""}`}
          onClick={() => onTabChange("ticket-types")}
        >
          Ticket Types
        </button>
        <button
          className={`${styles.tab} ${tab === "orders" ? styles.active : ""}`}
          onClick={() => onTabChange("orders")}
        >
          Orders
        </button>
      </div>

      {tab === "overview" && <OverviewTab event={event} />}
      {tab === "ticket-types" && <TicketTypesTab eventId={event.id} />}
      {tab === "orders" && <OrdersTab eventId={event.id} />}
    </div>
  );
}

function DeleteEventButton({ eventId, navigate }: { eventId: string; navigate: ReturnType<typeof useNavigate> }) {
  const deleteMutation = useDeleteEvent();

  const handleDelete = () => {
    if (!confirm("Are you sure you want to delete this event?")) return;
    deleteMutation.mutate(eventId, {
      onSuccess: () => navigate("/events"),
    });
  };

  return (
    <button
      className={`${styles.btn} ${styles.btnDanger}`}
      onClick={handleDelete}
      disabled={deleteMutation.isPending}
    >
      {deleteMutation.isPending ? "Deleting..." : "Delete"}
    </button>
  );
}

type OverviewProps = {
  event: {
    id: string;
    title: string;
    description: string | null;
    date: string;
    location: string | null;
    capacity: number;
    status: string;
    seating_type: string;
    slug: string;
    cover_image: string | null;
  };
};

function OverviewTab({ event }: OverviewProps) {
  const { data: stats } = useEventStats(event.id);

  return (
    <div>
      <div className={styles.overviewGrid}>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Date</span>
          <span className={styles.fieldValue}>
            {new Date(event.date).toLocaleDateString(undefined, {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Location</span>
          <span className={styles.fieldValue}>{event.location ?? "TBD"}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Capacity</span>
          <span className={styles.fieldValue}>{event.capacity}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Seating</span>
          <span className={styles.fieldValue}>{event.seating_type}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Slug</span>
          <span className={styles.fieldValue}>{event.slug}</span>
        </div>
      </div>

      {event.description && (
        <div className={styles.field} style={{ marginTop: 16 }}>
          <span className={styles.fieldLabel}>Description</span>
          <p className={styles.fieldValue} style={{ marginTop: 4 }}>{event.description}</p>
        </div>
      )}

      {stats && (
        <>
          <h3 style={{ marginTop: 24, marginBottom: 12, fontSize: "var(--text-lg)", fontWeight: 600 }}>Stats</h3>
          <div className={styles.statsGrid}>
            <StatCard label="Total Orders" value={String(stats.total_orders ?? 0)} />
            <StatCard label="Total Tickets" value={String(stats.total_tickets ?? 0)} />
            <StatCard label="Checked In" value={String(stats.checked_in ?? 0)} />
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.statCard}>
      <div className={styles.statValue}>{value}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  );
}

type TicketTypesTabProps = {
  eventId: string;
};

function TicketTypesTab({ eventId }: TicketTypesTabProps) {
  const { data, isLoading } = useOrgTicketTypes(eventId);
  const createTt = useCreateTicketType();
  const deleteTt = useDeleteTicketType();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState("");
  const [price, setPrice] = useState("0");
  const [maxPerOrder, setMaxPerOrder] = useState("5");

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !capacity) return;
    createTt.mutate(
      {
        eventId,
        data: {
          name,
          capacity: parseInt(capacity, 10),
          price: parseInt(price, 10),
          max_per_order: parseInt(maxPerOrder, 10),
        },
      },
      {
        onSuccess: () => {
          setName("");
          setCapacity("");
          setPrice("0");
          setMaxPerOrder("5");
          setShowForm(false);
        },
      },
    );
  };

  const ticketTypes = data?.data ?? [];

  return (
    <div>
      <div className={styles.ttHeader}>
        <h3 className={styles.ttTitle}>Ticket Types</h3>
        <button
          className={`${styles.btn} ${styles.btnPrimary} ${styles.btnSmall}`}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "+ Add"}
        </button>
      </div>

      {showForm && (
        <form className={styles.addTtForm} onSubmit={handleAdd}>
          <div className={`${styles.formGroup}`} style={{ flex: 2 }}>
            <label>Name</label>
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. General Admission"
              required
            />
          </div>
          <div className={`${styles.formGroup}`} style={{ flex: 1 }}>
            <label>Capacity</label>
            <input
              className={styles.input}
              type="number"
              min="1"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              placeholder="100"
              required
            />
          </div>
          <div className={`${styles.formGroup}`} style={{ flex: 1 }}>
            <label>Price (cents)</label>
            <input
              className={styles.input}
              type="number"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="0"
            />
          </div>
          <div className={`${styles.formGroup}`} style={{ flex: 1 }}>
            <label>Max/Order</label>
            <input
              className={styles.input}
              type="number"
              min="1"
              value={maxPerOrder}
              onChange={(e) => setMaxPerOrder(e.target.value)}
              placeholder="5"
            />
          </div>
          <button
            type="submit"
            className={`${styles.btn} ${styles.btnPrimary} ${styles.btnSmall}`}
            disabled={createTt.isPending}
            style={{ marginTop: 18 }}
          >
            {createTt.isPending ? "..." : "Add"}
          </button>
        </form>
      )}

      {isLoading ? (
        <p>Loading ticket types...</p>
      ) : ticketTypes.length > 0 ? (
        <table className={styles.ttTable}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Price</th>
              <th>Capacity</th>
              <th>Max/Order</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {ticketTypes.map((tt) => (
              <tr key={tt.id}>
                <td>{tt.name}</td>
                <td>{(tt.price / 100).toFixed(2)}</td>
                <td>{tt.capacity}</td>
                <td>{tt.max_per_order}</td>
                <td>
                  <button
                    className={`${styles.btn} ${styles.btnDanger} ${styles.btnSmall}`}
                    onClick={() => deleteTt.mutate({ eventId, ttId: tt.id })}
                    disabled={deleteTt.isPending}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: "var(--color-text-secondary)", fontSize: "var(--text-sm)" }}>
          No ticket types yet. Add one above.
        </p>
      )}
    </div>
  );
}

type OrdersTabProps = {
  eventId: string;
};

function OrdersTab({ eventId }: OrdersTabProps) {
  const { data, isLoading } = useEventOrders(eventId);

  if (isLoading) {
    return <p>Loading orders...</p>;
  }

  const orders = (data?.data ?? []) as Array<{
    id: string;
    status: string;
    created_at: string;
    email?: string;
  }>;

  if (orders.length === 0) {
    return (
      <p style={{ color: "var(--color-text-secondary)", fontSize: "var(--text-sm)" }}>
        No orders yet.
      </p>
    );
  }

  return (
    <table className={styles.orderTable}>
      <thead>
        <tr>
          <th>Order ID</th>
          <th>Email</th>
          <th>Status</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((order) => (
          <tr key={order.id}>
            <td style={{ fontFamily: "monospace", fontSize: "var(--text-xs)" }}>
              {order.id.slice(0, 8)}...
            </td>
            <td>{order.email ?? "—"}</td>
            <td>
              <span className={`${styles.orderBadge} ${styles[order.status] ?? ""}`}>
                {order.status}
              </span>
            </td>
            <td>{new Date(order.created_at).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
