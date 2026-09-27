/**
 * Reports & Dashboard API service
 *
 * FastAPI endpoints:
 *   GET /api/v1/dashboard/stats              → DashboardStats
 *   GET /api/v1/reports/daily               ?course_id=&date=YYYY-MM-DD → DailyReportResponse
 *   GET /api/v1/reports/weekly              ?course_id=&start_date=     → [DailyReportResponse]
 *   GET /api/v1/reports/monthly             ?course_id=&year=&month=    → [DailyReportResponse]
 *   GET /api/v1/reports/course/{course_id}                              → [StudentAttendanceSummary]
 *   GET /api/v1/reports/student/{student_id}                            → StudentReport
 *   GET /api/v1/reports/export              ?course_id=&student_id=&start_date=&end_date= → CSV
 *
 * DashboardStats shape:
 *   { total_students, total_courses, active_sessions, today_present,
 *     today_absent, today_late, today_percentage, recent_records }
 *
 * DailyReportResponse shape:
 *   { date, course_id, course_name, total_students, present, absent, late, percentage, records }
 *
 * StudentAttendanceSummary shape:
 *   { student_id, name, total_classes, present, absent, late, percentage }
 */

import { apiRequest } from "./client";

/**
 * Get aggregated dashboard statistics.
 */
export async function getDashboardStats() {
  return apiRequest("/api/v1/dashboard/stats");
}

/**
 * Get a daily attendance report.
 * @param {string} courseId
 * @param {string} date - YYYY-MM-DD
 */
export async function getDailyReport(courseId, date) {
  return apiRequest(
    `/api/v1/reports/daily?course_id=${encodeURIComponent(courseId)}&date=${encodeURIComponent(date)}`
  );
}

/**
 * Get a weekly attendance report (7 days from start_date).
 * @param {string} courseId
 * @param {string} startDate - YYYY-MM-DD
 */
export async function getWeeklyReport(courseId, startDate) {
  return apiRequest(
    `/api/v1/reports/weekly?course_id=${encodeURIComponent(courseId)}&start_date=${encodeURIComponent(startDate)}`
  );
}

/**
 * Get a monthly attendance report.
 * @param {string} courseId
 * @param {number} year
 * @param {number} month
 */
export async function getMonthlyReport(courseId, year, month) {
  return apiRequest(
    `/api/v1/reports/monthly?course_id=${encodeURIComponent(courseId)}&year=${year}&month=${month}`
  );
}

/**
 * Get course-wide attendance summary for all students.
 * @param {string} courseId
 */
export async function getCourseReport(courseId) {
  return apiRequest(`/api/v1/reports/course/${courseId}`);
}

/**
 * Get a student's attendance summary across all courses.
 * @param {string} studentId
 */
export async function getStudentReport(studentId) {
  return apiRequest(`/api/v1/reports/student/${studentId}`);
}

/**
 * Build the CSV export URL (for direct download via anchor tag).
 * @param {{ course_id?: string, student_id?: string, start_date?: string, end_date?: string }} filters
 * @returns {string} Full URL for downloading the CSV
 */
export function getExportUrl(filters = {}) {
  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const params = new URLSearchParams();
  if (filters.course_id) params.set("course_id", filters.course_id);
  if (filters.student_id) params.set("student_id", filters.student_id);
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  return `${API_BASE}/api/v1/reports/export?${params.toString()}`;
}
