import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DEMO_MODE = true;

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (DEMO_MODE) {
    return children;
  }

  if (loading) {
    return (
      <div style={{ padding: "48px", textAlign: "center", color: "#64748b" }}>
        Loading...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default ProtectedRoute;