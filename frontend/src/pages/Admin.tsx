import { useState } from "react";
import { useAdminOrgs, useCreateOrg, useUpdateOrg, useDeleteOrg, useAdminUsers, useCreateUser, useUpdateUser, useDeleteUser } from "@/hooks/useAdmin";
import styles from "./Admin.module.css";

export default function Admin() {
  const [tab, setTab] = useState<"orgs" | "users">("orgs");

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Admin</h1>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === "orgs" ? styles.active : ""}`}
          onClick={() => setTab("orgs")}
        >
          Organizations
        </button>
        <button
          className={`${styles.tab} ${tab === "users" ? styles.active : ""}`}
          onClick={() => setTab("users")}
        >
          Users
        </button>
      </div>

      {tab === "orgs" ? <OrgsPanel /> : <UsersPanel />}
    </div>
  );
}

function OrgsPanel() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminOrgs(page);
  const createOrg = useCreateOrg();
  const updateOrg = useUpdateOrg();
  const deleteOrg = useDeleteOrg();

  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editingOrg, setEditingOrg] = useState<{ id: string; name: string; slug: string } | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  const openCreate = () => {
    setName("");
    setSlug("");
    setModal("create");
  };

  const openEdit = (org: { id: string; name: string; slug: string }) => {
    setEditingOrg(org);
    setName(org.name);
    setSlug(org.slug);
    setModal("edit");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) return;
    if (modal === "create") {
      createOrg.mutate({ name: name.trim(), slug: slug.trim() }, { onSuccess: () => setModal(null) });
    } else if (modal === "edit" && editingOrg) {
      updateOrg.mutate({ id: editingOrg.id, data: { name: name.trim(), slug: slug.trim() } }, { onSuccess: () => setModal(null) });
    }
  };

  const isPending = createOrg.isPending || updateOrg.isPending;
  const orgs = data?.data ?? [];
  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / 20));

  if (isLoading) {
    return (
      <div>
        {[1, 2, 3].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 48, marginBottom: 8 }} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={openCreate}>
          + New Organization
        </button>
      </div>

      {orgs.length > 0 ? (
        <>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Slug</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orgs.map((org) => (
                <tr key={org.id}>
                  <td style={{ fontWeight: 500 }}>{org.name}</td>
                  <td style={{ fontFamily: "monospace", fontSize: "var(--text-xs)" }}>{org.slug}</td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        className={`${styles.btn} ${styles.btnSecondary} ${styles.btnSmall}`}
                        onClick={() => openEdit(org)}
                      >
                        Edit
                      </button>
                      <button
                        className={`${styles.btn} ${styles.btnDanger} ${styles.btnSmall}`}
                        onClick={() => { if (confirm(`Delete ${org.name}?`)) deleteOrg.mutate(org.id); }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.pageBtn} disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </button>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
                Page {page} of {totalPages}
              </span>
              <button className={styles.pageBtn} disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className={styles.emptyState}>No organizations yet.</div>
      )}

      {modal && (
        <div className={styles.overlay} onClick={() => setModal(null)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>
              {modal === "create" ? "New Organization" : "Edit Organization"}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.field}>
                <label className={styles.label}>Name</label>
                <input className={styles.input} value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Slug</label>
                <input className={styles.input} value={slug} onChange={(e) => setSlug(e.target.value)} required />
              </div>
              <div className={styles.modalActions}>
                <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={isPending}>
                  {isPending ? "Saving..." : "Save"}
                </button>
                <button type="button" className={`${styles.btn} ${styles.btnSecondary}`} onClick={() => setModal(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function UsersPanel() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminUsers(page);
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editingUser, setEditingUser] = useState<{ id: string } | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("operator");
  const [organizationId, setOrganizationId] = useState("");

  const openCreate = () => {
    setName("");
    setEmail("");
    setPassword("");
    setRole("operator");
    setOrganizationId("");
    setModal("create");
  };

  const openEdit = (user: { id: string; name: string; email: string; role: string; organization_id: string | null }) => {
    setEditingUser({ id: user.id });
    setName(user.name);
    setEmail(user.email);
    setPassword("");
    setRole(user.role);
    setOrganizationId(user.organization_id ?? "");
    setModal("edit");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    const payload: Record<string, unknown> = {
      name: name.trim(),
      email: email.trim(),
      role,
      organization_id: organizationId || null,
    };
    if (password.trim()) {
      payload.password = password.trim();
    }
    if (modal === "create") {
      payload.password = password.trim() || "changeme123";
      createUser.mutate(payload, { onSuccess: () => setModal(null) });
    } else if (modal === "edit" && editingUser) {
      updateUser.mutate({ id: editingUser.id, data: payload }, { onSuccess: () => setModal(null) });
    }
  };

  const isPending = createUser.isPending || updateUser.isPending;
  const users = data?.data ?? [];
  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / 20));

  if (isLoading) {
    return (
      <div>
        {[1, 2, 3].map((i) => (
          <div key={i} className={styles.skeleton} style={{ height: 48, marginBottom: 8 }} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={openCreate}>
          + New User
        </button>
      </div>

      {users.length > 0 ? (
        <>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Org</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td style={{ fontWeight: 500 }}>{u.name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span style={{
                      display: "inline-flex",
                      padding: "2px 8px",
                      borderRadius: 999,
                      fontSize: "var(--text-xs)",
                      fontWeight: 500,
                      background: u.role === "admin" ? "var(--color-danger-light)" : u.role === "operator" ? "var(--color-primary-light)" : "var(--color-bg)",
                      color: u.role === "admin" ? "#991b1b" : u.role === "operator" ? "var(--color-primary)" : "var(--color-text-secondary)",
                    }}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: "var(--text-xs)" }}>
                    {u.organization_id ? u.organization_id.slice(0, 8) + "..." : "—"}
                  </td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        className={`${styles.btn} ${styles.btnSecondary} ${styles.btnSmall}`}
                        onClick={() => openEdit(u)}
                      >
                        Edit
                      </button>
                      <button
                        className={`${styles.btn} ${styles.btnDanger} ${styles.btnSmall}`}
                        onClick={() => { if (confirm(`Delete ${u.name}?`)) deleteUser.mutate(u.id); }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.pageBtn} disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </button>
              <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)" }}>
                Page {page} of {totalPages}
              </span>
              <button className={styles.pageBtn} disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className={styles.emptyState}>No users yet.</div>
      )}

      {modal && (
        <div className={styles.overlay} onClick={() => setModal(null)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>
              {modal === "create" ? "New User" : "Edit User"}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.field}>
                <label className={styles.label}>Name</label>
                <input className={styles.input} value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Email</label>
                <input className={styles.input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>{modal === "create" ? "Password" : "Password (leave blank to keep)"}</label>
                <input className={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  required={modal === "create"} minLength={modal === "create" ? 8 : undefined} />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Role</label>
                <select className={styles.select} value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="operator">Operator</option>
                  <option value="admin">Admin</option>
                  <option value="checkin_staff">Check-in Staff</option>
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Organization ID</label>
                <input className={styles.input} value={organizationId} onChange={(e) => setOrganizationId(e.target.value)}
                  placeholder="UUID or leave empty" />
              </div>
              <div className={styles.modalActions}>
                <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={isPending}>
                  {isPending ? "Saving..." : "Save"}
                </button>
                <button type="button" className={`${styles.btn} ${styles.btnSecondary}`} onClick={() => setModal(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
