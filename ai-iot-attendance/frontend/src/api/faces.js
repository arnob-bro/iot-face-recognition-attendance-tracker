/**
 * Face recognition / enrollment API service
 *
 * FastAPI endpoints:
 *   POST   /api/v1/faces/enroll/{student_id}   multipart/form-data (image file)
 *   GET    /api/v1/faces/status/{student_id}   → { enrolled: bool, ... }
 *   DELETE /api/v1/faces/{student_id}          → { message } (admin only)
 *   POST   /api/v1/faces/recognize             multipart/form-data (image file)
 *                                              → { matched, student_id?, confidence?, message, liveness_score? }
 *
 * recognize response when matched:
 *   { matched: true, student_id, confidence, message, liveness_score }
 *
 * recognize response when not matched:
 *   { matched: false, confidence?, message, liveness_score? }
 *
 * recognize response on AI failure (no face, liveness fail, etc.):
 *   { matched: false, message, liveness_score? }
 */

import { apiRequest } from "./client";

/**
 * Enroll a face for a student.
 * Sends a single image (ideally high quality) to generate an embedding.
 *
 * @param {string} studentId
 * @param {File|Blob} imageFile
 * @returns {Promise<{ status, message, student_id, quality }>}
 */
export async function enrollFace(studentId, imageFile) {
  const formData = new FormData();
  formData.append("file", imageFile, "face.jpg");

  return apiRequest(
    `/api/v1/faces/enroll/${studentId}`,
    {
      method: "POST",
      body: formData,
    },
    true /* isFormData — don't set Content-Type, browser sets it with boundary */
  );
}

/**
 * Check if a student has a face enrollment.
 * @param {string} studentId
 * @returns {Promise<{ enrolled: boolean, student_id: string, num_samples?: number, quality?: number }>}
 */
export async function getEnrollmentStatus(studentId) {
  return apiRequest(`/api/v1/faces/status/${studentId}`);
}

/**
 * Delete a student's face enrollment (admin only).
 * @param {string} studentId
 */
export async function deleteEnrollment(studentId) {
  return apiRequest(`/api/v1/faces/${studentId}`, {
    method: "DELETE",
  });
}

/**
 * Send an image frame for face recognition.
 *
 * @param {File|Blob} imageFile - The image to analyze
 * @param {string|null} sessionId - Optional active session ID to auto-record attendance
 * @returns {Promise<{
 *   matched: boolean,
 *   face_detected?: boolean,
 *   student_id?: string,
 *   student_name?: string,
 *   confidence?: number,
 *   message: string,
 *   liveness_score?: number,
 *   attendance?: { recorded: boolean, status?: string, record_id?: string, message?: string }
 * }>}
 */
export async function recognizeFace(imageFile, sessionId = null) {
  const formData = new FormData();
  formData.append("file", imageFile, "frame.jpg");

  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return apiRequest(
    `/api/v1/faces/recognize${qs}`,
    {
      method: "POST",
      body: formData,
    },
    true /* isFormData */
  );
}

