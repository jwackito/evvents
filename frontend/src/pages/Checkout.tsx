import { useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate, Link } from "react-router-dom";
import { useEventDetail } from "@/hooks/useOrgEvents";
import { useCreateOrder } from "@/hooks/useOrder";
import { useAuthStore } from "@/stores/auth";
import type { TicketType } from "@/types";
import styles from "./Checkout.module.css";

export default function Checkout() {
  const { slug } = useParams<{ slug: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { data: eventDetail, isLoading, error } = useEventDetail(slug ?? "");
  const createOrder = useCreateOrder();

  const [selectedTtId, setSelectedTtId] = useState(searchParams.get("ticket_type_id") ?? "");
  const [quantity, setQuantity] = useState(1);
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (eventDetail?.data.ticket_types?.length && !selectedTtId) {
      setSelectedTtId(eventDetail.data.ticket_types[0].id);
    }
  }, [eventDetail, selectedTtId]);

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.skeleton} style={{ height: 24, width: 120, marginBottom: 16 }} />
        <div className={styles.skeleton} style={{ height: 24, width: 200, marginBottom: 24 }} />
        {[1, 2].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 60, marginBottom: 12 }} />
        ))}
      </div>
    );
  }

  if (error || !eventDetail?.data) {
    return (
      <div className={styles.page}>
        <Link to="/events" className={styles.backLink}>&larr; Back to Events</Link>
        <p style={{ color: "var(--color-danger)" }}>Event not found.</p>
      </div>
    );
  }

  const event = eventDetail.data;
  const selectedTt = event.ticket_types.find((t: TicketType) => t.id === selectedTtId);
  const total = (selectedTt?.price ?? 0) * quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!selectedTtId) { setFormError("Select a ticket type"); return; }
    if (!name.trim()) { setFormError("Name is required"); return; }

    createOrder.mutate(
      {
        slug: slug!,
        data: {
          ticket_type_id: selectedTtId,
          quantity,
          attendee_name: name.trim(),
          attendee_email: email.trim() || null,
        },
      },
      {
        onSuccess: (res) => {
          navigate(`/orders/${res.data.order_id}`);
        },
        onError: (err) => {
          setFormError(err.message);
        },
      },
    );
  };

  return (
    <div className={styles.page}>
      <Link to={`/events/${slug}`} className={styles.backLink}>
        &larr; Back to Event
      </Link>

      <div className={styles.eventTitle}>
        {event.title}
      </div>

      {formError && <div className={styles.errorBanner}>{formError}</div>}

      <form onSubmit={handleSubmit}>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Select Ticket Type</div>
          <div className={styles.radioGroup}>
            {event.ticket_types.map((tt: TicketType) => (
              <label
                key={tt.id}
                className={`${styles.radio} ${selectedTtId === tt.id ? styles.radioSelected : ""}`}
              >
                <input
                  type="radio"
                  name="ticketType"
                  className={styles.radioInput}
                  value={tt.id}
                  checked={selectedTtId === tt.id}
                  onChange={() => setSelectedTtId(tt.id)}
                />
                <div className={styles.radioInfo}>
                  <div className={styles.radioName}>{tt.name}</div>
                  <div className={styles.radioMeta}>
                    {tt.description ?? `${tt.capacity} available`}
                  </div>
                </div>
                <div className={styles.radioPrice}>
                  ${(tt.price / 100).toFixed(2)}
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>Quantity</div>
          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>Tickets</label>
              <input
                className={styles.input}
                type="number"
                min={1}
                max={selectedTt?.max_per_order ?? 10}
                value={quantity}
                onChange={(e) => setQuantity(Math.min(
                  parseInt(e.target.value) || 1,
                  selectedTt?.max_per_order ?? 10,
                ))}
              />
            </div>
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>Your Details</div>
          <div className={styles.field}>
            <label className={styles.label}>Name *</label>
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your full name"
              required
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Email</label>
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="For ticket delivery"
            />
          </div>
        </div>

        <div className={styles.summary}>
          <div className={styles.summaryRow}>
            <span>{selectedTt?.name ?? "Ticket"} x{quantity}</span>
            <span>${(total / 100).toFixed(2)}</span>
          </div>
          <div className={`${styles.summaryRow} ${styles.summaryTotal}`}>
            <span>Total</span>
            <span>${(total / 100).toFixed(2)}</span>
          </div>
        </div>

        <div className={styles.actions}>
          <button
            type="submit"
            className={`${styles.btn} ${styles.btnPrimary}`}
            disabled={createOrder.isPending}
          >
            {createOrder.isPending ? "Placing Order..." : "Place Order"}
          </button>
          <Link to={`/events/${slug}`} className={`${styles.btn} ${styles.btnSecondary}`}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
