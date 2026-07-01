import { Link } from "react-router-dom";
import { useCheckinEvents } from "@/hooks/useCheckin";
import styles from "./CheckinEvents.module.css";

export default function CheckinEvents() {
  const { data, isLoading } = useCheckinEvents();

  if (isLoading) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>Check-In</h1>
        {[1, 2].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 72, marginBottom: 8 }} />
        ))}
      </div>
    );
  }

  const events = data?.data ?? [];

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Check-In</h1>
      {events.length > 0 ? (
        <div className={styles.list}>
          {events.map((event) => (
            <Link
              key={event.id}
              to={`/checkin/${event.id}`}
              className={styles.card}
            >
              <div className={styles.info}>
                <div className={styles.eventTitle}>{event.title}</div>
                <div className={styles.eventMeta}>
                  {new Date(event.date).toLocaleDateString()}
                </div>
              </div>
              <span style={{ color: "var(--color-primary)", fontSize: "var(--text-sm)" }}>
                Scan &rarr;
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>&#128269;</div>
          <div className={styles.emptyTitle}>No events for check-in</div>
        </div>
      )}
    </div>
  );
}
