/**
 * Auth API service
 *
 * FastAPI endpoints:
 *   POST /api/v1/auth/login    → { access_token, token_type, role, name }
 *   GET  /api/v1/auth/me       → { teacher_id, name, email, role, created_at }
 *   POST /api/v1/auth/register → { teacher_id, name, email, role, created_at } (admin only)
 */

import { apiRequest } from "./client";

/**
 * Login with email and password.
 * @returns {Promise<{ access_token: string, token_type: string, role: string, name: string }>}
 */
export async function login(email, password) {
  return apiRequest("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

/**
 * Get the current authenticated user's profile.
 * @returns {Promise<{ teacher_id: string, name: string, email: string, role: string, created_at: string }>}
 */
export async function getMe() {
  return apiRequest("/api/v1/auth/me");
}

/**
 * Register a new teacher account (admin only).
 * @param {{ name: string, email: string, password: string, role: string }} data
 * @returns {Promise<{ teacher_id: string, name: string, email: string, role: string }>}
 */
export async function registerTeacher(data) {
  return apiRequest("/api/v1/auth/register", {
    method: "POST",
    body: data,
  });
}
