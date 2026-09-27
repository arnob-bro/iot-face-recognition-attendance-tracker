/**
 * Attendance API service
 *
 * FastAPI endpoints:
 *   GET  /api/v1/attendance/sessions/{id}               → SessionDetailResponse
 *   GET  /api/v1/attendance/sessions/active             → SessionResponse | null
 *   POST /api/v1/attendance/sessions/{id}/record        → AttendanceRecordResponse
 *   POST /api/v1/attendance/sessions/{id}/sync          → [AttendanceRecordResponse]
 *
 * SessionResponse shape:
 *   { session_id, course_id, teacher_id, session_date, start_time, end_time,
 *     late_threshold_minutes, status, present_count, late_count, absent_count }
 *
 * SessionDetailResponse shape:
 *   { session: SessionResponse, records: [AttendanceRecordResponse] }
 *
 * AttendanceRecordResponse shape:
 *   { record_id, session_id, student_id, student_name, status, confidence, detected_at, method }
 */

import { apiRequest } from "./client";

/**
 * Get a session's full details including attendance records.
 * @param {string} sessionId
 */
export async function getSession(sessionId) {
  return apiRequest(`/api/v1/attendance/sessions/${sessionId}`);
}

/**
 * Get the currently active session (optionally filtered by course).
 * @param {string|null} courseId
 */
export async function getActiveSession(courseId = null) {
  const qs = courseId ? `?course_id=${courseId}` : "";
  return apiRequest(`/api/v1/attendance/sessions/active${qs}`);
}

/**
 * Record attendance for a student in a session.
 * @param {string} sessionId
 * @param {{ student_id: string, confidence?: number, method?: string }} data
 */
export async function recordAttendance(sessionId, data) {
  return apiRequest(`/api/v1/attendance/sessions/${sessionId}/record`, {
    method: "POST",
    body: {
      student_id: data.student_id,
      confidence: data.confidence ?? 0.0,
      method: data.method ?? "face",
    },
  });
}
