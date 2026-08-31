import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isLoading, isLoggedIn } = useAuth();

  if (isLoading) {
    // Still checking whether there's an existing Cognito session -
    // avoid a flash-redirect to /login before we actually know.
    return <div style={{ padding: 24 }}>Loading…</div>;
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
