/**
 * Courses API service
 *
 * FastAPI endpoints:
 *   GET    /api/v1/courses/                       → { courses: [...], total: N }
 *   POST   /api/v1/courses/                       → CourseResponse (admin only)
 *   GET    /api/v1/courses/{course_id}             → CourseResponse
 *   PUT    /api/v1/courses/{course_id}             → CourseResponse (admin only)
 *   DELETE /api/v1/courses/{course_id}             → { message } (admin only)
 *   GET    /api/v1/courses/{course_id}/students    → [StudentResponse]
 *   POST   /api/v1/courses/{course_id}/enroll      → EnrollmentResponse (admin only)
 *   DELETE /api/v1/courses/{course_id}/enroll/{student_id} → { message } (admin only)
 *
 * CourseResponse shape:
 *   { course_id, name, code, department, teacher_id, total_classes, created_at }
 *
 * CourseCreate shape:
 *   { name, code, department, teacher_id? }
 */

import { apiRequest } from "./client";

/**
 * List all courses.
 * @param {{ teacher_id?: string, department?: string }} filters
 */
export async function listCourses(filters = {}) {
  const params = new URLSearchParams();
  if (filters.teacher_id) params.set("teacher_id", filters.teacher_id);
  if (filters.department) params.set("department", filters.department);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiRequest(`/api/v1/courses/${qs}`);
}

/**
 * Create a new course (admin only).
 * @param {{ name: string, code: string, department: string, teacher_id?: string }} data
 */
export async function createCourse(data) {
  return apiRequest("/api/v1/courses/", {
    method: "POST",
    body: {
      course_name: data.name,
      course_code: data.code,
      department: data.department,
      section: data.section,
      teacher_id: data.teacher_id,
    },
  });
}

/**
 * Get a course by ID.
 * @param {string} courseId
 */
export async function getCourse(courseId) {
  return apiRequest(`/api/v1/courses/${courseId}`);
}

/**
 * Update a course (admin only).
 */
export async function updateCourse(courseId, data) {
  return apiRequest(`/api/v1/courses/${courseId}`, {
    method: "PUT",
    body: data,
  });
}

/**
 * Delete a course (admin only).
 */
export async function deleteCourse(courseId) {
  return apiRequest(`/api/v1/courses/${courseId}`, {
    method: "DELETE",
  });
}

/**
 * Get all students enrolled in a course.
 * @param {string} courseId
 */
export async function getCourseStudents(courseId) {
  return apiRequest(`/api/v1/courses/${courseId}/students`);
}

/**
 * Enroll a student in a course (admin only).
 * @param {string} courseId
 * @param {string} studentId
 */
export async function enrollStudent(courseId, studentId) {
  return apiRequest(`/api/v1/courses/${courseId}/enroll`, {
    method: "POST",
    body: { student_id: studentId, course_id: courseId },
  });
}

/**
 * Unenroll a student from a course (admin only).
 * @param {string} courseId
 * @param {string} studentId
 */
export async function unenrollStudent(courseId, studentId) {
  return apiRequest(`/api/v1/courses/${courseId}/enroll/${studentId}`, {
    method: "DELETE",
  });
}
