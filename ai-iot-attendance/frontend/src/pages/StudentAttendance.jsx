import { useEffect, useState } from "react";
import {
    getStudentMe,
    getStudentAttendance,
} from "../api/students";
import "./StudentAttendance.css";
import Loader from "../components/Loader";



function StudentAttendance() {

    const [attendance, setAttendance] = useState([]);

    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");



    useEffect(() => {

        const loadAttendance = async () => {

            try {

                const student = await getStudentMe();


                const records = await getStudentAttendance(
                    student.student_id
                );


                setAttendance(
                    Array.isArray(records)
                        ? records
                        : []
                );


            } catch (error) {

                setMessage(
                    error.message || "Failed to load attendance."
                );

            } finally {

                setLoading(false);

            }

        };


        loadAttendance();

    }, []);




    if (loading) {

        return (
            <Loader/>
        );

    }




    return (

        <div className="student-attendance-page">

            <h1>
                My Attendance
            </h1>


            {message && (

                <p className="student-attendance-message">
                    {message}
                </p>

            )}



            {attendance.length === 0 ? (

                <p className="student-attendance-empty">
                    No attendance records found.
                </p>

            ) : (

                <table className="student-attendance-table">

                    <thead>

                        <tr>
                            <th>Course</th>

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

    );

}


export default StudentAttendance;