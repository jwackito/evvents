import { useState } from "react";
import { Link } from "react-router-dom";
import { useOrgEvents } from "@/hooks/useOrgEvents";
import { useAuthStore } from "@/stores/auth";
import styles from "./Events.module.css";

const STATUSES = ["", "published", "draft", "completed", "cancelled"] as const;

export default function Events() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>("");
  const user = useAuthStore((s) => s.user);
  const { data, isLoading, error } = useOrgEvents(page, 20, status || undefined);

  const canCreate = user?.role === "admin" || user?.role === "operator";

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>Events</h1>
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={styles.skeleton}
            style={{ height: 60, marginBottom: 8, borderRadius: "var(--radius-md)" }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <p style={{ color: "var(--color-danger)" }}>Failed to load events.</p>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / 20));

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Events</h1>
        {canCreate && (
          <Link to="/events/new" className={`${styles.btn} ${styles.btnPrimary}`}>
            + Create Event
          </Link>
        )}
      </div>

      <div className={styles.filters}>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={`${styles.filterBtn} ${status === s ? styles.active : ""}`}
            onClick={() => { setStatus(s); setPage(1); }}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {data && data.data.length > 0 ? (
        <>
          <div className={styles.list}>
            {data.data.map((event) => (
              <Link
                key={event.id}
                to={`/events/${event.slug}`}
                className={styles.row}
              >
                <div className={styles.info}>
                  <div className={styles.eventTitle}>{event.title}</div>
                  <div className={styles.meta}>
                    <span>{new Date(event.date).toLocaleDateString()}</span>
                    <span>{event.location ?? "TBD"}</span>
                    <span className={`${styles.badge} ${styles[event.status]}`}>
                      {event.status}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className={styles.pageBtn}
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                &larr; Prev
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`${styles.pageBtn} ${p === page ? styles.active : ""}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button
                className={styles.pageBtn}
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next &rarr;
              </button>
            </div>
          )}
        </>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>&#128197;</div>
          <div className={styles.emptyTitle}>No events found</div>
          <div className={styles.emptyText}>
            {status
              ? `No ${status} events. Try a different filter.`
              : "Create your first event to get started."}
          </div>
          {canCreate && (
            <Link to="/events/new" className={`${styles.btn} ${styles.btnPrimary}`}>
              Create Event
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
