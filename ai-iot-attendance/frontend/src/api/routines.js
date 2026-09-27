/**
 * Routines API service
 *
 * FastAPI endpoints:
 *   GET    /api/v1/routines/                 → list routines
 *   POST   /api/v1/routines/                 → create routine (admin only)
 *   GET    /api/v1/routines/{routine_id}     → get routine details
 *   PUT    /api/v1/routines/{routine_id}     → update routine (admin only)
 *   DELETE /api/v1/routines/{routine_id}     → delete routine (admin only)
 *
 * Routine shape:
 * {
 *   routine_id,
 *   course_id,
 *   teacher_id,
 *   device_id,
 *   room,
 *   day_of_week,
 *   start_time,
 *   end_time,
 *   late_threshold_minutes,
 *   is_active,
 *   created_at,
 *   updated_at
 * }
 */

import { apiRequest } from "./client";


/**
 * List routines.
 *
 * @param {{ teacher_id?: string }} filters
 */
export async function listRoutines(filters = {}) {

  const params = new URLSearchParams();

  if (filters.teacher_id) {
    params.set("teacher_id", filters.teacher_id);
  }

  const qs = params.toString()
    ? `?${params.toString()}`
    : "";

  return apiRequest(`/api/v1/routines/${qs}`);

}



/**
 * Create a routine (admin only).
 *
 * @param {{
 *   course_id: string,
 *   teacher_id: string,
 *   device_id?: string,
 *   room?: string,
 *   day_of_week?: number,
 *   start_time: string,
 *   end_time: string,
 *   late_threshold_minutes?: number,
 *   is_active?: boolean
 * }} data
 */
export async function createRoutine(data) {

  return apiRequest("/api/v1/routines/", {
    method: "POST",
    body: data,
  });

}



/**
 * Get a single routine.
 *
 * @param {string} routineId
 */
export async function getRoutine(routineId) {

  return apiRequest(`/api/v1/routines/${routineId}`);

}



/**
 * Update a routine (admin only).
 *
 * @param {string} routineId
 * @param {object} data
 */
export async function updateRoutine(routineId, data) {

  return apiRequest(`/api/v1/routines/${routineId}`, {
    method: "PUT",
    body: data,
  });

}



/**
 * Delete a routine (admin only).
 *
 * @param {string} routineId
 */
export async function deleteRoutine(routineId) {

  return apiRequest(`/api/v1/routines/${routineId}`, {
    method: "DELETE",
  });

}