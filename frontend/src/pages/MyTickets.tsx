import { Link } from "react-router-dom";
import { useMyOrders } from "@/hooks/useOrder";
import styles from "./MyTickets.module.css";

export default function MyTickets() {
  const { data, isLoading, error } = useMyOrders();

  if (isLoading) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>My Tickets</h1>
        {[1, 2].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 80, marginBottom: 12 }} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>My Tickets</h1>
        <p style={{ color: "var(--color-danger)" }}>Failed to load your tickets.</p>
      </div>
    );
  }

  const orders = data?.data ?? [];

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>My Tickets</h1>

      {orders.length > 0 ? (
        orders.map((order) => (
          <Link
            key={order.order_id}
            to={`/orders/${order.order_id}`}
            className={styles.card}
          >
            <div className={styles.cardInfo}>
              <div className={styles.eventTitle}>{order.event_title}</div>
              <div className={styles.eventMeta}>
                <span>{new Date(order.event_date).toLocaleDateString()}</span>
                <span>{order.ticket_count} ticket{order.ticket_count !== 1 ? "s" : ""}</span>
              </div>
            </div>
            <span className={`${styles.badge} ${styles[order.status] ?? ""}`}>
              {order.status}
            </span>
          </Link>
        ))
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>&#127915;</div>
          <div className={styles.emptyTitle}>No tickets yet</div>
          <div className={styles.emptyText}>
            Purchase tickets to an event to see them here.
          </div>
          <Link to="/events" className={`${styles.btn} ${styles.btnPrimary}`}>
            Browse Events
          </Link>
        </div>
      )}
    </div>
  );
}
