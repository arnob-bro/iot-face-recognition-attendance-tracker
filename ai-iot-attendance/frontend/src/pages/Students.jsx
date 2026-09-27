import "./Students.css";
import { useEffect, useMemo, useState, useRef } from "react";
import { listStudents, createStudent } from "../api/students";
import { enrollFace, deleteEnrollment } from "../api/faces";
import Loader from "../components/Loader";

const emptyForm = {
  name: "",
  student_id: "",
  department: "CSE",
  batch: "",
  email: "",
};

function Students() {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  // Face Enrollment Modal state
  const [enrollingStudent, setEnrollingStudent] = useState(null);
  const [enrollMode, setEnrollMode] = useState("camera"); // "camera" | "upload"
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [capturedPreview, setCapturedPreview] = useState(null);
  const [enrollMessage, setEnrollMessage] = useState("");
  const [enrollBusy, setEnrollBusy] = useState(false);

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const loadStudents = async () => {
    setLoading(true);

    try {
      const payload = await listStudents();
      setStudents(payload.students || []);

    } catch (error) {
      setMessage(error.message || "Failed to load students from Firestore.");

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudents();
  }, []);

  const filtered = useMemo(() => {
    return students.filter((student) => {
      const q = search.toLowerCase();
      const matchesSearch =
        !search ||
        (student.name || "").toLowerCase().includes(q) ||
        (student.student_id || "").toLowerCase().includes(q) ||
        (student.email || "").toLowerCase().includes(q);

      const matchesDept =
        !deptFilter || (student.department || "").toLowerCase() === deptFilter.toLowerCase();

      return matchesSearch && matchesDept;
    });
  }, [students, search, deptFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMessage("");

    try {
      await createStudent({
        student_id: form.student_id.trim(),
        name: form.name.trim(),
        department: form.department.trim(),
        batch: form.batch.trim(),
        email: form.email.trim(),
      });
      setForm(emptyForm);
      setShowAddModal(false);
      setMessage(`Student ${form.name} created successfully.`);
      await loadStudents();
    } catch (error) {
      setMessage(error.message || "Could not create student.");
    } finally {
      setBusy(false);
    }
  };

  // --- Face Enrollment Camera Controls ---
  const startCamera = async () => {
    setCapturedBlob(null);
    setCapturedPreview(null);
    setEnrollMessage("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err) {
      setEnrollMessage(`Camera access denied or unavailable: ${err.message}`);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const captureFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCapturedBlob(blob);
          setCapturedPreview(URL.createObjectURL(blob));
          stopCamera();
        }
      },
      "image/jpeg",
      0.92
    );
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setCapturedBlob(file);
      setCapturedPreview(URL.createObjectURL(file));
      setEnrollMessage("");
    }
  };

  const handleEnrollSubmit = async () => {
    if (!enrollingStudent || !capturedBlob) {
      setEnrollMessage("Please take a photo or select an image file first.");
      return;
    }

    setEnrollBusy(true);
    setEnrollMessage("Uploading to AI pipeline...");

    try {
      const res = await enrollFace(enrollingStudent.student_id, capturedBlob);
      setEnrollMessage(`Success: ${res.message} (Quality score: ${(res.quality * 100).toFixed(0)}%)`);
      await loadStudents();
      setTimeout(() => {
        closeEnrollModal();
      }, 1500);
    } catch (err) {
      setEnrollMessage(`Enrollment failed: ${err.message}`);
    } finally {
      setEnrollBusy(false);
    }
  };

  const openEnrollModal = (student) => {
    setEnrollingStudent(student);
    setCapturedBlob(null);
    setCapturedPreview(null);
    setEnrollMessage("");
    setEnrollMode("camera");
  };

  const closeEnrollModal = () => {
    stopCamera();
    setEnrollingStudent(null);
    setCapturedBlob(null);
    setCapturedPreview(null);
    setEnrollMessage("");
  };

  const departments = [...new Set(students.map((s) => s.department).filter(Boolean))];

  return (
    <div className="students-page">

      {/* Header */}
      <div className="students-header">
        <div>
          <p className="students-subtitle">Database Records</p>
          <h1>Students Management</h1>
          <p className="students-description">
            Enrolled students in Firebase Firestore used by the AI face recognition system.
          </p>
        </div>

        <button
          className="add-student-button"
          type="button"
          onClick={() => setShowAddModal(true)}
        >
          <span>+</span>
          Add Student
        </button>
      </div>


      {/* Statistics */}
      <div className="student-stats">

        <div className="student-stat-card">
          <div className="student-stat-icon total-icon">👥</div>
          <div>
            <p>Total Students</p>
            <h2>{students.length}</h2>
          </div>
        </div>

        <div className="student-stat-card">
          <div className="student-stat-icon active-icon">📷</div>
          <div>
            <p>Faces Enrolled</p>
            <h2>
              {students.filter((s) => s.face_enrolled).length}
            </h2>
          </div>
        </div>

        <div className="student-stat-card">
          <div className="student-stat-icon class-icon">🏛</div>
          <div>
            <p>Departments</p>
            <h2>{departments.length}</h2>
          </div>
        </div>

        <div className="student-stat-card">
          <div className="student-stat-icon inactive-icon">▦</div>
          <div>
            <p>Filtered List</p>
            <h2>{filtered.length}</h2>
          </div>
        </div>

      </div>


      {message && (
        <p
          className={`students-message ${message.includes("success") ? "success" : "error"
            }`}
        >
          {message}
        </p>
      )}


      {/* Student List Card */}
      <div className="students-table-card">

        <div className="students-table-header">
          <div>
            <h2>Enrolled Students</h2>
            <p>
              Students eligible for AI attendance recognition sessions
            </p>
          </div>
        </div>


        <div className="students-toolbar">

          <div className="search-box">
            <span className="search-icon">⌕</span>

            <input
              type="text"
              placeholder="Search by name, student ID, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>


          <select
            className="class-filter"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
          >
            <option value="">All Departments</option>

            {departments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}

          </select>

        </div>


        <div className="table-wrapper">

          {loading ? (
            <Loader />
          ) : (<table className="students-table">

            <thead>
              <tr>
                <th>Student</th>
                <th>Student ID</th>
                <th>Department</th>
                <th>Batch</th>
                <th>Face Status</th>
                <th>Actions</th>
              </tr>
            </thead>


            <tbody>

              {filtered.map((student) => (

                <tr key={student.student_id}>

                  <td>
                    <div className="student-profile">

                      <div className="student-avatar">
                        {(student.name || "ST")
                          .slice(0, 2)
                          .toUpperCase()}
                      </div>

                      <div>
                        <strong>{student.name}</strong>

                        <span className="student-email">
                          {student.email}
                        </span>

                      </div>

                    </div>
                  </td>


                  <td>
                    <code className="student-id">
                      {student.student_id}
                    </code>
                  </td>


                  <td>{student.department}</td>

                  <td>
                    {student.batch || "—"}
                  </td>


                  <td>

                    {student.face_enrolled ? (

                      <span className="face-status enrolled">
                        ✓ Enrolled
                      </span>

                    ) : (

                      <span className="face-status not-enrolled">
                        ✕ Not Enrolled
                      </span>

                    )}

                  </td>


                  <td>

                    <button
                      type="button"
                      className={
                        student.face_enrolled
                          ? "enroll-button enrolled"
                          : "enroll-button"
                      }
                      onClick={() => openEnrollModal(student)}
                    >
                      {student.face_enrolled
                        ? "Re-enroll Face"
                        : "Enroll Face"}
                    </button>

                  </td>

                </tr>

              ))}


              {filtered.length === 0 && (

                <tr>
                  <td colSpan={6} className="students-empty">
                    No students matching your search.
                  </td>
                </tr>

              )}

            </tbody>

          </table>)}



        </div>

      </div>

      {/* ================= ADD STUDENT MODAL ================= */}
      {showAddModal && (
        <div
          className="auth-overlay"
          onClick={() => setShowAddModal(false)}
        >

          <div
            className="auth-modal"
            onClick={(e) => e.stopPropagation()}
          >

            <div className="modal-header">

              <h2>Add New Student</h2>

              <button
                type="button"
                className="modal-close"
                onClick={() => setShowAddModal(false)}
              >
                ×
              </button>

            </div>


            <form
              onSubmit={handleCreate}
              className="student-form"
            >

              <div>

                <label className="form-label">
                  Student ID
                </label>

                <input
                  className="student-input"
                  placeholder="e.g. 202401001"
                  value={form.student_id}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      student_id: e.target.value,
                    })
                  }
                  required
                />

              </div>


              <div>

                <label className="form-label">
                  Full Name
                </label>

                <input
                  className="student-input"
                  placeholder="e.g. John Doe"
                  value={form.name}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      name: e.target.value,
                    })
                  }
                  required
                />

              </div>


              <div>

                <label className="form-label">
                  Email
                </label>

                <input
                  className="student-input"
                  type="email"
                  placeholder="e.g. student@university.edu"
                  value={form.email}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      email: e.target.value,
                    })
                  }
                  required
                />

              </div>


              <div className="student-form-grid">

                <div>

                  <label className="form-label">
                    Department
                  </label>

                  <input
                    className="student-input"
                    placeholder="e.g. CSE"
                    value={form.department}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        department: e.target.value,
                      })
                    }
                    required
                  />

                </div>


                <div>

                  <label className="form-label">
                    Batch / Section
                  </label>

                  <input
                    className="student-input"
                    placeholder="e.g. 24"
                    value={form.batch}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        batch: e.target.value,
                      })
                    }
                    required
                  />

                </div>

              </div>


              <div className="modal-actions">

                <button
                  type="button"
                  className="modal-secondary-button"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="modal-primary-button"
                  disabled={busy}
                >
                  {busy ? "Saving..." : "Save Student"}
                </button>

              </div>


            </form>

          </div>

        </div>
      )}
      {/* ================= FACE ENROLLMENT MODAL ================= */}
      {enrollingStudent && (
        <div
          className="auth-overlay face-overlay"
          onClick={closeEnrollModal}
        >

          <div
            className="auth-modal face-modal"
            onClick={(e) => e.stopPropagation()}
          >

            <div className="modal-header">

              <div>

                <h2 className="face-modal-title">
                  Enroll Face Embedding
                </h2>

                <p className="face-modal-description">
                  Student: <strong>{enrollingStudent.name}</strong>{" "}
                  (ID: {enrollingStudent.student_id})
                </p>

              </div>


              <button
                type="button"
                className="modal-close"
                onClick={closeEnrollModal}
              >
                ×
              </button>

            </div>


            {/* Mode selection tabs */}
            <div className="enroll-tabs">

              <button
                type="button"
                className={`enroll-tab ${enrollMode === "camera" ? "active" : ""
                  }`}
                onClick={() => {
                  setEnrollMode("camera");
                  setCapturedBlob(null);
                  setCapturedPreview(null);
                }}
              >
                📷 Web Camera
              </button>


              <button
                type="button"
                className={`enroll-tab ${enrollMode === "upload" ? "active" : ""
                  }`}
                onClick={() => {
                  stopCamera();
                  setEnrollMode("upload");
                  setCapturedBlob(null);
                  setCapturedPreview(null);
                }}
              >
                📁 Upload Photo
              </button>

            </div>


            {/* Camera Viewport */}
            {enrollMode === "camera" && (

              <div className="camera-section">

                <div className="camera-container">

                  {capturedPreview ? (

                    <img
                      src={capturedPreview}
                      alt="Captured Face"
                      className="camera-preview"
                    />

                  ) : (

                    <video
                      ref={videoRef}
                      playsInline
                      muted
                      className={`camera-video ${cameraActive ? "active" : ""
                        }`}
                    />

                  )}


                  {!cameraActive && !capturedPreview && (

                    <div className="camera-off">

                      <p>
                        Camera is currently off
                      </p>


                      <button
                        type="button"
                        className="camera-start-button"
                        onClick={startCamera}
                      >
                        Start Camera
                      </button>

                    </div>

                  )}

                </div>


                <div className="camera-actions">

                  {cameraActive && (

                    <>

                      <button
                        type="button"
                        className="capture-button"
                        onClick={captureFrame}
                      >
                        📸 Capture Photo
                      </button>


                      <button
                        type="button"
                        className="secondary-action-button"
                        onClick={stopCamera}
                      >
                        Stop Camera
                      </button>

                    </>

                  )}


                  {capturedPreview && (

                    <button
                      type="button"
                      className="secondary-action-button"
                      onClick={startCamera}
                    >
                      Retake Photo
                    </button>

                  )}

                </div>

              </div>

            )}

            {/* Upload Viewport */}
            {enrollMode === "upload" && (

              <div className="upload-section">

                <div className="upload-container">

                  {capturedPreview ? (

                    <img
                      src={capturedPreview}
                      alt="Uploaded Preview"
                      className="upload-preview"
                    />

                  ) : (

                    <div>

                      <p className="upload-description">
                        Select a clear frontal photo of the student.
                      </p>


                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="upload-input"
                      />

                    </div>

                  )}

                </div>

              </div>

            )}



            {enrollMessage && (

              <p
                className={`enroll-message ${enrollMessage.includes("Success")
                  ? "success"
                  : "error"
                  }`}
              >
                {enrollMessage}
              </p>

            )}



            <div className="modal-actions">

              <button
                type="button"
                className="modal-secondary-button"
                onClick={closeEnrollModal}
              >
                Close
              </button>


              <button
                type="button"
                className="modal-primary-button enroll-submit-button"
                onClick={handleEnrollSubmit}
                disabled={!capturedBlob || enrollBusy}
              >
                {enrollBusy
                  ? "Processing..."
                  : "Enroll Face"}
              </button>

            </div>


          </div>

        </div>

      )}

    </div>
  );

}

export default Students;

