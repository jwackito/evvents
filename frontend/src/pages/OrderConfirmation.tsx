import { useParams, Link } from "react-router-dom";
import { useOrder } from "@/hooks/useOrder";
import styles from "./OrderConfirmation.module.css";

export default function OrderConfirmation() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, error } = useOrder(id ?? "");

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.skeleton} style={{ height: 64, width: 64, borderRadius: "50%", margin: "0 auto 16px" }} />
        <div className={styles.skeleton} style={{ height: 24, width: 200, margin: "0 auto 24px" }} />
        {[1, 2, 3].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 80, marginBottom: 12 }} />
        ))}
      </div>
    );
  }

  if (error || !data?.data) {
    return (
      <div className={styles.page}>
        <p style={{ color: "var(--color-danger)" }}>Order not found.</p>
        <Link to="/tickets" className={styles.btn} style={{ marginTop: 16, display: "inline-block" }}>
          My Tickets
        </Link>
      </div>
    );
  }

  const { order_id, status, attendee, tickets, event_title, event_date } = data.data;

  return (
    <div className={styles.page}>
      <div className={styles.successIcon}>&#10003;</div>
      <h1 className={styles.title}>Order Confirmed!</h1>
      <p className={styles.subtitle}>Your tickets are ready. Show the QR code at the door.</p>

      <div className={styles.orderMeta}>
        <div className={styles.orderMetaField}>
          <span className={styles.orderMetaLabel}>Order</span>
          <span className={styles.orderMetaValue} style={{ fontFamily: "monospace", fontSize: "var(--text-xs)" }}>
            {order_id.slice(0, 8)}...
          </span>
        </div>
        <div className={styles.orderMetaField}>
          <span className={styles.orderMetaLabel}>Event</span>
          <span className={styles.orderMetaValue}>{event_title}</span>
        </div>
        <div className={styles.orderMetaField}>
          <span className={styles.orderMetaLabel}>Date</span>
          <span className={styles.orderMetaValue}>
            {event_date ? new Date(event_date).toLocaleDateString() : "—"}
          </span>
        </div>
        <div className={styles.orderMetaField}>
          <span className={styles.orderMetaLabel}>Status</span>
          <span className={styles.orderMetaValue}>{status}</span>
        </div>
      </div>

      <h3 style={{ fontSize: "var(--text-sm)", fontWeight: 600, marginBottom: 12 }}>
        Tickets ({tickets.length})
      </h3>

      {tickets.map((ticket) => (
        <div key={ticket.id} className={styles.ticketCard}>
          <div className={styles.qrCode}>
            {ticket.qr_hash.slice(0, 32)}
          </div>
          <div className={styles.ticketInfo}>
            <div className={styles.ticketType}>{ticket.ticket_type}</div>
            <div className={styles.ticketStatus}>
              {ticket.checked_in ? "Checked in" : "Not checked in"}
            </div>
          </div>
        </div>
      ))}

      {attendee && (
        <div style={{ marginTop: 16, textAlign: "center" }}>
          <span style={{ fontSize: "var(--text-xs)", color: "var(--color-text-secondary)" }}>
            Link code for Telegram:
          </span>{" "}
          <span className={styles.linkCode}>{attendee.link_code}</span>
        </div>
      )}

      <div className={styles.actions}>
        <Link to="/tickets" className={`${styles.btn} ${styles.btnPrimary}`}>
          My Tickets
        </Link>
        <Link to="/events" className={`${styles.btn} ${styles.btnSecondary}`}>
          Browse Events
        </Link>
      </div>
    </div>
  );
}
