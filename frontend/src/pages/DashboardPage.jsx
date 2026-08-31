import { useAuth } from "../auth/AuthContext";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div style={{ padding: 24 }}>
      <h1>Receipts</h1>
      <p>Logged in as {user}</p>
      <button onClick={logout}>Log out</button>
      <p style={{ color: "var(--stone)" }}>
        Full dashboard (receipt list, upload) coming next.
      </p>
    </div>
  );
}
