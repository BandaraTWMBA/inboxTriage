import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api, USE_MOCK } from "../api/index.js";
import { useAuth } from "../auth/AuthContext.jsx";

const NAV = [
  { to: "/inbox", label: "Inbox" },
  { to: "/digest", label: "Digest" },
  { to: "/drafts", label: "Drafts" },
  { to: "/calendar", label: "Calendar", badge: true },
  { to: "/status", label: "Status" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [pending, setPending] = useState(0);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api.listProposals()
        .then((rows) => alive && setPending(rows.filter((p) => p.status === "pending").length))
        .catch(() => {});
    load();
    window.addEventListener("it:proposals-changed", load);
    return () => {
      alive = false;
      window.removeEventListener("it:proposals-changed", load);
    };
  }, []);

  return (
    <div className="shell">
      <nav className="rail" aria-label="Main">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="26" height="26" />
          InboxTriage
        </div>
        <div className="nav">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => `nav__link${isActive ? " active" : ""}`}>
              {n.label}
              {n.badge && pending > 0 && <span className="nav__badge" aria-label={`${pending} waiting`}>{pending}</span>}
            </NavLink>
          ))}
        </div>
        <div className="rail__foot">
          {USE_MOCK && <p className="rail__note">Sample data. No backend connected.</p>}
          <div className="rail__user">{user?.email}</div>
          <button className="rail__signout" onClick={logout}>Sign out</button>
        </div>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
