/**
 * Students API service
 *
 * FastAPI endpoints:
 *   GET    /api/v1/students/                  → { students: [...], total: N }
 *   POST   /api/v1/students/                  → StudentResponse (admin only)
 *   GET    /api/v1/students/{student_id}       → StudentResponse
 *   PUT    /api/v1/students/{student_id}       → StudentResponse (admin only)
 *   DELETE /api/v1/students/{student_id}       → { message }   (admin only)
 *   GET    /api/v1/students/{student_id}/attendance → [AttendanceRecordResponse]
 *
 * StudentResponse shape:
 *   { student_id, name, department, batch, email, is_active, face_enrolled, created_at }
 *
 * StudentCreate shape:
 *   { student_id, name, department, batch, email, course_ids: [] }
 */

import { apiRequest } from "./client";

/**
 * List all students with optional filters.
 * @param {{ department?: string, batch?: string, course_id?: string }} filters
 */
export async function listStudents(filters = {}) {
  const params = new URLSearchParams();
  if (filters.department) params.set("department", filters.department);
  if (filters.batch) params.set("batch", filters.batch);
  if (filters.course_id) params.set("course_id", filters.course_id);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/api/v1/students/${qs}`);
}

/**
 * Create a new student (admin only).
 * @param {{ student_id: string, name: string, department: string, batch: string, email: string, course_ids?: string[] }} data
 */
export async function createStudent(data) {
  return apiRequest("/api/v1/students/", {
    method: "POST",
    body: data,
  });
}

/**
 * Get a single student by ID.
 * @param {string} studentId
 */
export async function getStudent(studentId) {
  return apiRequest(`/api/v1/students/${studentId}`);
}

/**
 * Update a student (admin only).
 * @param {string} studentId
 * @param {{ name?: string, department?: string, batch?: string, email?: string }} data
 */
export async function updateStudent(studentId, data) {
  return apiRequest(`/api/v1/students/${studentId}`, {
    method: "PUT",
    body: data,
  });
}

/**
 * Deactivate/delete a student (admin only).
 * @param {string} studentId
 */
export async function deleteStudent(studentId) {
  return apiRequest(`/api/v1/students/${studentId}`, {
    method: "DELETE",
  });
}

/**
 * Get a student's attendance history.
 * @param {string} studentId
 * @param {string|null} courseId
 */
export async function getStudentAttendance(studentId, courseId = null) {
  const qs = courseId ? `?course_id=${courseId}` : "";
  return apiRequest(`/api/v1/students/${studentId}/attendance${qs}`);
}
