/**
 * Teachers API service
 *
 * FastAPI endpoints:
 *   GET /api/v1/auth/teachers              → list all teachers (admin)
 *   GET /api/v1/auth/teachers/{teacher_id} → get teacher details (admin)
 *
 * TeacherResponse shape:
 *   {
 *     teacher_id,
 *     name,
 *     email,
 *     role,
 *     created_at
 *   }
 */

import { apiRequest } from "./client";


/**
 * List all teachers/admins.
 */
export async function listTeachers() {
  return apiRequest("/api/v1/auth/teachers");
}


/**
 * Get a teacher profile by ID.
 *
 * @param {string} teacherId
 */
export async function getTeacher(teacherId) {
  return apiRequest(`/api/v1/auth/teachers/${teacherId}`);
}

export async function registerTeacher(data) {
  return apiRequest("/api/v1/auth/register", {
    method: "POST",
    body: {
      name: data.name,
      email: data.email,
      password: data.password,
      role: "teacher",
    },
  });
}