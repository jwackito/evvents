import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";
import { useLogout } from "@/hooks/useAuth";

export default function Layout() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div>
      <nav>
        <Link to="/">Evvents</Link>
        <div>
          <Link to="/events">Events</Link>
          <span>{user?.name}</span>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
