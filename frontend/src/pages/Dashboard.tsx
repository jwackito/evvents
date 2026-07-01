import { Link } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";
import { useDashboard } from "@/hooks/useDashboard";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { me, events, totalEvents, upcomingEvents, isLoading, error } =
    useDashboard();

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <div className={`${styles.skeleton}`} style={{ width: 200, height: 24, marginBottom: 8 }} />
          <div className={`${styles.skeleton}`} style={{ width: 140, height: 16 }} />
        </div>
        <div className={styles.statsGrid}>
          <div className={`${styles.skeleton} ${styles.skeletonCard}`} />
          <div className={`${styles.skeleton} ${styles.skeletonCard}`} />
        </div>
        <div className={styles.section}>
          <div className={`${styles.skeleton}`} style={{ width: 120, height: 20, marginBottom: 16 }} />
          <div className={`${styles.skeleton} ${styles.skeletonRow}`} style={{ marginBottom: 8 }} />
          <div className={`${styles.skeleton} ${styles.skeletonRow}`} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorState}>
          <p>Failed to load dashboard. Please try again.</p>
        </div>
      </div>
    );
  }

  const role = user?.role;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.greeting}>
          Welcome, {me?.name ?? "User"}
        </h1>
        <p className={styles.subtitle}>
          Here's what's happening with your events.
        </p>
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.card}>
          <div className={`${styles.cardIcon} ${styles.events}`}>
            &#9733;
          </div>
          <div className={styles.cardValue}>{totalEvents}</div>
          <div className={styles.cardLabel}>Total Events</div>
        </div>
        <div className={styles.card}>
          <div className={`${styles.cardIcon} ${styles.upcoming}`}>
            &#9654;
          </div>
          <div className={styles.cardValue}>{upcomingEvents}</div>
          <div className={styles.cardLabel}>Upcoming</div>
        </div>
      </div>

      <div className={styles.actions}>
        <Link to="/events" className={`${styles.btn} ${styles.btnPrimary}`}>
          + Create Event
        </Link>
        <Link to="/events" className={`${styles.btn} ${styles.btnSecondary}`}>
          View Events
        </Link>
        {(role === "admin" || role === "operator" || role === "checkin_staff") && (
          <Link to="/checkin" className={`${styles.btn} ${styles.btnSecondary}`}>
            Check In
          </Link>
        )}
      </div>

      <div className={styles.section} style={{ marginTop: 32 }}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Recent Events</h2>
          <Link to="/events" className={styles.seeAll}>
            See all &rarr;
          </Link>
        </div>

        {events.length > 0 ? (
          <div className={styles.eventList}>
            {events.map((event) => (
              <div key={event.id} className={styles.eventRow}>
                <div className={styles.eventInfo}>
                  <div className={styles.eventTitle}>{event.title}</div>
                  <div className={styles.eventMeta}>
                    <span>{new Date(event.date).toLocaleDateString()}</span>
                    <span>{event.location ?? "TBD"}</span>
                    <span className={`${styles.badge} ${styles[event.status]}`}>
                      {event.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>&#128197;</div>
            <div className={styles.emptyTitle}>No events yet</div>
            <div className={styles.emptyText}>
              Create your first event to get started.
            </div>
            <Link to="/events" className={`${styles.btn} ${styles.btnPrimary}`}>
              Create Event
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
