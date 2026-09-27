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


  const isStudent = user?.role === "student";
  const isAdmin = user?.role === "admin";
  const isTeacher = user?.role === "teacher";


  return (

    <header className="app-nav">


      <div
        className="app-nav-brand"
        onClick={() =>
          navigate(
            isStudent
              ? "/student/dashboard"
              : "/dashboard"
          )
        }
      >
        Attendance Tracker
      </div>



      <nav className="app-nav-links">


        {isStudent ? (

          <>
            <NavLink to="/student/dashboard">
              Dashboard
            </NavLink>

            <NavLink to="/student/attendance">
              My Attendance
            </NavLink>

            <NavLink to="/student/profile">
              Profile
            </NavLink>
          </>


        ) : (

          <>

            <NavLink to="/dashboard">
              Dashboard
            </NavLink>


            <NavLink to="/students">
              Students
            </NavLink>


            <NavLink to="/courses">
              Courses
            </NavLink>


            <NavLink to="/attendance">
              Attendance
            </NavLink>


            <NavLink to="/reports">
              Reports
            </NavLink>


            {isAdmin && (

              <NavLink to="/devices">
                Devices
              </NavLink>

            )}


            {isAdmin && (

              <NavLink to="/teachers">
                Teachers
              </NavLink>

            )}

            {(isAdmin || isTeacher) && (

              <NavLink to="/routines">
                Routines
              </NavLink>

            )}

          </>

        )}


      </nav>




      <div className="app-nav-user">

        <div className="app-nav-user-name">

          <span>
            {user?.name}
          </span>


          <span>

            {
              isAdmin
                ? "Admin"
                : isStudent
                  ? "Student"
                  : "Teacher"
            }

          </span>

        </div>



        <button
          type="button"
          onClick={handleLogout}
        >
          Logout
        </button>


      </div>


    </header>

  );

}


export default AppNav;