import { useEffect, useState } from "react";
import { getStudentCourses } from "../api/students";
import "./StudentAttendance.css";
import Loader from "../components/Loader";

function StudentAttendance() {
  const [courses, setCourses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const loadAttendance = async () => {
      try {
        const enrolledCourses = await getStudentCourses();
        setCourses(Array.isArray(enrolledCourses) ? enrolledCourses : []);
      } catch (error) {
        setMessage(error.message || "Failed to load attendance.");
      } finally {
        setLoading(false);
      }
    };

    loadAttendance();
  }, []);

  if (loading) {
    return <Loader />;
  }

  return (
    <div className="student-attendance-page">
      <h1>My Attendance</h1>

      {message && <p className="student-attendance-message">{message}</p>}

      {courses.length === 0 ? (
        <p className="student-attendance-empty">
          You are not currently enrolled in any courses.
        </p>
      ) : (
        <div className="student-course-list">
          {courses.map((course) => (
            <section className="student-course-section" key={course.course_id}>
              <div className="student-course-header">
                <div>
                  <h2>
                    {course.course_code} · {course.course_name}
                  </h2>
                  <p>
                    Section {course.section} · {course.department}
                  </p>
                </div>
                <div className="student-course-percentage">
                  <strong>{course.percentage.toFixed(1)}%</strong>
                  <span>attendance</span>
                </div>
              </div>

              <div className="student-course-stats">
                <span>Total classes: {course.total_classes}</span>
                <span>Present: {course.present}</span>
                <span>Late: {course.late}</span>
                <span>Absent: {course.absent}</span>
              </div>

              {course.attendance_history.length === 0 ? (
                <p className="student-course-empty">
                  No sessions have been recorded yet.
                </p>
              ) : (
                <table className="student-attendance-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Status</th>
                      <th>Method</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {course.attendance_history.map((record) => (
                      <tr key={record.session_id}>
                        <td>
                          {record.session_date || record.start_time || "-"}
                        </td>
                        <td>{record.status}</td>
                        <td>{record.method || "-"}</td>
                        <td>{record.confidence ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

export default StudentAttendance;
