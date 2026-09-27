import "./Reports.css";
import { useEffect, useMemo, useState } from "react";
import { listCourses } from "../api/courses";
import { getDailyReport, getWeeklyReport, getMonthlyReport, getStudentReport } from "../api/reports";
import Loader from "../components/Loader";



function Reports() {
  const [courses, setCourses] = useState([]);
  const [reports, setReports] = useState([]);
  //const [students, setStudents] = useState([]);
  //const [studentSearch, setStudentSearch] = useState("");
  //const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentId, setStudentId] = useState("");
  const [studentReport, setStudentReport] = useState([]);
  const [studentMessage, setStudentMessage] = useState("");


  const [reportType, setReportType] = useState("daily");
  const [courseFilter, setCourseFilter] = useState("all");

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [studentReportLoading, setStudentReportLoading] = useState(false);


  const today = new Date().toISOString().split("T")[0];





  async function loadCourses() {
    setLoading(true);
    try {
      const data = await listCourses();
      setCourses(data.courses || []);
    } catch (err) {
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  }


  async function loadReports() {
    setLoading(true);
    setMessage("");

    try {
      let selectedCourses = courses;

      if (courseFilter !== "all") {
        selectedCourses = courses.filter(
          (c) => c.course_id === courseFilter
        );
      }


      const results = [];


      for (const course of selectedCourses) {

        let response;


        if (reportType === "daily") {
          response = await getDailyReport(
            course.course_id,
            today
          );
        }


        if (reportType === "weekly") {
          response = await getWeeklyReport(
            course.course_id,
            today
          );
        }


        if (reportType === "monthly") {
          const date = new Date();

          response = await getMonthlyReport(
            course.course_id,
            date.getFullYear(),
            date.getMonth() + 1
          );
        }


        if (response) {
          if (Array.isArray(response)) {
            results.push(...response);
          } else {
            results.push(response);
          }
        }
      }


      setReports(results);

    } catch (err) {
      setMessage(err.message || "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  }


  async function handleStudentSearch() {
    if (!studentId.trim()) {
      setStudentReport([]);
      setStudentMessage("Enter a student ID.");
      return;
    }

    try {
      setStudentReportLoading(true);
      setStudentMessage("");

      const data = await getStudentReport(studentId.trim());

      setStudentReport(data);

      if (data.length === 0) {
        setStudentMessage("No attendance records found for this student.");
      }

    } catch (err) {
      setStudentReport([]);
      setStudentMessage(
        err.message || "Failed to load student report."
      );
    } finally {
      setStudentReportLoading(false);
    }
  }



  useEffect(() => {
    loadCourses();
  }, []);



  useEffect(() => {
    if (courses.length > 0) {
      loadReports();
    }
  }, [courses, reportType, courseFilter]);



  const totals = useMemo(() => {

    return reports.reduce(
      (acc, report) => {

        acc.present += report.present || 0;
        acc.absent += report.absent || 0;
        acc.late += report.late || 0;

        acc.total += report.total_students || 0;

        return acc;
      },
      {
        present: 0,
        absent: 0,
        late: 0,
        total: 0
      }
    );

  }, [reports]);



  const attendanceRate =
    totals.total
      ? Math.round(
        ((totals.present + totals.late) /
          totals.total) * 100
      )
      : 0;



  return (
    <div className="reports-page">

      <div className="reports-top-section">

        <div className="reports-header">
          <div>
            <p className="reports-subtitle">
              Attendance Overview
            </p>

            <h1>Reports</h1>

            <p className="reports-description">
              View attendance reports by day, week, month and course.
            </p>
          </div>
        </div>


        <div className="reports-toolbar">

          <div className="reports-filter-wrapper">
            <label>
              Report Type
            </label>

            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <option value="daily">
                Today
              </option>

              <option value="weekly">
                Weekly
              </option>

              <option value="monthly">
                Monthly
              </option>
            </select>
          </div>


          <div className="reports-filter-wrapper">
            <label>
              Course
            </label>

            <select
              value={courseFilter}
              onChange={(e) => setCourseFilter(e.target.value)}
            >
              <option value="all">
                All Courses
              </option>

              {courses.map(course => (
                <option
                  key={course.course_id}
                  value={course.course_id}
                >
                  {course.course_name}
                </option>
              ))}
            </select>
          </div>


          <button
            className="reports-reset-button"
            onClick={loadReports}
          >
            ↻ Refresh
          </button>

        </div>

      </div>

      {studentMessage && (
        <p className="reports-error">
          {studentMessage}
        </p>
      )}


      <div className="reports-stats">


        <div className="reports-stat-card">
          <div className="reports-stat-icon overall-stat-icon">
            ◎
          </div>

          <div>
            <p>
              Reports
            </p>

            <h2>
              {reports.length}
            </h2>
          </div>
        </div>



        <div className="reports-stat-card">
          <div className="reports-stat-icon present-stat-icon">
            ✓
          </div>

          <div>
            <p>
              Present
            </p>

            <h2>
              {totals.present}
            </h2>
          </div>
        </div>



        <div className="reports-stat-card">
          <div className="reports-stat-icon late-stat-icon">
            ◷
          </div>

          <div>
            <p>
              Late
            </p>

            <h2>
              {totals.late}
            </h2>
          </div>
        </div>



        <div className="reports-stat-card">
          <div className="reports-stat-icon absent-stat-icon">
            ✕
          </div>

          <div>
            <p>
              Absent
            </p>

            <h2>
              {totals.absent}
            </h2>
          </div>
        </div>



        <div className="reports-stat-card">
          <div className="reports-stat-icon rate-stat-icon">
            %
          </div>

          <div>
            <p>
              Attendance Rate
            </p>

            <h2>
              {attendanceRate}%
            </h2>
          </div>
        </div>


      </div>




      <div className="reports-card">

        <div className="reports-card-header">

          <h2>
            Attendance Reports
          </h2>


          {
            loading
              ?
              <Loader />
              : (
                <div className="reports-table-wrapper">


                  <table className="reports-table">

                    <thead>

                      <tr>
                        <th>Date</th>
                        <th>Course</th>
                        <th>Total Students</th>
                        <th>Present</th>
                        <th>Late</th>
                        <th>Absent</th>
                        <th>Rate</th>
                      </tr>

                    </thead>


                    <tbody>


                      {reports.map((report, index) => (

                        <tr key={index}>

                          <td>
                            {report.date}
                          </td>

                          <td>
                            {report.course_name}
                          </td>

                          <td>
                            {report.total_students}
                          </td>

                          <td>
                            {report.present}
                          </td>

                          <td>
                            {report.late}
                          </td>

                          <td>
                            {report.absent}
                          </td>

                          <td>
                            {report.percentage}%
                          </td>

                        </tr>

                      ))}



                      {!loading && reports.length === 0 && (

                        <tr>

                          <td
                            colSpan="7"
                            className="reports-empty"
                          >
                            No reports found.
                          </td>

                        </tr>

                      )}



                    </tbody>

                  </table>


                </div>

              )
          }


        </div>






      </div>


      <div className="student-search-section">

        <h2>
          View Reports by student ID
        </h2>

        <div className="student-search-controls">

          <div className="reports-filter-wrapper">

            <label>
              Student ID
            </label>

            <input
              type="text"
              placeholder="Enter student ID..."
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            />

          </div>


          <button
            className="reports-reset-button"
            onClick={handleStudentSearch}
          >
            Search
          </button>


          <button
            className="reports-reset-button"
            onClick={() => {
              setStudentReport([]);
              setStudentId("");
            }}
          >
            ↻ Refresh
          </button>



        </div>

      </div>



      {studentReportLoading ? (

        <div className="reports-card">
          <Loader />
        </div>

      ) : studentReport.length > 0 && (

        <div className="reports-card">

          <div className="reports-card-header">
            <h2>
              Student Attendance Report
            </h2>
          </div>


          <div className="reports-table-wrapper">

            <table className="reports-table">

              <thead>
                <tr>
                  <th>Course Code</th>
                  <th>Course Name</th>
                  <th>Total Classes</th>
                  <th>Present</th>
                  <th>Late</th>
                  <th>Absent</th>
                  <th>Rate</th>
                </tr>
              </thead>


              <tbody>

                {studentReport.map((report) => (
                  <tr key={report.course_id}>

                    <td>
                      {report.course_code}
                    </td>

                    <td>
                      {report.course_name}
                    </td>

                    <td>
                      {report.total_classes}
                    </td>

                    <td>
                      {report.present}
                    </td>

                    <td>
                      {report.late}
                    </td>

                    <td>
                      {report.absent}
                    </td>

                    <td>
                      {report.percentage}%
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>

        </div>

      )}


    </div>
  );
}


export default Reports;