import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth/AuthContext.jsx";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Inbox from "./pages/Inbox.jsx";
import Digest from "./pages/Digest.jsx";
import Drafts from "./pages/Drafts.jsx";
import Calendar from "./pages/Calendar.jsx";
import Status from "./pages/Status.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="splash" aria-busy="true">Loading…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/inbox" replace />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/inbox/:id" element={<Inbox />} />
        <Route path="/digest" element={<Digest />} />
        <Route path="/drafts" element={<Drafts />} />
        <Route path="/drafts/:id" element={<Drafts />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/status" element={<Status />} />
        <Route path="*" element={<Navigate to="/inbox" replace />} />
      </Route>
    </Routes>
  );
}
