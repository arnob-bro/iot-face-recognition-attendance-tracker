import "./Dashboard.css";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getDashboardStats } from "../api/reports";
import { listCourses } from "../api/courses";

import { getActiveSession } from "../api/attendance";
import Loader from "../components/Loader";

function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    total_students: 0,
    total_courses: 0,
    active_sessions: 0,
    today_present: 0,
    today_absent: 0,
    today_late: 0,
    today_percentage: 0.0,
  });

  const [courses, setCourses] = useState([]);

  const [activeSession, setActiveSession] = useState(null);

  const [message, setMessage] = useState("");

  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, coursesData, activeData] = await Promise.all([
        getDashboardStats().catch(() => null),
        listCourses().catch(() => ({ courses: [] })),
        getActiveSession().catch(() => null),
      ]);


      if (statsData) setStats(statsData);
      if (coursesData?.courses) setCourses(coursesData.courses);

      setActiveSession(activeData);

    } catch (error) {
      setMessage(error.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);



  return (
    <div className="dashboard">

      <div className="dashboard-header">
        <div className="dashboard-title">
          <h1>Dashboard</h1>
          <p className="dashboard-description">
            Welcome back, {user?.name || "Teacher"}. Powered by FastAPI & Firebase.
          </p>
        </div>

        <div className="dashboard-date">
          <span>Today</span>
          <strong>
            {new Date().toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </strong>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon students-icon">👥</div>
          <div className="stat-info">
            <p>Total Students</p>
            <h2>{stats.total_students}</h2>
            <Link to="/students" className="dashboard-nav-button">
              View Students
            </Link>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon present-icon">📚</div>
          <div className="stat-info">
            <p>Total Courses</p>
            <h2>{stats.total_courses || courses.length}</h2>
            <span className="stat-positive">Active in Firestore</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon present-icon">✓</div>
          <div className="stat-info">
            <p>Live Sessions</p>
            <h2>{stats.active_sessions}</h2>
            <span className={activeSession ? "stat-positive" : ""}>
              {activeSession ? "1 session running" : "No active session"}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon accuracy-icon">◎</div>
          <div className="stat-info">
            <p>Today's Present</p>
            <h2>{stats.today_present}</h2>
            <span className="stat-positive">
              {stats.today_percentage ? `${stats.today_percentage.toFixed(0)}% Rate` : "0% Rate"}
            </span>
          </div>
        </div>
      </div>

      <div className="dashboard-content">

        {loading ? (
          <Loader />
        ) : (
          <div className="attendance-card">

            <div className="card-header">
              <div>
                <h2>Attendance Session Status</h2>
                <p>
                  Sessions are created automatically according to configured routines.
                </p>
              </div>
            </div>


            {activeSession ? (

              <div className="attendance-details">

                <p>
                  Live session running for course:
                  {" "}
                  <strong>
                    {
                      courses.find(
                        (c) =>
                          c.course_id === activeSession.course_id
                      )?.course_name ||
                      activeSession.course_id
                    }
                  </strong>
                </p>


                <button
                  className="view-button"
                  type="button"
                  onClick={() => navigate("/attendance")}
                >
                  Open Live Camera Console
                </button>


              </div>

            ) : (

              <div className="attendance-details">

                <p>
                  No active session currently running.
                </p>

                <p>
                  The scheduler will create sessions automatically based on routines.
                </p>

              </div>

            )}


            {message && (
              <p className="dashboard-description">
                {message}
              </p>
            )}


          </div>
        )}

      </div>


    </div>
  );
}

export default Dashboard;

