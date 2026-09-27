# AI-IoT Attendance System

This repository contains a FastAPI attendance backend and a separate Raspberry Pi camera client. The backend stores users, students, courses, face embeddings, attendance sessions, and reports in Firebase Firestore. The AI pipeline runs face detection, liveness checking, and recognition; mock AI is enabled by default for development.

## Project structure

- `backend/` - FastAPI application, Firebase services, AI pipeline, and tests
- `rpi-client/` - camera client with API integration, offline SQLite queue, and optional ESP32 serial bridge
- `models/` - model storage used by the backend when real AI is enabled

## Prerequisites

- Python 3.11 or newer
- A Firebase project with Firestore enabled for live use
- Visual Studio C++ Build Tools on Windows if installing `insightface` requires compilation
- Firebase CLI only when using the local Firestore emulator

## Firebase configuration

The emulator is optional. Choose one of these modes.

### Live Firebase project

1. In Firebase Console, enable Firestore.
2. In Project Settings > Service accounts, generate a private key.
3. Save the downloaded file as `backend/firebase-credentials.json`.
4. Create `backend/.env` with at least:

```dotenv
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
JWT_SECRET_KEY=replace-with-a-long-random-secret
USE_MOCK_AI=true
LIVENESS_ENABLED=true
```

Run the backend from `backend/` so the relative credentials path resolves correctly. Do not commit the credentials file; it is ignored by Git.

### Local Firestore emulator

Use this mode for isolated development and tests. It does not require a service-account file.

From the repository root, start Firestore in one terminal:

```powershell
firebase emulators:start --only firestore --project test-project --host 127.0.0.1
```

In the backend terminal, set the emulator host before starting the server or tests:

```powershell
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
```

The emulator must remain running while the backend or test suite uses Firestore.

## Run the backend

From `backend/`:
in windows

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

in raspberry pi linux terminal

```powershell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application bootstraps the admin account on startup. Defaults are `admin@university.edu` and `changeme123`; set `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_NAME` in `.env` for a real deployment.

Useful URLs:

- Health check: http://localhost:8000/health
- OpenAPI documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Run backend tests

Tests use Firestore. Start the emulator as described above, set `FIRESTORE_EMULATOR_HOST`, then run from `backend/`:

```powershell
python -m pytest tests/ -q
```

The verified local result is 16 passed and 3 skipped. Tests clear their Firestore collections before running.

## Seed mock data

With the Firestore emulator running, seed the demo teachers, students, courses, enrollments, device, inactive routines, completed sessions, and attendance records from `backend/`:

```powershell
$env:FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
python mock_data.py
```

The script upserts deterministic mock document IDs and does not clear existing collections. It refuses to write to a live Firebase project unless `--allow-live` is explicitly provided. Demo login credentials are printed after a successful seed; use them only with mock data.

To generate face embeddings from images, enable real AI and provide the model image folder. Images must identify one of the seeded student IDs, either as filenames such as `MOCK001_1.jpg` or inside a student subfolder such as `face-images/MOCK001/photo.jpg`. Supported image formats are `.jpg`, `.jpeg`, `.png`, `.bmp`, and `.webp`.

```powershell
$env:USE_MOCK_AI="false"
python mock_data.py --face-embeddings-dir "C:\path\to\face-images"
```

The seeder uses the configured InsightFace detector and ArcFace recognizer, combines usable images for each student into one normalized representative embedding, and saves it in the same Base64 float32 format used by face enrollment. It skips unreadable images and images without a usable face. Keep `USE_MOCK_AI=false` and ensure the InsightFace dependencies and models are available; the script refuses to write synthetic mock-recognizer vectors as face enrollments. Without `--face-embeddings-dir`, it does not create or update any face-embedding records.

## API workflow

Use the interactive documentation at `/docs`:

1. Log in with `POST /api/v1/auth/login` and authorize with the returned bearer token.
2. Register each Raspberry Pi with `POST /api/v1/devices` and save the returned secret securely.
3. Create a student with `POST /api/v1/students/`.
4. Create a course with `POST /api/v1/courses/` and enroll the student.
5. As an admin, create a weekly class routine with `POST /api/v1/routines/`, including the course, schedule, and assigned `device_id`.
6. Configure the Pi with that device ID and secret; during the routine window it polls the automatically generated session assigned to that device.
7. Enroll a face with `POST /api/v1/faces/enroll/{student_id}`.
8. Recognize a frame with `POST /api/v1/faces/recognize`.
9. Review attendance and reports through the attendance, dashboard, and reports endpoints.

Recognition responses include a confidence value and, when liveness is enabled, a `liveness_score`. Face enrollment currently stores one representative sample per upload.

## API endpoint reference

The backend exposes all routes under `/api/v1`, and authorization is enforced through JWT claims. The role checks are:

- `admin`: full admin access
- `teacher`: teacher-level operations
- `student`: student login and self-service access to their own profile and attendance history
- `device`: Raspberry Pi device access only
- any authenticated user: logged-in user or device token accepted by `get_current_user`

### Authentication and token usage

- Human users log in via `POST /api/v1/auth/login`.
- Students log in via `POST /api/v1/students/login` using their student ID and password.
- Admin/teacher accounts are created by admin users only via `POST /api/v1/auth/register`.
- Raspberry Pi devices log in via `POST /api/v1/devices/login` using `device_id` and `device_secret`.
- All protected routes require the `Authorization: Bearer <token>` header.

### Public / health endpoints

| Method | Endpoint                 | Auth required | Allowed roles | Required data                   | Description                                               |
| ------ | ------------------------ | ------------- | ------------- | ------------------------------- | --------------------------------------------------------- |
| GET    | `/health`                | No            | Public        | None                            | Backend health check.                                     |
| POST   | `/api/v1/auth/login`     | No            | Public        | `email`, `password`             | Login as admin or teacher and receive a JWT.              |
| POST   | `/api/v1/students/login` | No            | Public        | Query: `student_id`, `password` | Login as a student and receive a student JWT.             |
| POST   | `/api/v1/devices/login`  | No            | Public        | `device_id`, `device_secret`    | Login a registered Raspberry Pi and receive a device JWT. |

### Authentication and profile endpoints

| Method | Endpoint                             | Auth required | Allowed roles                | Required data                                                       | Description                                                              |
| ------ | ------------------------------------ | ------------- | ---------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| POST   | `/api/v1/auth/register`              | Yes           | `admin`                      | `name`, `email`, `password`, optional `role` (`teacher` or `admin`) | Create a new teacher/admin account.                                      |
| GET    | `/api/v1/auth/me`                    | Yes           | `admin`, `teacher`, `device` | None                                                                | Returns the authenticated user's profile.                                |
| GET    | `/api/v1/auth/teachers`              | Yes           | `admin`, `teacher`           | None                                                                | `admin` sees all teachers/admins; `teacher` sees only their own profile. |
| GET    | `/api/v1/auth/teachers/{teacher_id}` | Yes           | `admin`, `teacher`           | Path: `teacher_id`                                                  | `admin` can view any teacher; `teacher` can view only their own profile. |
| GET    | `/api/v1/devices/me`                 | Yes           | `device`                     | None                                                                | Returns the device profile for the current device token.                 |
| GET    | `/api/v1/dashboard/stats`            | Yes           | `admin`, `teacher`, `device` | None                                                                | Returns dashboard stats for the current user.                            |

### Student management endpoints

| Method | Endpoint                                   | Auth required | Allowed roles                          | Required data                                                                     | Description                                                               |
| ------ | ------------------------------------------ | ------------- | -------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| GET    | `/api/v1/students/`                        | Yes           | `admin`, `teacher`                     | Query: `department` (optional), `batch` (optional), `course_id` (optional)        | List students with optional filters.                                      |
| POST   | `/api/v1/students/`                        | Yes           | `admin`                                | Body: `student_id`, `name`, `department`, `batch`, `email`, optional `course_ids` | Create a student record.                                                  |
| GET    | `/api/v1/students/me`                      | Yes           | `student`                              | None                                                                              | Fetch the authenticated student's own profile.                            |
| POST   | `/api/v1/students/me/change-password`      | Yes           | `student`                              | Body: `current_password`, `new_password`                                          | Change the authenticated student's password.                              |
| GET    | `/api/v1/students/{student_id}`            | Yes           | `admin`, `teacher`, matching `student` | Path: `student_id`                                                                | Fetch a student; student tokens can access only their own record.         |
| PUT    | `/api/v1/students/{student_id}`            | Yes           | `admin`                                | Path: `student_id`; body: any of `name`, `department`, `batch`, `email`           | Update student details.                                                   |
| DELETE | `/api/v1/students/{student_id}`            | Yes           | `admin`                                | Path: `student_id`                                                                | Deactivate a student.                                                     |
| GET    | `/api/v1/students/{student_id}/attendance` | Yes           | `admin`, `teacher`, matching `student` | Path: `student_id`; query: `course_id` (optional)                                 | Get attendance history; student tokens can access only their own records. |

When `POST /api/v1/students/` omits `password`, the service creates a temporary password using the pattern `<student_id>-changeme`, stores only its bcrypt hash, and returns the temporary value once with `must_change_password: true`. Supplying a password stores its bcrypt hash and sets `must_change_password: false`. Student login currently takes `student_id` and `password` as query parameters.

### Course management endpoints

| Method | Endpoint                                          | Auth required | Allowed roles      | Required data                                                                        | Description                             |
| ------ | ------------------------------------------------- | ------------- | ------------------ | ------------------------------------------------------------------------------------ | --------------------------------------- |
| GET    | `/api/v1/courses/`                                | Yes           | `admin`, `teacher` | Query: `teacher_id` (optional), `department` (optional)                              | List courses.                           |
| POST   | `/api/v1/courses/`                                | Yes           | `admin`            | Body: `course_code`, `course_name`, `department`, `section`, `teacher_id`            | Create a course.                        |
| GET    | `/api/v1/courses/{course_id}`                     | Yes           | `admin`, `teacher` | Path: `course_id`                                                                    | Get one course by ID.                   |
| PUT    | `/api/v1/courses/{course_id}`                     | Yes           | `admin`            | Path: `course_id`; body: any of `course_name`, `department`, `section`, `teacher_id` | Update a course.                        |
| DELETE | `/api/v1/courses/{course_id}`                     | Yes           | `admin`            | Path: `course_id`                                                                    | Delete a course and its enrollments.    |
| GET    | `/api/v1/courses/{course_id}/students`            | Yes           | `admin`, `teacher` | Path: `course_id`                                                                    | List all students enrolled in a course. |
| POST   | `/api/v1/courses/{course_id}/enroll`              | Yes           | `admin`            | Path: `course_id`; body: `student_id`, `course_id`                                   | Enroll a student in a course.           |
| DELETE | `/api/v1/courses/{course_id}/enroll/{student_id}` | Yes           | `admin`            | Path: `course_id`, `student_id`                                                      | Unenroll a student from a course.       |

### Attendance session endpoints

| Method | Endpoint                                          | Auth required | Allowed roles           | Required data                                                           | Description                                                                                 |
| ------ | ------------------------------------------------- | ------------- | ----------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| GET    | `/api/v1/attendance/sessions/active`              | Yes           | Any authenticated token | Query: `course_id` (optional)                                           | Get the active session; device tokens are filtered to their assigned device.                |
| GET    | `/api/v1/attendance/sessions/{session_id}`        | Yes           | `admin`, `teacher`      | Path: `session_id`                                                      | Fetch a session and all attendance records.                                                 |
| POST   | `/api/v1/attendance/sessions/{session_id}/record` | Yes           | Any authenticated token | Path: `session_id`; body: `student_id`, `confidence`, `method`          | Record one attendance event; device tokens are checked against the session device.          |
| POST   | `/api/v1/attendance/sessions/{session_id}/sync`   | Yes           | Any authenticated token | Path: `session_id`; body: `records: [{student_id, confidence, method}]` | Bulk-sync offline attendance records; device tokens are checked against the session device. |

Attendance sessions are created and completed only by the background routine scheduler; there is no public endpoint to manually create, complete, cancel, or delete a session. The scheduler checks routines every 30 seconds by default, starts a session during its scheduled window, and completes it at or after the end time. Set `ROUTINE_TIMEZONE` (default `UTC`) and `ROUTINE_SCHEDULER_INTERVAL_SECONDS` in the backend environment to configure its clock and polling interval. On startup, it reconciles sessions for windows currently in progress and completes overdue active routine sessions.

Run one backend worker while using this in-process scheduler. Each worker starts its own scheduler loop; the current implementation does not use a distributed leader lock.

### Class routine endpoints

| Method | Endpoint                        | Auth required | Allowed roles / behavior                                                  | Required data                                                                                                                                 | Description                                       |
| ------ | ------------------------------- | ------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| GET    | `/api/v1/routines/`             | Yes           | Authenticated; admin sees all, other tokens are filtered by their user ID | None                                                                                                                                          | List routines.                                    |
| POST   | `/api/v1/routines/`             | Yes           | `admin`                                                                   | Body: `course_id`, `teacher_id`, `start_time`, `end_time`; optional `device_id`, `room`, `day_of_week`, `late_threshold_minutes`, `is_active` | Create a routine; overlapping slots are rejected. |
| GET    | `/api/v1/routines/{routine_id}` | Yes           | Authenticated; teacher is restricted to their own routine                 | Path: `routine_id`                                                                                                                            | Fetch one routine.                                |
| PUT    | `/api/v1/routines/{routine_id}` | Yes           | `admin`                                                                   | Path: `routine_id`; body: any routine fields                                                                                                  | Update a routine; overlap validation is repeated. |
| DELETE | `/api/v1/routines/{routine_id}` | Yes           | `admin`                                                                   | Path: `routine_id`                                                                                                                            | Delete a routine.                                 |

`day_of_week` uses Python weekday numbering (`0` = Monday through `6` = Sunday); `start_time` and `end_time` use `HH:MM`. The read routes accept any authenticated token; teacher ownership is enforced on an individual routine read, while routine administration is intended for admins and teachers.

### Face enrollment and recognition endpoints

| Method | Endpoint                            | Auth required | Allowed roles                | Required data                            | Description                                                                              |
| ------ | ----------------------------------- | ------------- | ---------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------- |
| POST   | `/api/v1/faces/enroll/{student_id}` | Yes           | `admin`                      | Path: `student_id`; file upload (`file`) | Upload a face image to enroll a student.                                                 |
| GET    | `/api/v1/faces/status/{student_id}` | Yes           | `admin`, `teacher`, `device` | Path: `student_id`                       | Check whether a student has an enrollment record.                                        |
| DELETE | `/api/v1/faces/{student_id}`        | Yes           | `admin`                      | Path: `student_id`                       | Remove a student's face enrollment.                                                      |
| POST   | `/api/v1/faces/recognize`           | Yes           | `admin`, `teacher`, `device` | File upload (`file`)                     | Submit a camera frame for face recognition. Returns matched student data and confidence. |

### Reporting endpoints

| Method | Endpoint                               | Auth required | Allowed roles      | Required data                                                       | Description                                        |
| ------ | -------------------------------------- | ------------- | ------------------ | ------------------------------------------------------------------- | -------------------------------------------------- |
| GET    | `/api/v1/reports/daily`                | Yes           | `admin`, `teacher` | Query: `course_id`, `date` (`YYYY-MM-DD`)                           | Get daily attendance report for a course.          |
| GET    | `/api/v1/reports/weekly`               | Yes           | `admin`, `teacher` | Query: `course_id`, `start_date` (`YYYY-MM-DD`)                     | Get 7-day attendance breakdown.                    |
| GET    | `/api/v1/reports/monthly`              | Yes           | `admin`, `teacher` | Query: `course_id`, `year`, `month` (1-12)                          | Get monthly attendance breakdown.                  |
| GET    | `/api/v1/reports/course/{course_id}`   | Yes           | `admin`, `teacher` | Path: `course_id`                                                   | Get a course-wide attendance summary.              |
| GET    | `/api/v1/reports/student/{student_id}` | Yes           | `admin`, `teacher` | Path: `student_id`                                                  | Get a student's attendance summary across courses. |
| GET    | `/api/v1/reports/export`               | Yes           | `admin`, `teacher` | Query: optional `course_id`, `student_id`, `start_date`, `end_date` | Export attendance results as a CSV file.           |

### Raspberry Pi device registration endpoints

| Method | Endpoint                              | Auth required | Allowed roles      | Required data                                 | Description                                            |
| ------ | ------------------------------------- | ------------- | ------------------ | --------------------------------------------- | ------------------------------------------------------ |
| POST   | `/api/v1/devices`                     | Yes           | `admin`            | Body: `device_id`, `name`, `location`         | Register a Raspberry Pi and receive a one-time secret. |
| GET    | `/api/v1/devices`                     | Yes           | `admin`, `teacher` | None                                          | List all registered devices.                           |
| PUT    | `/api/v1/devices/{device_id}/enabled` | Yes           | `admin`            | Path: `device_id`; query/body flag: `enabled` | Enable or disable a device.                            |

### Role summary

| Role      | Access level                                                                                                                                                                    |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `admin`   | Full system admin access: create/update/delete students, courses, devices, teacher accounts, and face enrollments. Can list every teacher and view any teacher detail.          |
| `teacher` | Operational access to courses, students, attendance sessions, reports, and dashboard data. Can view only their own teacher profile and self-limited teacher listing data.       |
| `student` | Can log in, view their own profile, change their own password, and view their own attendance history. Cannot use the student report endpoint, which remains admin/teacher-only. |
| `device`  | Device-only access for session polling, attendance recording, device status, and recognition.                                                                                   |

Student ownership is enforced for `/students/{student_id}` and `/students/{student_id}/attendance`. The `/reports/student/{student_id}` endpoint remains restricted to admins and teachers.

### Session and routine collision rules

- At most one `active` attendance session may exist for a course.
- At most one `active` attendance session may use a device.
- Routine-created sessions use the active-session guard before taking a course or device slot.
- Completed sessions do not block a later session because the guard checks only `status: active`; legacy cancelled sessions are also inactive.
- Routine create/update rejects overlapping time ranges for the same teacher and weekday. For resource conflicts, it checks the same device when `device_id` is set; otherwise it checks the same room. If both are set, the current validator does not separately check room conflicts.
- Completion marks unrecorded enrolled students absent and releases the course/device slot.
- The scheduler starts at most one session per routine slot per local date. A completed or legacy-cancelled session for that routine and date prevents an automatic restart later that day.
- Session lifecycle is scheduler-only; the application exposes no session creation, completion, cancellation, or deletion endpoint.

## Database schema (Firestore)

The backend uses Firestore collections that map directly to the service layer. The design is intentionally simple: human users live in the `teachers` collection, students and course relationships are stored separately, attendance is session-based, and face enrollment is stored as a derived embedding record.

### Collection overview

| Collection            | Purpose                                                | Primary key / pattern                               | Key fields                                                                                                                                                                                    |
| --------------------- | ------------------------------------------------------ | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `teachers`            | Admin and teacher accounts used for login and JWT auth | Auto-generated Firestore document ID                | `name`, `email`, `password_hash`, `role`, `created_at`                                                                                                                                        |
| `students`            | Student directory, profile, and student login data     | `student_id` as the document ID                     | `student_id`, `name`, `department`, `batch`, `email`, `password_hash`, `must_change_password`, `is_active`, `created_at`                                                                      |
| `face_embeddings`     | One face model per student used for recognition        | Auto-generated document ID, queried by `student_id` | `student_id`, `embedding`, `num_samples`, `quality`, `created_at`, `updated_at`                                                                                                               |
| `courses`             | Academic course definitions                            | Auto-generated document ID                          | `course_code`, `course_name`, `department`, `section`, `teacher_id`, `total_classes`, `created_at`                                                                                            |
| `enrollments`         | Many-to-many student-to-course enrollment links        | Auto-generated document ID                          | `student_id`, `course_id`, `enrolled_at`                                                                                                                                                      |
| `attendance_sessions` | Each class attendance session                          | Auto-generated document ID                          | `course_id`, `teacher_id`, `session_date`, `start_time`, `end_time`, `late_threshold_minutes`, `status`, `device_id`, `source`, `routine_id`, `cancelled_at`, `cancelled_by`, `cancel_reason` |
| `attendance_records`  | One attendance result per student per session          | Stable SHA-256 ID: `session_id:student_id`          | `session_id`, `student_id`, `student_name`, `status`, `confidence`, `detected_at`, `method`                                                                                                   |
| `rpi_devices`         | Registered Raspberry Pi devices assigned to sessions   | Device ID string as document ID                     | `name`, `location`, `secret_hash`, `enabled`, `last_seen_at`                                                                                                                                  |
| `class_routines`      | Weekly class schedule and session defaults             | Auto-generated document ID                          | `course_id`, `teacher_id`, `device_id`, `room`, `day_of_week`, `start_time`, `end_time`, `late_threshold_minutes`, `is_active`, `created_at`, `updated_at`                                    |

### `teachers`

Stores all human accounts that can sign in to the backend.

```json
{
  "name": "Dr. Jane Smith",
  "email": "jane@university.edu",
  "password_hash": "bcrypt-hash",
  "role": "teacher",
  "created_at": "2026-09-27T10:30:00+00:00"
}
```

Notes:

- `role` is one of `admin` or `teacher`.
- `password_hash` is stored as a bcrypt hash, not plaintext.
- JWT claims carry `sub`, `email`, and `role`.
- There is no separate `users` collection; teacher/admin users are kept in `teachers`.

### `students`

Each student is keyed by their university student ID, and the document ID is the same as `student_id`.

```json
{
  "student_id": "20220104064",
  "name": "Aisha Rahman",
  "department": "Computer Science",
  "batch": "2022",
  "email": "aisha@example.edu",
  "password_hash": "bcrypt-hash",
  "must_change_password": true,
  "is_active": true,
  "created_at": "2026-09-27T10:00:00+00:00"
}
```

Notes:

- `password_hash` is bcrypt-hashed; the plaintext password is never stored.
- If the create request omits `password`, the API currently returns a one-time temporary password in the creation response, generated as `<student_id>-changeme`, and sets `must_change_password` to `true`. The student changes it through `POST /api/v1/students/me/change-password`.
- `must_change_password` is persisted, but the current login flow does not block other student operations until it is changed.
- `is_active` is a soft-delete flag. Students are not physically removed on delete.
- `face_enrolled` is derived by checking the `face_embeddings` collection, not by a permanent field in the student record.

### `face_embeddings`

Face matching is done against stored 128D-style embedding vectors. The actual value is Base64-encoded and compressed into a Firestore field.

```json
{
  "student_id": "20220104064",
  "embedding": "base64-encoded-vector",
  "num_samples": 1,
  "quality": 0.98,
  "created_at": "2026-09-27T12:20:00+00:00",
  "updated_at": "2026-09-27T12:20:00+00:00"
}
```

Notes:

- The embedding is compared against the live recognition embedding with cosine similarity.
- A `face_enrolled` flag on the student is set to true by checking whether this collection has at least one record for that `student_id`.
- `quality` is used as a face-quality indicator during enrollment.

### `courses`

A course is usually owned by one teacher but can be related to many students through the `enrollments` collection.

```json
{
  "course_code": "CS101",
  "course_name": "Introduction to Programming",
  "department": "Computer Science",
  "section": "A",
  "teacher_id": "abc123xyz",
  "total_classes": 12,
  "created_at": "2026-09-27T09:15:00+00:00"
}
```

Notes:

- `course_id` is the Firestore document ID, not a persisted field.
- `total_classes` is incremented when an attendance session is started.

### `enrollments`

This is the join collection between students and courses.

```json
{
  "student_id": "20220104064",
  "course_id": "course_doc_id",
  "enrolled_at": "2026-09-27T09:30:00+00:00"
}
```

Notes:

- A student can be enrolled in many courses.
- A course can have many students.
- This collection is used to list students for a specific course and to validate course membership.

### `attendance_sessions`

One attendance session is created per class or device-linked check-in window.

```json
{
  "course_id": "course_doc_id",
  "teacher_id": "teacher_doc_id",
  "session_date": "2026-09-27",
  "start_time": "2026-09-27T10:00:00+00:00",
  "end_time": null,
  "late_threshold_minutes": 15,
  "status": "active",
  "device_id": "rpi-01",
  "source": "routine",
  "routine_id": "routine_doc_id",
  "cancelled_at": null,
  "cancelled_by": null,
  "cancel_reason": null
}
```

Notes:

- `source` is `routine` for sessions created by the scheduler.
- `routine_id` links the session to its class routine.
- `cancelled_at`, `cancelled_by`, and `cancel_reason` remain in the response schema for compatibility with older stored records. The current application has no session cancellation or deletion operation.
- Only one active session is allowed per course and only one active session may use a given device at a time. Only active sessions participate in these collision checks.
- New sessions transition from `active` to `completed`; `cancelled` is retained only as a historical status.
- When completed, unmarked enrolled students are automatically marked absent and the course/device slot is released.

### `class_routines`

Stores weekly class schedules used to configure routine-associated sessions. Routine document IDs are generated by Firestore.

```json
{
  "course_id": "course_doc_id",
  "teacher_id": "teacher_doc_id",
  "device_id": "rpi-01",
  "room": "Room 204",
  "day_of_week": 0,
  "start_time": "09:00",
  "end_time": "10:00",
  "late_threshold_minutes": 15,
  "is_active": true,
  "created_at": "2026-09-27T08:00:00+00:00",
  "updated_at": "2026-09-27T08:00:00+00:00"
}
```

Notes:

- `day_of_week` follows Python numbering: Monday is `0`, Sunday is `6`.
- Times use 24-hour `HH:MM` strings.
- On create/update, overlapping ranges are rejected for the same teacher and weekday. Resource validation checks the device when `device_id` is set, and checks the room only when no device is set; providing both does not add an independent room-conflict check.
- The backend scheduler starts a routine session when it finds the current local time inside an active routine's window, completes active routine sessions at or after the end time, and reconciles in-progress or overdue sessions after restart.

### `attendance_records`

This collection stores each individual recognition event. It is keyed by a stable hash so each student can only appear once in a session.

```json
{
  "session_id": "session_doc_id",
  "student_id": "20220104064",
  "student_name": "Aisha Rahman",
  "status": "present",
  "confidence": 0.91,
  "detected_at": "2026-09-27T10:03:22+00:00",
  "method": "face"
}
```

Notes:

- `status` is computed as `present` or `late` during recording.
- The system avoids duplicate records by checking whether a record already exists for `(session_id, student_id)`.
- `method` may be `face`, `rfid`, or `manual`.

### `rpi_devices`

Each Raspberry Pi that participates in live attendance is registered separately and authenticated with its own device secret.

```json
{
  "name": "Lab RPi 01",
  "location": "Room 204",
  "secret_hash": "bcrypt-hash",
  "enabled": true,
  "last_seen_at": "2026-09-27T10:05:00+00:00"
}
```

Notes:

- Device tokens are distinct from teacher/admin JWT tokens.
- A session may be assigned to a specific `device_id`, and the backend enforces that the posting device matches the assigned device.
- `last_seen_at` is updated when a Pi reports in.

### Data relationships

```text
teachers
  └── creates / manages courses

courses
  ├── has many enrollments
  └── has many attendance_sessions

enrollments
  ├── links students to courses
  └── used to fetch course members

students
  ├── has one or more face_embeddings
  └── has many attendance_records across sessions

attendance_sessions
  └── contains many attendance_records

rpi_devices
  └── can be assigned to one active session at a time
```

### Design notes and constraints

- The project currently uses Firestore as a document database rather than a relational schema.
- Document IDs are not always generated by a single predictable rule; for example, `teachers` and `courses` use auto-generated IDs while `students` and `rpi_devices` often use natural IDs.
- `attendance_records` uses a deterministic ID derived from the session and student to prevent duplicates.
- `face_enrolled` is not treated as a canonical source of truth; when the system needs to check enrollment, it queries `face_embeddings` by `student_id`.

## Run the Raspberry Pi client

The client can run on a Raspberry Pi or another device with a camera. From `rpi-client/`:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `rpi-client/.env` as needed:

```dotenv
API_URL=http://localhost:8000
RPI_EMAIL=admin@university.edu
RPI_PASSWORD=changeme123
COURSE_ID=
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15
ESP32_SERIAL_PORT=
ESP32_BAUD_RATE=115200
FACE_MATCH_THRESHOLD=0.45
ATTENDANCE_COOLDOWN_SECONDS=60
```

Start it with the backend already running:

```bash
python main.py
```

The client polls for an active session, captures camera frames, calls face recognition, records attendance, and queues records locally when the API is unavailable. If an ESP32 port is configured, successful recognition can open the door, buzz, and turn on the green LED. Without an ESP32, the bridge runs in no-op mode. Press `q` in the camera window to quit.

For Linux boot startup, see [rpi-client/README.md](rpi-client/README.md) for the systemd service example.

## Security notes

- Keep `firebase-credentials.json` and `.env` files private.
- Replace the default JWT and admin credentials before using a shared or production Firebase project.
- Use the emulator for destructive or repeatable local tests to avoid modifying live attendance data.
