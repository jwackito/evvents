import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useCreateEvent, useUpdateEvent, useEventDetail } from "@/hooks/useOrgEvents";
import styles from "./EventForm.module.css";

function toSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function EventForm() {
  const { slug } = useParams<{ slug?: string }>();
  const navigate = useNavigate();
  const isEdit = !!slug;
  const { data: existingEvent } = useEventDetail(slug ?? "");

  const createEvent = useCreateEvent();
  const updateEvent = useUpdateEvent();

  const [title, setTitle] = useState("");
  const [eventSlug, setEventSlug] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("12:00");
  const [location, setLocation] = useState("");
  const [capacity, setCapacity] = useState("100");
  const [status, setStatus] = useState("draft");
  const [seatingType, setSeatingType] = useState("general");
  const [description, setDescription] = useState("");
  const [coverImage, setCoverImage] = useState("");
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isEdit && existingEvent) {
      const ev = existingEvent.data;
      setTitle(ev.title);
      setEventSlug(ev.slug);
      setLocation(ev.location ?? "");
      setCapacity(String(ev.capacity));
      setStatus(ev.status);
      setSeatingType(ev.seating_type);
      setDescription(ev.description ?? "");
      setCoverImage(ev.cover_image ?? "");
      if (ev.date) {
        const d = new Date(ev.date);
        setDate(d.toISOString().slice(0, 10));
        setTime(d.toISOString().slice(11, 16));
      }
    }
  }, [isEdit, existingEvent]);

  const handleTitleChange = (value: string) => {
    setTitle(value);
    if (!slugManuallyEdited && !isEdit) {
      setEventSlug(toSlug(value));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!title.trim()) { setError("Title is required"); return; }
    if (!eventSlug.trim()) { setError("Slug is required"); return; }
    if (!date) { setError("Date is required"); return; }

    const dateTime = new Date(`${date}T${time}:00`);

    const payload: Record<string, unknown> = {
      title: title.trim(),
      slug: eventSlug.trim(),
      date: dateTime.toISOString(),
      capacity: parseInt(capacity, 10) || 100,
      status,
      seating_type: seatingType,
      description: description.trim() || null,
      location: location.trim() || null,
      cover_image: coverImage.trim() || null,
    };

    try {
      if (isEdit) {
        await updateEvent.mutateAsync({ id: existingEvent!.data.id, data: payload });
      } else {
        await createEvent.mutateAsync(payload);
      }
      navigate(`/events/${eventSlug.trim()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save event");
    }
  };

  const isPending = createEvent.isPending || updateEvent.isPending;

  if (isEdit && !existingEvent) {
    return (
      <div className={styles.page}>
        <Link to="/events" className={styles.backLink}>&larr; Back to Events</Link>
        <p style={{ color: "var(--color-text-secondary)" }}>Loading event...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Link to="/events" className={styles.backLink}>&larr; Back to Events</Link>
      <h1 className={styles.title}>{isEdit ? "Edit Event" : "Create Event"}</h1>

      {error && <div className={styles.errorBanner}>{error}</div>}

      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>Title *</label>
          <input
            className={styles.input}
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            placeholder="My Awesome Event"
            required
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Slug *</label>
          <input
            className={styles.input}
            value={eventSlug}
            onChange={(e) => { setEventSlug(e.target.value); setSlugManuallyEdited(true); }}
            placeholder="my-awesome-event"
            required
          />
          <span className={styles.hint}>Used in URLs: /events/{eventSlug || "slug"}</span>
        </div>

        <div className={styles.row}>
          <div className={styles.field}>
            <label className={styles.label}>Date *</label>
            <input
              className={styles.input}
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Time</label>
            <input
              className={styles.input}
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
            />
          </div>
        </div>

        <div className={styles.row}>
          <div className={styles.field}>
            <label className={styles.label}>Location</label>
            <input
              className={styles.input}
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Venue name or address"
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Capacity *</label>
            <input
              className={styles.input}
              type="number"
              min="1"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              required
            />
          </div>
        </div>

        <div className={styles.row}>
          <div className={styles.field}>
            <label className={styles.label}>Status</label>
            <select
              className={styles.select}
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Seating Type</label>
            <select
              className={styles.select}
              value={seatingType}
              onChange={(e) => setSeatingType(e.target.value)}
            >
              <option value="general">General</option>
              <option value="assigned">Assigned</option>
            </select>
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Description</label>
          <textarea
            className={`${styles.input} ${styles.textarea}`}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Tell people about your event..."
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Cover Image URL</label>
          <input
            className={styles.input}
            value={coverImage}
            onChange={(e) => setCoverImage(e.target.value)}
            placeholder="https://example.com/image.jpg"
          />
        </div>

        <div className={styles.actions}>
          <button
            type="submit"
            className={`${styles.btn} ${styles.btnPrimary}`}
            disabled={isPending}
          >
            {isPending ? "Saving..." : isEdit ? "Update Event" : "Create Event"}
          </button>
          <Link to="/events" className={`${styles.btn} ${styles.btnSecondary}`}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
