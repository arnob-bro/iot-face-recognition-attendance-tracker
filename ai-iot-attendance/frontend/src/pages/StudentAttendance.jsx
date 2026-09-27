import { useEffect, useState } from "react";
import { getStudentCourses } from "../api/students";
import "./StudentAttendance.css";
import Loader from "../components/Loader";
import AttendancePieChart from "../components/AttendancePieChart";

function StudentAttendance() {
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const loadAttendance = async () => {
      try {
        const enrolledCourses = await getStudentCourses();
        const availableCourses = Array.isArray(enrolledCourses)
          ? enrolledCourses
          : [];
        setCourses(availableCourses);
        setSelectedCourseId(
          availableCourses[0] ? String(availableCourses[0].course_id) : ""
        );
      } catch (error) {
        setMessage(error.message || "Failed to load attendance.");
      } finally {
        setLoading(false);
      }
    };

    loadAttendance();
  }, []);

  const selectedCourse = courses.find(
    (course) => String(course.course_id) === selectedCourseId
  );

  if (loading) {
    return <Loader />;
  }

  return (
    <div className="student-attendance-page">
      <div className="student-attendance-heading">
        <h1>My Attendance</h1>
        {courses.length > 0 && (
          <label className="student-course-picker">
            <span>Course</span>
            <select
              value={selectedCourseId}
              onChange={(event) => setSelectedCourseId(event.target.value)}
            >
              {courses.map((course) => (
                <option key={course.course_id} value={String(course.course_id)}>
                  {course.course_code} · {course.course_name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {message && <p className="student-attendance-message">{message}</p>}

      {courses.length === 0 ? (
        <p className="student-attendance-empty">
          You are not currently enrolled in any courses.
        </p>
      ) : (
        selectedCourse && (
          <div className="student-course-list">
            <section
              className="student-course-section"
              key={selectedCourse.course_id}
            >
              <div className="student-course-header">
                <div>
                  <h2>
                    {selectedCourse.course_code} · {selectedCourse.course_name}
                  </h2>
                  <p>
                    Section {selectedCourse.section} · {selectedCourse.department}
                  </p>
                </div>
                <div className="student-course-percentage">
                  <strong>
                    {Number(selectedCourse.percentage || 0).toFixed(1)}%
                  </strong>
                  <span>attendance</span>
                </div>
              </div>

              <div className="student-course-stats">
                <span>Total classes: {selectedCourse.total_classes || 0}</span>
                <span>Present: {selectedCourse.present || 0}</span>
                <span>Late: {selectedCourse.late || 0}</span>
                <span>Absent: {selectedCourse.absent || 0}</span>
              </div>

              <AttendancePieChart reports={[selectedCourse]} />

              {(selectedCourse.attendance_history || []).length === 0 ? (
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
                    {(selectedCourse.attendance_history || []).map((record) => (
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
          </div>
        )
      )}
    </div>
  );
}

export default StudentAttendance;
