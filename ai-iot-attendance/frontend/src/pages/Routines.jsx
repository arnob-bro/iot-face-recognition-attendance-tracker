import { useEffect, useState } from "react";

import { listRoutines, createRoutine, updateRoutine, deleteRoutine, } from "../api/routines";

import { listCourses } from "../api/courses";
import { listTeachers } from "../api/teachers";
import { listDevices } from "../api/devices";
import "./Routines.css";
import { useAuth } from "../context/AuthContext";
import Loader from "../components/Loader";



function Routines() {
  const { user } = useAuth();
  const [routines, setRoutines] = useState([]);

  const [courses, setCourses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [devices, setDevices] = useState([]);


  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [editingRoutineId, setEditingRoutineId] = useState(null);


  const [routineForm, setRoutineForm] = useState({

    course_id: "",
    teacher_id: "",
    device_id: "",
    room: "",
    day_of_week: "0",
    start_time: "",
    end_time: "",
    late_threshold_minutes: 15,
    is_active: true,

  });



  const loadData = async () => {

    setLoading(true);
    setMessage("");

    try {

      const [
        routineData,
        courseData,
        teacherData,
        deviceData,
      ] = await Promise.all([

        listRoutines(),
        listCourses(),
        listTeachers(),
        listDevices(),

      ]);


      setRoutines(
        routineData?.routines || routineData || []
      );


      setCourses(
        courseData?.courses || courseData || []
      );


      setTeachers(
        teacherData?.teachers || teacherData || []
      );


      setDevices(
        deviceData?.devices || deviceData || []
      );


    } catch (error) {

      setMessage(
        error.message || "Failed to load routines."
      );

    } finally {

      setLoading(false);

    }

  };



  useEffect(() => {

    loadData();

  }, []);




  const handleChange = (e) => {

    const { name, value, type, checked } = e.target;


    setRoutineForm({

      ...routineForm,

      [name]:
        type === "checkbox"
          ? checked
          : value,

    });

  };

  const resetRoutineForm = () => {

    setRoutineForm({

      course_id: "",
      teacher_id: "",
      device_id: "",
      room: "",
      day_of_week: "0",
      start_time: "",
      end_time: "",
      late_threshold_minutes: 15,
      is_active: true,

    });

    setEditingRoutineId(null);

  };




  const handleSaveRoutine = async (e) => {

    e.preventDefault();


    setMessage("");


    try {

      const routineData = {

        ...routineForm,

        day_of_week:
          Number(routineForm.day_of_week),

        late_threshold_minutes:
          Number(routineForm.late_threshold_minutes),

      };

      if (editingRoutineId) {

        await updateRoutine(
          editingRoutineId,
          routineData
        );

      } else {

        await createRoutine(routineData);

      }

      resetRoutineForm();


      await loadData();


    } catch (error) {

      setMessage(
        error.message || "Failed to create routine."
      );

    }

  };




  const handleDeleteRoutine = async (routineId) => {

    const confirmDelete = window.confirm(
      "Delete this routine?"
    );


    if (!confirmDelete) {
      return;
    }


    try {

      await deleteRoutine(routineId);

      await loadData();


    } catch (error) {

      setMessage(
        error.message || "Failed to delete routine."
      );

    }

  };

  const handleEditRoutine = (routine) => {

    setRoutineForm({

      course_id: routine.course_id || "",
      teacher_id: routine.teacher_id || "",
      device_id: routine.device_id || "",
      room: routine.room || "",
      day_of_week: String(
        routine.day_of_week ?? 0
      ),
      start_time: routine.start_time || "",
      end_time: routine.end_time || "",
      late_threshold_minutes:
        routine.late_threshold_minutes || 15,
      is_active:
        routine.is_active ?? true,

    });


    setEditingRoutineId(
      routine.routine_id
    );

  };







  return (

    <div className="routine-page">


      <h1>
        Class Routines
      </h1>



      {message && (

        <p className="routine-message">
          {message}
        </p>

      )}



      {user?.role === "admin" && (
        <>
          <section className="routine-form-section">

            <h2>
              {editingRoutineId
                ? "Edit Routine"
                : "Create Routine"}
            </h2>



            <form
              className="routine-form"
              onSubmit={handleSaveRoutine}
            >



              <label>
                Course

                <select
                  name="course_id"
                  value={routineForm.course_id}
                  onChange={handleChange}
                  required
                >

                  <option value="">
                    Select course
                  </option>


                  {courses.map((course) => (

                    <option
                      key={course.course_id}
                      value={course.course_id}
                    >

                      {course.name || course.course_name}

                    </option>

                  ))}

                </select>

              </label>





              <label>
                Teacher

                <select
                  name="teacher_id"
                  value={routineForm.teacher_id}
                  onChange={handleChange}
                  required
                >

                  <option value="">
                    Select teacher
                  </option>


                  {teachers.map((teacher) => (

                    <option
                      key={teacher.teacher_id}
                      value={teacher.teacher_id}
                    >

                      {teacher.name}

                    </option>

                  ))}


                </select>

              </label>





              <label>
                Device

                <select
                  name="device_id"
                  value={routineForm.device_id}
                  onChange={handleChange}
                >

                  <option value="">
                    Select device
                  </option>


                  {devices.map((device) => (

                    <option
                      key={device.device_id}
                      value={device.device_id}
                    >

                      {device.name || device.device_id}

                    </option>

                  ))}


                </select>

              </label>





              <label>
                Room

                <input
                  name="room"
                  value={routineForm.room}
                  onChange={handleChange}
                  placeholder="Example: 7B03"
                />

              </label>





              <label>
                Day

                <select
                  name="day_of_week"
                  value={routineForm.day_of_week}
                  onChange={handleChange}
                >

                  <option value="0">
                    Monday
                  </option>

                  <option value="1">
                    Tuesday
                  </option>

                  <option value="2">
                    Wednesday
                  </option>

                  <option value="3">
                    Thursday
                  </option>

                  <option value="4">
                    Friday
                  </option>

                  <option value="5">
                    Saturday
                  </option>

                  <option value="6">
                    Sunday
                  </option>

                </select>

              </label>





              <label>
                Start Time

                <input
                  type="time"
                  name="start_time"
                  value={routineForm.start_time}
                  onChange={handleChange}
                  required
                />

              </label>





              <label>
                End Time

                <input
                  type="time"
                  name="end_time"
                  value={routineForm.end_time}
                  onChange={handleChange}
                  required
                />

              </label>





              <label>
                Late Threshold (minutes)

                <input
                  type="number"
                  name="late_threshold_minutes"
                  value={
                    routineForm.late_threshold_minutes
                  }
                  onChange={handleChange}
                />

              </label>





              <label className="routine-checkbox">

                <input
                  type="checkbox"
                  name="is_active"
                  checked={routineForm.is_active}
                  onChange={handleChange}
                />

                Active

              </label>





              <button type="submit">
                {editingRoutineId
                  ? "Update Routine"
                  : "Create Routine"}
              </button>

              {editingRoutineId && (

                <button
                  type="button"
                  onClick={resetRoutineForm}
                >
                  Cancel Edit
                </button>

              )}

            </form>
          </section>
        </>
      )}


      {loading ? (
        <Loader />
      ) : (
        <section className="routine-list-section">


          <h2>
            Existing Routines
          </h2>



          {routines.length === 0 ? (

            <p>
              No routines found.
            </p>

          ) : (


            <div className="routine-list">


              {routines.map((routine) => (

                <div
                  className="routine-card"
                  key={routine.routine_id}
                >


                  <p>
                    Course: {routine.course_id}
                  </p>


                  <p>
                    Teacher: {routine.teacher_id}
                  </p>


                  <p>
                    Room: {routine.room || "-"}
                  </p>


                  <p>
                    Time: {routine.start_time} - {routine.end_time}
                  </p>


                  <p>
                    Active: {routine.is_active ? "Yes" : "No"}
                  </p>



                  {user?.role === "admin" && (

                    <div className="routine-actions">

                      <button
                        onClick={() => handleEditRoutine(routine)}
                      >
                        Edit
                      </button>


                      <button
                        onClick={() => handleDeleteRoutine(routine.routine_id)}
                      >
                        Delete
                      </button>

                    </div>

                  )}


                </div>

              ))}


            </div>


          )}


        </section>
      )}



    </div>


  );

}


export default Routines;