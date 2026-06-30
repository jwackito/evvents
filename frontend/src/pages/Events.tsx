import { useEvents } from "@/hooks/useEvents";

export default function Events() {
  const { data, isLoading, error } = useEvents();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div>
      <h1>Events</h1>
      {data && data.data.length > 0 ? (
        <ul>
          {data.data.map((event) => (
            <li key={event.id}>
              <strong>{event.title}</strong> — {event.date}
            </li>
          ))}
        </ul>
      ) : (
        <p>No events found.</p>
      )}
    </div>
  );
}
