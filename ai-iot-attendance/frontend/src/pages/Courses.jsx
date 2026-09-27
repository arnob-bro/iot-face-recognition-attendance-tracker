import "./Courses.css";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import Loader from "../components/Loader";
import {
    listCourses,
    createCourse,
    updateCourse,
    deleteCourse,
    getCourseStudents,
    enrollStudent,
    unenrollStudent,
} from "../api/courses";


function Courses() {
    const { user } = useAuth();

    const isAdmin = user?.role === "admin";


    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [courseStudents, setCourseStudents] = useState([]);

    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");

    const [showModal, setShowModal] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    


    const [formData, setFormData] = useState({
        name: "",
        code: "",
        department: "",
        teacher_id: "",
    });


    const [enrollStudentId, setEnrollStudentId] = useState("");


    async function loadCourses() {
        setLoading(true);
        try {
            

            const data = await listCourses();

            console.log("Courses API response:", data);

            setCourses(data.courses || []);

        } catch (err) {
            setMessage(err.message || "Failed to load courses.");
        } finally {
            setLoading(false);
        }
    }


    useEffect(() => {
        loadCourses();
    }, []);



    async function handleViewStudents(course) {
        try {
            setSelectedCourse(course);

            const students = await getCourseStudents(course.course_id);

            setCourseStudents(students);

        } catch (err) {
            setMessage(err.message || "Failed to load students.");
        }
    }



    function openCreateModal() {
        setEditingCourse(null);

        setFormData({
            name: "",
            code: "",
            department: "",
            teacher_id: "",
            section: "",
        });

        setShowModal(true);
    }



    function openEditModal(course) {
        setEditingCourse(course);

        setFormData({
            name: course.course_name,
            code: course.course_code,
            department: course.department,
            teacher_id: course.teacher_id || "",
            section: course.section || "",
        });

        setShowModal(true);
    }



    async function handleSubmitCourse(e) {
        e.preventDefault();

        try {

            if (editingCourse) {

                await updateCourse(
                    editingCourse.course_id,
                    formData
                );

                setMessage("Course updated successfully.");

            } else {

                await createCourse(formData);

                setMessage("Course created successfully.");
            }


            setShowModal(false);

            await loadCourses();


        } catch (err) {
            setMessage(err.message || "Failed to save course.");
        }
    }




    async function handleDelete(courseId) {

        const confirmDelete = window.confirm(
            "Delete this course?"
        );

        if (!confirmDelete) return;


        try {

            await deleteCourse(courseId);

            setMessage("Course deleted successfully.");

            await loadCourses();


            if (selectedCourse?.course_id === courseId) {
                setSelectedCourse(null);
                setCourseStudents([]);
            }


        } catch (err) {
            setMessage(err.message || "Failed to delete course.");
        }
    }




    async function handleEnroll() {

        if (!enrollStudentId || !selectedCourse) return;


        try {

            await enrollStudent(
                selectedCourse.course_id,
                enrollStudentId
            );


            setEnrollStudentId("");

            await handleViewStudents(selectedCourse);


        } catch (err) {
            setMessage(err.message || "Failed to enroll student.");
        }

    }




    async function handleRemoveStudent(studentId) {

        try {

            await unenrollStudent(
                selectedCourse.course_id,
                studentId
            );


            await handleViewStudents(selectedCourse);


        } catch (err) {
            setMessage(err.message || "Failed to remove student.");
        }

    }




    return (

        <div className="courses-page">


            <div className="courses-header">

                <div>
                    <h1>Courses</h1>

                    <p>
                        Manage courses and enrolled students.
                    </p>
                </div>


                {isAdmin && (
                    <button
                        className="primary-btn"
                        onClick={openCreateModal}
                    >
                        + Add Course
                    </button>
                )}

            </div>



            {message && (
                <p className="courses-message">
                    {message}
                </p>
            )}




            <div className="courses-card">


                {loading ? (

                    <Loader/>

                ) : (

                    <table className="courses-table">

                        <thead>

                            <tr>
                                <th>Code</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Teacher ID</th>
                                <th>Total Classes</th>
                                <th>Actions</th>
                            </tr>

                        </thead>


                        <tbody>

                            {courses.map((course) => (

                                <tr key={course.course_id}>

                                    <td>
                                        {course.course_code}
                                    </td>

                                    <td>
                                        {course.course_name}
                                    </td>

                                    <td>
                                        {course.department}
                                    </td>

                                    <td>
                                        {course.teacher_id || "-"}
                                    </td>

                                    <td>
                                        {course.total_classes || 0}
                                    </td>


                                    <td>

                                        <div className="action-buttons">


                                            <button
                                                className={
                                                    selectedCourse?.course_id === course.course_id
                                                        ? "view-btn active"
                                                        : "view-btn"
                                                }
                                                onClick={() =>
                                                    handleViewStudents(course)
                                                }
                                            >
                                                View Students
                                            </button>



                                            {isAdmin && (
                                                <>
                                                    <button
                                                        className="edit-btn"
                                                        onClick={() =>
                                                            openEditModal(course)
                                                        }
                                                    >
                                                        Edit
                                                    </button>


                                                    <button
                                                        className="delete-btn"
                                                        onClick={() =>
                                                            handleDelete(course.course_id)
                                                        }
                                                    >
                                                        Delete
                                                    </button>
                                                </>
                                            )}


                                        </div>

                                    </td>


                                </tr>

                            ))}


                        </tbody>

                    </table>

                )}

            </div>




            {selectedCourse && (

                <div className="students-card">

                    <div className="students-header">

                        <h2>
                            {selectedCourse.course_name} Students
                        </h2>


                        <button
                            className="close-btn"
                            onClick={() => {
                                setSelectedCourse(null);
                                setCourseStudents([]);
                            }}
                        >
                            Close
                        </button>


                    </div>



                    {isAdmin && (

                        <div className="enroll-box">

                            <input
                                placeholder="Student ID"
                                value={enrollStudentId}
                                onChange={(e) =>
                                    setEnrollStudentId(e.target.value)
                                }
                            />


                            <button
                                className="primary-btn"
                                onClick={handleEnroll}
                            >
                                Enroll
                            </button>

                        </div>

                    )}



                    <table className="courses-table">

                        <thead>

                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Batch</th>
                                {isAdmin && <th>Action</th>}
                            </tr>

                        </thead>


                        <tbody>

                            {courseStudents.map((student) => (

                                <tr key={student.student_id}>

                                    <td>{student.student_id}</td>

                                    <td>{student.name}</td>

                                    <td>{student.department}</td>

                                    <td>{student.batch}</td>


                                    {isAdmin && (

                                        <td>

                                            <button
                                                className="delete-btn"
                                                onClick={() =>
                                                    handleRemoveStudent(
                                                        student.student_id
                                                    )
                                                }
                                            >
                                                Remove
                                            </button>

                                        </td>

                                    )}


                                </tr>

                            ))}


                        </tbody>

                    </table>


                </div>

            )}




            {showModal && (

                <div className="modal-overlay">

                    <div className="course-modal">


                        <h2>
                            {editingCourse ? "Edit Course" : "Add Course"}
                        </h2>


                        <form onSubmit={handleSubmitCourse}>


                            <input
                                placeholder="Course Name"
                                value={formData.name}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        name: e.target.value
                                    })
                                }
                                required
                            />


                            <input
                                placeholder="Course Code"
                                value={formData.code}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        code: e.target.value
                                    })
                                }
                                required
                            />


                            <input
                                placeholder="Department"
                                value={formData.department}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        department: e.target.value
                                    })
                                }
                                required
                            />


                            <input
                                placeholder="Teacher ID"
                                value={formData.teacher_id}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        teacher_id: e.target.value
                                    })
                                }
                            />

                            <input
                                placeholder="Section"
                                value={formData.section}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        section: e.target.value
                                    })
                                }
                            />


                            <div className="modal-buttons">

                                <button
                                    type="button"
                                    className="cancel-btn"
                                    onClick={() =>
                                        setShowModal(false)
                                    }
                                >
                                    Cancel
                                </button>


                                <button
                                    type="submit"
                                    className="primary-btn"
                                >
                                    Save
                                </button>


                            </div>


                        </form>


                    </div>

                </div>

            )}


        </div>

    );
}


export default Courses;