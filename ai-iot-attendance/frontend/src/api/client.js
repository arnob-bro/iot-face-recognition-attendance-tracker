/**
 * API client — base fetch wrapper for FastAPI backend.
 *
 * Authentication: Bearer token stored in localStorage.
 * The FastAPI backend expects: Authorization: Bearer <token>
 *
 * Base URL: VITE_API_URL env variable (defaults to http://localhost:8000)
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/** Retrieve the stored JWT token */
export function getToken() {
  return localStorage.getItem("auth_token");
}

/** Store a JWT token after login */
export function setToken(token) {
  localStorage.setItem("auth_token", token);
}

/** Remove the JWT token (logout) */
export function clearToken() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
}

/** Store user info */
export function setUserInfo(user) {
  localStorage.setItem("auth_user", JSON.stringify(user));
}

/** Retrieve stored user info */
export function getUserInfo() {
  try {
    const raw = localStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Core API request function.
 *
 * @param {string} path - API path, e.g. "/api/v1/students/"
 * @param {object} options - fetch options (method, body, headers, etc.)
 * @param {boolean} isFormData - if true, do NOT set Content-Type (let browser set multipart boundary)
 */
export async function apiRequest(path, options = {}, isFormData = false) {
  const { body, headers = {}, ...rest } = options;

  const token = getToken();

  const requestHeaders = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(body !== undefined && !isFormData
      ? { "Content-Type": "application/json" }
      : {}),
    ...headers,
  };

  const response = await fetch(`${API_BASE}${path}`, {
    headers: requestHeaders,
    body: body !== undefined
      ? (isFormData ? body : JSON.stringify(body))
      : undefined,
    ...rest,
  });

  // Handle 401 — token expired or invalid
  if (response.status === 401) {
    clearToken();
    // Redirect to home if not already there
    if (window.location.pathname !== "/") {
      window.location.href = "/";
    }
    throw new Error("Session expired. Please log in again.");
  }

  let payload = null;
  const contentType = response.headers.get("content-type") || "";

  try {
    if (contentType.includes("application/json")) {
      payload = await response.json();
    } else {
      payload = await response.text();
    }
  } catch {
    payload = null;
  }

  if (!response.ok) {
    // FastAPI returns { detail: "..." } for errors
    const detail = payload?.detail;
    let message;

    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      // Pydantic validation errors: array of { loc, msg, type }
      message = detail.map((e) => e.msg).join("; ");
    } else if (response.status === 403) {
      message = "You do not have permission to perform this action.";
    } else if (response.status === 404) {
      message = "The requested resource was not found.";
    } else if (response.status === 409) {
      message = payload?.detail || "A conflict occurred (duplicate data).";
    } else if (response.status >= 500) {
      message = "The server encountered an error. Please try again later.";
    } else {
      message = "Request failed.";
    }

    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}
