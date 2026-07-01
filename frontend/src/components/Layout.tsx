import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";
import { useLogout } from "@/hooks/useAuth";
import ToastContainer from "@/components/Toast";
import styles from "./Layout.module.css";

const navItems = [
  { to: "/", label: "Dashboard", icon: "\u2302", roles: null },
  { to: "/events", label: "Events", icon: "\u2606", roles: null },
  { to: "/tickets", label: "Tickets", icon: "\u2691", roles: null },
  { to: "/checkin", label: "Check-in", icon: "\u2713", roles: ["admin", "operator", "checkin_staff"] },
  { to: "/admin", label: "Admin", icon: "\u2699", roles: ["admin"] },
];

export default function Layout() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const visibleNavItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  );

  return (
    <div className={styles.layout}>
      <div
        className={`${styles.overlay} ${sidebarOpen ? "" : styles.hidden}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside
        className={`${styles.sidebar} ${sidebarCollapsed ? styles.collapsed : ""} ${sidebarOpen ? styles.open : ""}`}
      >
        <div className={styles.brand}>
          <span className={styles.icon}>E</span>
          <span>Evvents</span>
        </div>

        <nav className={styles.nav}>
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.active : ""}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <span className={styles.icon}>{item.icon}</span>
              <span className={styles.label}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className={styles.toggleBtn}
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          <span className={styles.icon}>{sidebarCollapsed ? "\u25B6" : "\u25C0"}</span>
          <span className={styles.label}>{sidebarCollapsed ? "Expand" : "Collapse"}</span>
        </button>
      </aside>

      <header className={styles.topbar}>
        <button
          type="button"
          className={styles.mobileToggle}
          onClick={() => setSidebarOpen(true)}
        >
          &#9776;
        </button>
        <div />
        <div className={styles.userSection}>
          <span className={styles.userName}>{user?.name}</span>
          <button type="button" className={styles.logoutBtn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <main className={styles.main}>
        <Outlet />
      </main>

      <ToastContainer />
    </div>
  );
}
