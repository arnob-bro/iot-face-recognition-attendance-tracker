import "./Attendance.css";
import { useEffect, useState, useRef, useCallback } from "react";
import { getSession, getActiveSession, recordAttendance } from "../api/attendance";
import { listCourses, getCourseStudents } from "../api/courses";
import { recognizeFace } from "../api/faces";


function Attendance() {
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [selectedSessionData, setSelectedSessionData] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [courses, setCourses] = useState([]);

  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [manualAttendance, setManualAttendance] = useState({});


  // Status & error messages
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  // --- AI Camera & Testing Console State ---
  const [testMode, setTestMode] = useState("camera"); // "camera" | "upload"
  const [cameraActive, setCameraActive] = useState(false);
  const [autoScan, setAutoScan] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedPreview, setUploadedPreview] = useState(null);

  // AI Results
  const [aiResult, setAiResult] = useState(null);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const autoScanTimerRef = useRef(null);

  // --- Load Initial Data ---
  const loadData = async () => {
    try {
      const [activeData, coursesData] = await Promise.all([
        getActiveSession().catch(() => null),
        listCourses().catch(() => ({ courses: [] })),
      ]);

      setActiveSession(activeData);
      setCourses(coursesData.courses || []);

      if (activeData?.course_id) {
        await loadEnrolledStudents(activeData.course_id);
      }

      if (activeData) {
        setSelectedSessionId(activeData.session_id);
        await loadSessionDetails(activeData.session_id);
      }

    } catch (err) {
      setMessage(err.message || "Failed to load attendance sessions.");
    }
  };

  const loadSessionDetails = async (id) => {
    if (!id) {
      setSelectedSessionData(null);
      return;
    }
    try {
      const details = await getSession(id);
      setSelectedSessionData(details);
    } catch (err) {
      setMessage(`Failed to load session details: ${err.message}`);
    }
  };

  useEffect(() => {
    loadData();
    return () => {
      stopCamera();
      stopAutoScan();
    };
  }, []);

  const handleSelectSession = async (id) => {
    setSelectedSessionId(id);
    await loadSessionDetails(id);
  };


  const loadEnrolledStudents = async (courseId) => {
    if (!courseId) return;

    try {
      const data = await getCourseStudents(courseId);
      setEnrolledStudents(data);
    } catch (err) {
      setMessage("Failed to load enrolled students.");
    }
  };


  const handleManualAttendance = async (studentId) => {
    if (!activeSession) return;

    try {
      const response = await recordAttendance(
        activeSession.session_id,
        {
          student_id: studentId,
          confidence: 0,
          method: "manual",
        }
      );

      // Backend decides present/late
      setManualAttendance((prev) => ({
        ...prev,
        [studentId]: response.status,
      }));

      await loadSessionDetails(activeSession.session_id);

    } catch (err) {
      setMessage(err.message || "Failed to mark attendance.");
    }
  };





  // --- Camera Operations ---
  const startCamera = async () => {
    setMessage("");
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
      setMessage(`Camera error: ${err.message}. You can also use the 'Upload Image' tab.`);
    }
  };

  const stopCamera = () => {
    stopAutoScan();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const captureFrameBlob = () => {
    if (!videoRef.current || !cameraActive) return null;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.9);
    });
  };

  // --- Send Image to Backend for Recognition ---
  const processImageForRecognition = async (blob) => {
    if (!blob) return;
    setScanning(true);

    try {
      const targetSessionId = activeSession?.session_id || null;
      const res = await recognizeFace(blob, targetSessionId);
      setAiResult(res);

      // If attendance was recorded, refresh the session table!
      if (res.attendance?.recorded && targetSessionId) {
        await loadSessionDetails(targetSessionId);
      }
    } catch (err) {
      setAiResult({
        matched: false,
        face_detected: false,
        message: err.message || "Failed to reach AI service.",
      });
    } finally {
      setScanning(false);
    }
  };

  const handleScanOnce = async () => {
    if (testMode === "camera") {
      if (!cameraActive) {
        await startCamera();
      }
      const blob = await captureFrameBlob();
      if (blob) {
        await processImageForRecognition(blob);
      }
    } else {
      if (uploadedFile) {
        await processImageForRecognition(uploadedFile);
      } else {
        setMessage("Please select an image file first.");
      }
    }
  };

  // --- Auto-Scan Toggle ---
  const toggleAutoScan = () => {
    if (autoScan) {
      stopAutoScan();
    } else {
      if (!cameraActive) startCamera();
      setAutoScan(true);
      autoScanTimerRef.current = setInterval(async () => {
        const blob = await captureFrameBlob();
        if (blob) {
          processImageForRecognition(blob);
        }
      }, 2500);
    }
  };

  const stopAutoScan = () => {
    setAutoScan(false);
    if (autoScanTimerRef.current) {
      clearInterval(autoScanTimerRef.current);
      autoScanTimerRef.current = null;
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setUploadedPreview(URL.createObjectURL(file));
      setAiResult(null);
    }
  };

  // Session counts from selectedSessionData
  const currentSession = selectedSessionData?.session;
  const records = selectedSessionData?.records || [];

  const presentCount =
    currentSession?.present_count ??
    records.filter((r) => r.status?.toLowerCase() === "present").length;
  const lateCount =
    currentSession?.late_count ??
    records.filter((r) => r.status?.toLowerCase() === "late").length;
  const absentCount =
    currentSession?.absent_count ??
    records.filter((r) => r.status?.toLowerCase() === "absent").length;

  const activeCourseName =
    courses.find((c) => c.course_id === activeSession?.course_id)?.course_name ||
    activeSession?.course_id;

  return (
    <div className="attendance-page">
      {/* Header */}
      <div className="attendance-header">
        <div>
          <p className="attendance-subtitle">Live AI Attendance</p>
          <h1>Attendance & Face Recognition</h1>
          <p className="attendance-description">
            Test real-time face detection, anti-spoofing liveness, and automated attendance logging.
          </p>
        </div>

        <div className="attendance-session-status">
          {activeSession && (
            <span className="session-live-badge">
              Live Session Running
            </span>
          )}
        </div>


      </div>

      {/* Active Session Alert Banner */}
      {activeSession ? (
        <div
          style={{
            background: "#fff",
            borderLeft: "6px solid #15803d",
            padding: "16px 20px",
            borderRadius: "10px",
            marginBottom: "24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          }}
        >
          <div>
            <span
              style={{
                display: "inline-block",
                background: "#dcfce7",
                color: "#15803d",
                fontSize: "12px",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "6px",
                textTransform: "uppercase",
                marginBottom: "4px",
              }}
            >
              ● Live Session Active
            </span>
            <h3 style={{ margin: "4px 0", fontSize: "17px" }}>
              Course: {activeCourseName} · Late threshold: {activeSession.late_threshold_minutes} min
            </h3>
            <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
              Started: {new Date(activeSession.start_time).toLocaleTimeString()} · Session ID:{" "}
              <code>{activeSession.session_id}</code>
            </p>
          </div>

          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: "13px", color: "#64748b", display: "block" }}>
              Recognized faces are automatically recorded
            </span>
          </div>
        </div>
      ) : (
        <div
          style={{
            background: "#fff",
            borderLeft: "6px solid #CB2957",
            padding: "14px 20px",
            borderRadius: "10px",
            marginBottom: "24px",
            fontSize: "15px",
            color: "#475569",
            fontWeight: "600",
          }}
        >
          No active session currently running. The scheduler will automatically create sessions according to the configured routine.
        </div>
      )}

      {/* Statistics Cards */}
      <div className="attendance-stats">
        <div className="attendance-stat-card">
          <div className="attendance-stat-icon present-stat-icon">✓</div>
          <div>
            <p>Present</p>
            <h2>{presentCount}</h2>
          </div>
        </div>
        <div className="attendance-stat-card">
          <div className="attendance-stat-icon late-stat-icon">◷</div>
          <div>
            <p>Late</p>
            <h2>{lateCount}</h2>
          </div>
        </div>
        <div className="attendance-stat-card">
          <div className="attendance-stat-icon absent-stat-icon">✕</div>
          <div>
            <p>Absent</p>
            <h2>{absentCount}</h2>
          </div>
        </div>
        <div className="attendance-stat-card">
          <div className="attendance-stat-icon overall-stat-icon">◎</div>
          <div>
            <p>Total Records</p>
            <h2>{records.length}</h2>
          </div>
        </div>
      </div>

      {message && (
        <p
          className="attendance-description"
          style={{
            fontWeight: 600,
            marginBottom: "16px",
            color: message.includes("success") || message.includes("Started") ? "#15803d" : "#CB2957",
          }}
        >
          {message}
        </p>
      )}

      {/* ================= AI TESTING CONSOLE (WEBCAM & DIAGNOSTICS) ================= */}
      <div
        style={{
          background: "#fff",
          border: "2px solid #DDDDDD",
          borderRadius: "14px",
          padding: "24px",
          marginBottom: "28px",
          boxShadow: "0 4px 16px rgba(0,0,0,0.06)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid #eee",
            paddingBottom: "16px",
            marginBottom: "20px",
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: "20px" }}>AI Face Recognition & Liveness Console</h2>
            <p style={{ margin: "4px 0 0", fontSize: "14px", color: "#64748b" }}>
              Captures image from PC camera or file upload, passes to FastAPI pipeline (SCRFD + MiniFASNet + ArcFace).
            </p>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              type="button"
              onClick={() => {
                setTestMode("camera");
                setUploadedFile(null);
                setUploadedPreview(null);
              }}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: testMode === "camera" ? "#CB2957" : "#ccc",
                background: testMode === "camera" ? "#fdf2f4" : "#fff",
                color: testMode === "camera" ? "#CB2957" : "#333",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              📷 PC Camera
            </button>
            <button
              type="button"
              onClick={() => {
                stopCamera();
                setTestMode("upload");
              }}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: testMode === "upload" ? "#CB2957" : "#ccc",
                background: testMode === "upload" ? "#fdf2f4" : "#fff",
                color: testMode === "upload" ? "#CB2957" : "#333",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              📁 Upload Image
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "24px" }}>
          {/* Left Column: Camera / Image Capture Viewport */}
          <div>
            {testMode === "camera" ? (
              <div>
                <div
                  style={{
                    width: "100%",
                    height: "340px",
                    background: "#000",
                    borderRadius: "10px",
                    overflow: "hidden",
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <video
                    ref={videoRef}
                    playsInline
                    muted
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: cameraActive ? "block" : "none",
                    }}
                  />

                  {!cameraActive && (
                    <div style={{ textAlign: "center", color: "#aaa" }}>
                      <p style={{ margin: "0 0 12px" }}>Computer camera is inactive</p>
                      <button
                        type="button"
                        onClick={startCamera}
                        style={{
                          padding: "10px 20px",
                          borderRadius: "8px",
                          border: "none",
                          background: "#CB2957",
                          color: "#fff",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        Enable Camera
                      </button>
                    </div>
                  )}

                  {scanning && (
                    <div
                      style={{
                        position: "absolute",
                        top: "12px",
                        left: "12px",
                        background: "rgba(0,0,0,0.7)",
                        color: "#fff",
                        padding: "4px 10px",
                        borderRadius: "6px",
                        fontSize: "12px",
                        fontWeight: 600,
                      }}
                    >
                      Analyzing frame...
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", gap: "10px", marginTop: "14px" }}>
                  {cameraActive && (
                    <>
                      <button
                        type="button"
                        onClick={handleScanOnce}
                        disabled={scanning}
                        style={{
                          flex: 1,
                          padding: "10px",
                          borderRadius: "8px",
                          border: "none",
                          background: "#CB2957",
                          color: "#fff",
                          fontWeight: 600,
                          cursor: scanning ? "not-allowed" : "pointer",
                        }}
                      >
                        {scanning ? "Processing..." : "Scan Face Now"}
                      </button>

                      <button
                        type="button"
                        onClick={toggleAutoScan}
                        style={{
                          padding: "10px 18px",
                          borderRadius: "8px",
                          border: "1px solid #ccc",
                          background: autoScan ? "#fee2e2" : "#f1f5f9",
                          color: autoScan ? "#b91c1c" : "#333",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {autoScan ? "■ Stop Auto-Scan" : "▶ Auto-Scan Loop"}
                      </button>

                      <button
                        type="button"
                        onClick={stopCamera}
                        style={{
                          padding: "10px 16px",
                          borderRadius: "8px",
                          border: "1px solid #ccc",
                          background: "#fff",
                          cursor: "pointer",
                        }}
                      >
                        Turn Off
                      </button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div>
                <div
                  style={{
                    width: "100%",
                    height: "340px",
                    border: "2px dashed #ccc",
                    borderRadius: "10px",
                    background: "#f9fafb",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                  }}
                >
                  {uploadedPreview ? (
                    <img
                      src={uploadedPreview}
                      alt="Uploaded Preview"
                      style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }}
                    />
                  ) : (
                    <div style={{ textAlign: "center", padding: "20px" }}>
                      <p style={{ margin: "0 0 10px", color: "#64748b" }}>
                        Select a face image file to test AI detection and recognition
                      </p>
                      <input type="file" accept="image/*" onChange={handleFileUpload} />
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", gap: "10px", marginTop: "14px" }}>
                  <button
                    type="button"
                    onClick={handleScanOnce}
                    disabled={!uploadedFile || scanning}
                    style={{
                      flex: 1,
                      padding: "10px",
                      borderRadius: "8px",
                      border: "none",
                      background: "#CB2957",
                      color: "#fff",
                      fontWeight: 600,
                      cursor: uploadedFile && !scanning ? "pointer" : "not-allowed",
                      opacity: uploadedFile && !scanning ? 1 : 0.6,
                    }}
                  >
                    {scanning ? "Processing..." : "Analyze Selected Image"}
                  </button>
                  {uploadedFile && (
                    <button
                      type="button"
                      onClick={() => {
                        setUploadedFile(null);
                        setUploadedPreview(null);
                        setAiResult(null);
                      }}
                      style={{
                        padding: "10px 16px",
                        borderRadius: "8px",
                        border: "1px solid #ccc",
                        background: "#fff",
                        cursor: "pointer",
                      }}
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Real-time AI Results Card */}
          <div>
            <div
              style={{
                background: "#fafafa",
                border: "1px solid #e5e7eb",
                borderRadius: "10px",
                padding: "20px",
                height: "340px",
                boxSizing: "border-box",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ margin: 0, fontSize: "16px", color: "#111827" }}>Recognition Output</h3>
                  {aiResult ? (
                    <span
                      style={{
                        fontSize: "12px",
                        fontWeight: 700,
                        padding: "3px 8px",
                        borderRadius: "6px",
                        background: aiResult.matched ? "#dcfce7" : "#fee2e2",
                        color: aiResult.matched ? "#15803d" : "#b91c1c",
                        textTransform: "uppercase",
                      }}
                    >
                      {aiResult.matched ? "Matched" : "No Match"}
                    </span>
                  ) : (
                    <span style={{ fontSize: "12px", color: "#94a3b8" }}>Waiting for scan...</span>
                  )}
                </div>

                <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
                  {/* Face Detected */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Face Detected:</span>
                    <strong>
                      {aiResult ? (aiResult.face_detected !== false ? "YES" : "NO") : "—"}
                    </strong>
                  </div>

                  {/* Student Name */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Student Name:</span>
                    <strong style={{ color: aiResult?.student_name ? "#111827" : "#64748b" }}>
                      {aiResult?.student_name || (aiResult?.matched ? aiResult?.student_id : "—")}
                    </strong>
                  </div>

                  {/* Student ID */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Student ID:</span>
                    <code>{aiResult?.student_id || "—"}</code>
                  </div>

                  {/* Confidence */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Recognition Confidence:</span>
                    <strong>
                      {typeof aiResult?.confidence === "number"
                        ? `${(aiResult.confidence * 100).toFixed(1)}%`
                        : "—"}
                    </strong>
                  </div>

                  {/* Liveness */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Liveness Anti-Spoof:</span>
                    <strong>
                      {typeof aiResult?.liveness_score === "number" ? (
                        aiResult.liveness_score >= 0.5 ? (
                          <span style={{ color: "#15803d" }}>
                            PASS ({(aiResult.liveness_score * 100).toFixed(0)}%)
                          </span>
                        ) : (
                          <span style={{ color: "#b91c1c" }}>
                            FAIL ({(aiResult.liveness_score * 100).toFixed(0)}%)
                          </span>
                        )
                      ) : (
                        "—"
                      )}
                    </strong>
                  </div>

                  {/* Attendance Logged */}
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "#64748b" }}>Attendance Status:</span>
                    <strong>
                      {aiResult?.attendance ? (
                        aiResult.attendance.recorded ? (
                          <span style={{ color: "#15803d", textTransform: "uppercase" }}>
                            ✓ {aiResult.attendance.status || "Recorded"}
                          </span>
                        ) : (
                          <span style={{ color: "#b91c1c" }}>
                            {aiResult.attendance.message || "Failed"}
                          </span>
                        )
                      ) : activeSession ? (
                        <span style={{ color: "#94a3b8" }}>Session Ready</span>
                      ) : (
                        <span style={{ color: "#94a3b8" }}>No active session</span>
                      )}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Message from backend */}
              <div
                style={{
                  background: "#fff",
                  padding: "10px",
                  borderRadius: "6px",
                  border: "1px solid #e2e8f0",
                  fontSize: "12px",
                  color: "#475569",
                  wordBreak: "break-word",
                }}
              >
                <strong>Backend Msg: </strong>
                {aiResult?.message || "Submit a frame to inspect backend AI pipeline diagnostics."}
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ================= MANUAL ATTENDANCE TABLE ================= */}
      {activeSession && (
        <div className="manual-attendance-card">

          <h2>
            Manual Attendance
          </h2>


          <table className="manual-attendance-table">

            <thead>
              <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>


            <tbody>

              {enrolledStudents.map((student) => (
                <tr key={student.student_id}>

                  <td>
                    {student.student_id}
                  </td>


                  <td>
                    {student.name}
                  </td>


                  <td>
                    {student.department}
                  </td>


                  <td>
                    <span
                      className={`manual-status ${manualAttendance[student.student_id] || "absent"
                        }`}
                    >
                      {manualAttendance[student.student_id] || "Absent"}
                    </span>
                  </td>


                  <td>

                    <div className="manual-action-buttons">

                      <button
                        className="manual-attendance-btn"
                        onClick={() =>
                          handleManualAttendance(student.student_id)
                        }
                      >
                        Mark Attendance
                      </button>

                    </div>

                  </td>


                </tr>
              ))}

            </tbody>

          </table>

        </div>
      )}


    </div>
  );
}

export default Attendance;