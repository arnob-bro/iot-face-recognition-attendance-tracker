/**
 * Attendance API service
 *
 * FastAPI endpoints:
 *   POST /api/v1/attendance/sessions                    → SessionResponse (teacher/admin)
 *   PUT  /api/v1/attendance/sessions/{id}               → SessionResponse
 *   GET  /api/v1/attendance/sessions                    → [SessionResponse]
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
 * Start a new attendance session for a course.
 * @param {{
 *   course_id: string,
 *   late_threshold_minutes?: number,
 *   device_id: string
 * }} data
 */
export async function startSession(data) {
  return apiRequest("/api/v1/attendance/sessions", {
    method: "POST",
    body: {
      course_id: data.course_id,
      late_threshold_minutes: data.late_threshold_minutes ?? 15,
      device_id: data.device_id,
    },
  });
}

/**
 * End or cancel an active session.
 * @param {string} sessionId
 * @param {"completed" | "cancelled"} status
 */
export async function endSession(sessionId, status = "completed") {
  return apiRequest(`/api/v1/attendance/sessions/${sessionId}`, {
    method: "PUT",
    body: { status },
  });
}

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

/**
 * List attendance sessions with optional filters.
 * @param {{ course_id?: string, status?: string, limit?: number }} filters
 */
export async function listSessions(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.set("course_id", filters.course_id);
  if (filters.status) params.set("status", filters.status);
  if (filters.limit) params.set("limit", filters.limit);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/api/v1/attendance/sessions${qs}`);
}

