import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useCheckinEvents, useScanTicket, useUndoCheckin, useCheckinHistory, useCheckinSearch } from "@/hooks/useCheckin";
import styles from "./CheckinEvent.module.css";

export default function CheckinEvent() {
  const { eventId } = useParams<{ eventId: string }>();
  const [qrHash, setQrHash] = useState("");
  const [lastResult, setLastResult] = useState<{ qrHash: string; checkedIn: boolean } | null>(null);
  const scanTicket = useScanTicket();
  const undoCheckin = useUndoCheckin();
  const [tab, setTab] = useState<"history" | "search">("history");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: eventsData } = useCheckinEvents();
  const event = eventsData?.data?.find((e) => e.id === eventId);

  const { data: historyData } = useCheckinHistory(eventId ?? "", 1);
  const { data: searchData } = useCheckinSearch(eventId ?? "", searchQuery);

  const handleScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (!qrHash.trim()) return;
    scanTicket.mutate(qrHash.trim(), {
      onSuccess: () => setLastResult({ qrHash: qrHash.trim(), checkedIn: true }),
      onError: () => setLastResult({ qrHash: qrHash.trim(), checkedIn: false }),
    });
    setQrHash("");
  };

  const handleUndo = (hash: string) => {
    undoCheckin.mutate(hash);
  };

  if (!eventId) {
    return <div className={styles.page}>Event not found.</div>;
  }

  return (
    <div className={styles.page}>
      <Link to="/checkin" className={styles.backLink}>&larr; Back to Events</Link>
      <div className={styles.eventTitle}>
        {event?.title ?? "Check-In"}
      </div>

      <div className={styles.scannerSection}>
        <form className={styles.scanForm} onSubmit={handleScan}>
          <input
            className={styles.scanInput}
            value={qrHash}
            onChange={(e) => setQrHash(e.target.value)}
            placeholder="Scan or paste QR hash..."
            autoFocus
          />
          <button
            type="submit"
            className={`${styles.btn} ${styles.btnPrimary}`}
            disabled={scanTicket.isPending || !qrHash.trim()}
          >
            {scanTicket.isPending ? "..." : "Scan"}
          </button>
        </form>

        {scanTicket.data && (
          <div className={styles.scanResult}>
            <div className={styles.scanResultHeader}>
              <div>
                <div className={styles.scanAttendee}>
                  {scanTicket.data.data.attendee_name}
                </div>
                <div className={styles.scanType}>
                  {scanTicket.data.data.ticket_type}
                </div>
              </div>
              <span className={`${styles.scanBadge} ${scanTicket.data.data.checked_in ? styles.checked_in : styles.not_checked_in}`}>
                {scanTicket.data.data.checked_in ? "Checked In" : "Not Checked In"}
              </span>
            </div>
            {scanTicket.data.data.checked_in_at && (
              <div className={styles.scanTime}>
                Checked in at: {new Date(scanTicket.data.data.checked_in_at).toLocaleString()}
              </div>
            )}
            {scanTicket.data.data.checked_in && (
              <div className={styles.scanActions}>
                <button
                  className={`${styles.btn} ${styles.btnWarning} ${styles.btnSmall}`}
                  onClick={() => handleUndo(lastResult?.qrHash ?? "")}
                  disabled={undoCheckin.isPending}
                >
                  {undoCheckin.isPending ? "..." : "Undo Check-In"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === "history" ? styles.active : ""}`}
          onClick={() => setTab("history")}
        >
          History
        </button>
        <button
          className={`${styles.tab} ${tab === "search" ? styles.active : ""}`}
          onClick={() => setTab("search")}
        >
          Search
        </button>
      </div>

      {tab === "history" && (
        <div>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Attendee</th>
                <th>Ticket Type</th>
                <th>Checked In At</th>
              </tr>
            </thead>
            <tbody>
              {(historyData?.data ?? []).length > 0 ? (
                historyData!.data.map((item) => (
                  <tr key={item.id}>
                    <td>{item.attendee_name}</td>
                    <td>{item.ticket_type}</td>
                    <td>{new Date(item.checked_in_at).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className={styles.tableEmpty}>
                    No check-in history yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "search" && (
        <div>
          <div className={styles.searchForm}>
            <input
              className={styles.searchInput}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or ticket type..."
            />
          </div>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Attendee</th>
                <th>Ticket Type</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(searchData?.data ?? []).length > 0 ? (
                searchData!.data.map((item) => (
                  <tr key={item.id}>
                    <td>{item.attendee_name}</td>
                    <td>{item.ticket_type}</td>
                    <td>
                      <span className={`${styles.scanBadge} ${item.checked_in ? styles.checked_in : styles.not_checked_in}`}>
                        {item.checked_in ? "In" : "Out"}
                      </span>
                    </td>
                    <td>
                      {item.checked_in ? (
                        <button
                          className={`${styles.btn} ${styles.btnWarning} ${styles.btnSmall}`}
                          onClick={() => handleUndo(item.qr_hash)}
                          disabled={undoCheckin.isPending}
                        >
                          Undo
                        </button>
                      ) : (
                        <button
                          className={`${styles.btn} ${styles.btnSuccess} ${styles.btnSmall}`}
                          onClick={() => {
                            scanTicket.mutate(item.qr_hash);
                          }}
                          disabled={scanTicket.isPending}
                        >
                          Check In
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className={styles.tableEmpty}>
                    {searchQuery ? "No matching attendees" : "Type to search"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
