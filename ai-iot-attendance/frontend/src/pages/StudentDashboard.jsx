import { useEffect, useState } from "react";
import {
  getStudentMe,
  getStudentAttendance,
} from "../api/students";
import "./StudentDashboard.css";
import Loader from "../components/Loader";


function StudentDashboard() {

  const [student, setStudent] = useState(null);
  const [attendance, setAttendance] = useState([]);

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");


  const loadStudentData = async () => {

    setLoading(true);
    setMessage("");

    try {

      const profile = await getStudentMe();

      setStudent(profile);


      const records = await getStudentAttendance(
        profile.student_id
      );


      setAttendance(
        Array.isArray(records)
          ? records
          : []
      );


    } catch (error) {

      setMessage(
        error.message || "Failed to load student data."
      );

    } finally {

      setLoading(false);

    }

  };


  useEffect(() => {

    loadStudentData();

  }, []);



  if (loading) {

    return (
      <Loader/>
    );

  }



  return (

    <div className="student-dashboard">


      <h1>
        Student Dashboard
      </h1>



      {message && (

        <p className="student-message">
          {message}
        </p>

      )}




      {student && (

        <div className="student-profile-card">

          <h2>
            Profile
          </h2>


          <p>
            <strong>Name:</strong>{" "}
            {student.name}
          </p>


          <p>
            <strong>Student ID:</strong>{" "}
            {student.student_id}
          </p>


          <p>
            <strong>Email:</strong>{" "}
            {student.email}
          </p>


          <p>
            <strong>Department:</strong>{" "}
            {student.department}
          </p>


          <p>
            <strong>Batch:</strong>{" "}
            {student.batch}
          </p>


        </div>

      )}




      <div className="student-attendance-section">

        <h2>
          Attendance History
        </h2>



        {attendance.length === 0 ? (

          <p className="student-empty">
            No attendance records found.
          </p>

        ) : (


          <table className="student-attendance-table">


            <thead>

              <tr>

                <th>
                  Course
                </th>


                <th>
                  Date
                </th>


                <th>
                  Status
                </th>


                <th>
                  Method
                </th>


                <th>
                  Confidence
                </th>


              </tr>


            </thead>



            <tbody>


              {attendance.map((record, index) => (


                <tr key={index}>


                  <td>
                    {record.course_name || "-"}
                  </td>


                  <td>
                    {record.detected_at || "-"}
                  </td>


                  <td>
                    {record.status || "-"}
                  </td>


                  <td>
                    {record.method || "-"}
                  </td>


                  <td>
                    {record.confidence ?? "-"}
                  </td>


                </tr>


              ))}


            </tbody>


          </table>


        )}


      </div>


    </div>

  );

}


export default StudentDashboard;