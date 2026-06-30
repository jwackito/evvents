import { useMe } from "@/hooks/useAuth";
import { useEvents } from "@/hooks/useEvents";

export default function Dashboard() {
  const { data: me, isLoading: meLoading } = useMe();
  const { data: eventsData, isLoading: eventsLoading } = useEvents(1, 5);

  if (meLoading || eventsLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {me?.name ?? "User"}!</p>
      <h2>Upcoming Events</h2>
      {eventsData && eventsData.data.length > 0 ? (
        <ul>
          {eventsData.data.map((event) => (
            <li key={event.id}>{event.title}</li>
          ))}
        </ul>
      ) : (
        <p>No upcoming events.</p>
      )}
    </div>
  );
}
