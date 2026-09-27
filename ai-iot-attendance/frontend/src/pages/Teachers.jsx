import "./Teachers.css";
import { useEffect, useState } from "react";
import { listTeachers, getTeacher, registerTeacher } from "../api/teachers";
import Loader from "../components/Loader";

function Teachers() {
  const [teachers, setTeachers] = useState([]);
  const [selectedTeacher, setSelectedTeacher] = useState(null);

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const [showAddTeacher, setShowAddTeacher] = useState(false);

  const [teacherForm, setTeacherForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const loadTeachers = async () => {
    setLoading(true);
    setMessage("");

    try {
      const data = await listTeachers();

      setTeachers(Array.isArray(data) ? data : []);
    } catch (err) {
      setMessage(err.message || "Failed to load teachers.");
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadTeachers();
  }, []);


  const handleViewTeacher = async (teacherId) => {
    try {
      setMessage("");

      const teacher = await getTeacher(teacherId);

      setSelectedTeacher(teacher);
    } catch (err) {
      setMessage(err.message || "Failed to load teacher details.");
    }
  };


  const handleAddTeacher = async (e) => {
    e.preventDefault();

    try {
      setMessage("");

      await registerTeacher(teacherForm);

      setShowAddTeacher(false);

      setTeacherForm({
        name: "",
        email: "",
        password: "",
      });

      await loadTeachers();

    } catch (err) {
      setMessage(err.message || "Failed to create teacher.");
    }
  };


  return (
    <div className="teachers-page">

      <div className="teachers-header">
        <div>
          <p className="teachers-subtitle">
            Teacher Management
          </p>

          <h1>Teachers</h1>

          <p className="teachers-description">
            View registered teachers and their account details.
          </p>
        </div>


        <div>
          <button
            className="teachers-refresh-button"
            onClick={loadTeachers}
          >
            ↻ Refresh
          </button>

          <button
            className="teachers-add-button"
            onClick={() => setShowAddTeacher(true)}
          >
            + Add Teacher
          </button>
        </div>

      </div>



      {message && (
        <p className="teachers-error">
          {message}
        </p>
      )}



      <div className="teachers-card">

        <div className="teachers-card-header">
          <div>
            <h2>All Teachers</h2>

            <div>
              {loading ? (
                <Loader />
              ) : (
                <p>
                  {teachers.length} teacher{teachers.length === 1 ? "" : "s"} found
                </p>
              )}
            </div>
          </div>
        </div>



        <div className="teachers-table-wrapper">

          <table className="teachers-table">

            <thead>
              <tr>
                <th>Teacher ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Created At</th>
              </tr>
            </thead>


            <tbody>

              {teachers.map((teacher) => (

                <tr key={teacher.teacher_id}>

                  <td>
                    <button
                      className="teachers-id-button"
                      onClick={() =>
                        handleViewTeacher(teacher.teacher_id)
                      }
                    >
                      {teacher.teacher_id}
                    </button>
                  </td>

                  <td>{teacher.name}</td>

                  <td>{teacher.email}</td>

                  <td>
                    <span className="teachers-role">
                      {teacher.role}
                    </span>
                  </td>

                  <td>
                    {teacher.created_at || "-"}
                  </td>

                </tr>

              ))}



              {!loading && teachers.length === 0 && (
                <tr>
                  <td
                    colSpan="5"
                    className="teachers-empty"
                  >
                    No teachers found.
                  </td>
                </tr>
              )}

            </tbody>

          </table>

        </div>

      </div>




      {selectedTeacher && (

        <div className="teachers-card">

          <div className="teachers-card-header">

            <div>
              <h2>Teacher Details</h2>

              <p>
                {selectedTeacher.teacher_id}
              </p>
            </div>


            <button
              className="teachers-refresh-button"
              onClick={() => setSelectedTeacher(null)}
            >
              Close
            </button>

          </div>



          <div className="teachers-details">

            <div>
              <strong>Teacher ID</strong>
              <p>{selectedTeacher.teacher_id}</p>
            </div>


            <div>
              <strong>Name</strong>
              <p>{selectedTeacher.name}</p>
            </div>


            <div>
              <strong>Email</strong>
              <p>{selectedTeacher.email}</p>
            </div>


            <div>
              <strong>Role</strong>
              <p>{selectedTeacher.role}</p>
            </div>


            <div>
              <strong>Created At</strong>
              <p>{selectedTeacher.created_at || "-"}</p>
            </div>

          </div>

        </div>

      )}

      {showAddTeacher && (
        <div className="teacher-modal-overlay">

          <div className="teacher-modal">

            <h2>Add Teacher</h2>

            <form onSubmit={handleAddTeacher}>

              <input
                type="text"
                placeholder="Name"
                value={teacherForm.name}
                onChange={(e) =>
                  setTeacherForm({
                    ...teacherForm,
                    name: e.target.value,
                  })
                }
                required
              />


              <input
                type="email"
                placeholder="Email"
                value={teacherForm.email}
                onChange={(e) =>
                  setTeacherForm({
                    ...teacherForm,
                    email: e.target.value,
                  })
                }
                required
              />


              <input
                type="password"
                placeholder="Password"
                value={teacherForm.password}
                onChange={(e) =>
                  setTeacherForm({
                    ...teacherForm,
                    password: e.target.value,
                  })
                }
                required
              />


              <div className="teacher-modal-actions">

                <button
                  type="button"
                  className="teachers-cancel-button"
                  onClick={() => setShowAddTeacher(false)}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="teachers-add-button"
                >
                  Create
                </button>

              </div>


            </form>

          </div>

        </div>
      )}


    </div>
  );
}

export default Teachers;