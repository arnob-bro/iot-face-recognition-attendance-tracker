import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AppNav.css";

function AppNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="app-nav">
      <div className="app-nav-brand" onClick={() => navigate("/dashboard")}>Attendance Tracker</div>

      <nav className="app-nav-links">
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/students">Students</NavLink>
        <NavLink to="/courses">Courses</NavLink>
        <NavLink to="/attendance">Attendance</NavLink>
        <NavLink to="/reports">Reports</NavLink>
        {user?.role === "admin" && (
          <NavLink to="/devices">Devices</NavLink>
        )}
        {user?.role === "admin" && (
          <NavLink to="/teachers">Teachers</NavLink>
        )}
      </nav>

      <div className="app-nav-user">
        <div className="app-nav-user-name">
        <span>
          {user?.name} 
        </span>
        <span>
          {user?.role === "admin" ? "Admin" : "Teacher"}
        </span>
        </div>
        <button type="button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

export default AppNav;
