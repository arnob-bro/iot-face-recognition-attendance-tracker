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

## API workflow

Use the interactive documentation at `/docs`:

1. Log in with `POST /api/v1/auth/login` and authorize with the returned bearer token.
2. Register each Raspberry Pi with `POST /api/v1/devices` and save the returned secret securely.
3. Create a student with `POST /api/v1/students/`.
4. Create a course with `POST /api/v1/courses/` and enroll the student.
5. Start a session with `POST /api/v1/attendance/sessions`, including the assigned `device_id`.
6. Configure the Pi with that device ID and secret; it will poll only its assigned session.
7. Enroll a face with `POST /api/v1/faces/enroll/{student_id}`.
8. Recognize a frame with `POST /api/v1/faces/recognize`.
9. Review attendance and reports through the attendance, dashboard, and reports endpoints.

Recognition responses include a confidence value and, when liveness is enabled, a `liveness_score`. Face enrollment currently stores one representative sample per upload.

## API endpoint reference

The backend exposes all routes under `/api/v1`, and authorization is enforced through JWT claims. The role checks are:

- `admin`: full admin access
- `teacher`: teacher-level operations
- `device`: Raspberry Pi device access only
- any authenticated user: logged-in user or device token accepted by `get_current_user`

### Authentication and token usage

- Human users log in via `POST /api/v1/auth/login`.
- Admin/teacher accounts are created by admin users only via `POST /api/v1/auth/register`.
- Raspberry Pi devices log in via `POST /api/v1/devices/login` using `device_id` and `device_secret`.
- All protected routes require the `Authorization: Bearer <token>` header.

### Public / health endpoints

| Method | Endpoint                | Auth required | Allowed roles | Required data                | Description                                               |
| ------ | ----------------------- | ------------- | ------------- | ---------------------------- | --------------------------------------------------------- |
| GET    | `/health`               | No            | Public        | None                         | Backend health check.                                     |
| POST   | `/api/v1/auth/login`    | No            | Public        | `email`, `password`          | Login as admin or teacher and receive a JWT.              |
| POST   | `/api/v1/devices/login` | No            | Public        | `device_id`, `device_secret` | Login a registered Raspberry Pi and receive a device JWT. |

### Authentication and profile endpoints

| Method | Endpoint                             | Auth required | Allowed roles                | Required data                                                       | Description                                                              |
| ------ | ------------------------------------ | ------------- | ---------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| POST   | `/api/v1/auth/register`              | Yes           | `admin`                      | `name`, `email`, `password`, optional `role` (`teacher` or `admin`) | Create a new teacher/admin account.                                      |
| GET    | `/api/v1/auth/me`                    | Yes           | `admin`, `teacher`, `device` | None                                                                | Returns the authenticated user's profile.                                |
| GET    | `/api/v1/auth/teachers`              | Yes           | `admin`                      | None                                                                | `admin` sees all teachers/admins; `teacher` sees only their own profile. |
| GET    | `/api/v1/auth/teachers/{teacher_id}` | Yes           | `admin`                      | Path: `teacher_id`                                                  | `admin` can view any teacher. `teacher` can only view their own profile. |
| GET    | `/api/v1/devices/me`                 | Yes           | `device`                     | None                                                                | Returns the device profile for the current device token.                 |
| GET    | `/api/v1/dashboard/stats`            | Yes           | `admin`, `teacher`, `device` | None                                                                | Returns dashboard stats for the current user.                            |

### Student management endpoints

| Method | Endpoint                                   | Auth required | Allowed roles      | Required data                                                                     | Description                          |
| ------ | ------------------------------------------ | ------------- | ------------------ | --------------------------------------------------------------------------------- | ------------------------------------ |
| GET    | `/api/v1/students/`                        | Yes           | `admin`, `teacher` | Query: `department` (optional), `batch` (optional), `course_id` (optional)        | List students with optional filters. |
| POST   | `/api/v1/students/`                        | Yes           | `admin`            | Body: `student_id`, `name`, `department`, `batch`, `email`, optional `course_ids` | Create a student record.             |
| GET    | `/api/v1/students/{student_id}`            | Yes           | `admin`, `teacher` | Path: `student_id`                                                                | Fetch a specific student.            |
| PUT    | `/api/v1/students/{student_id}`            | Yes           | `admin`            | Path: `student_id`; body: any of `name`, `department`, `batch`, `email`           | Update student details.              |
| DELETE | `/api/v1/students/{student_id}`            | Yes           | `admin`            | Path: `student_id`                                                                | Deactivate a student.                |
| GET    | `/api/v1/students/{student_id}/attendance` | Yes           | `admin`, `teacher` | Path: `student_id`; query: `course_id` (optional)                                 | Get a student's attendance history.  |

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

| Method | Endpoint                                          | Auth required | Allowed roles                | Required data                                                              | Description                                                                      |
| ------ | ------------------------------------------------- | ------------- | ---------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| POST   | `/api/v1/attendance/sessions`                     | Yes           | `admin`, `teacher`           | Body: `course_id`, optional `late_threshold_minutes`, optional `device_id` | Start an attendance session.                                                     |
| PUT    | `/api/v1/attendance/sessions/{session_id}`        | Yes           | `admin`, `teacher`           | Path: `session_id`; body: `status` (`completed` or `cancelled`)            | End or cancel a session.                                                         |
| GET    | `/api/v1/attendance/sessions/active`              | Yes           | `admin`, `teacher`, `device` | Query: `course_id` (optional)                                              | Get the currently active session. For Pi devices, it checks the assigned device. |
| GET    | `/api/v1/attendance/sessions/{session_id}`        | Yes           | `admin`, `teacher`           | Path: `session_id`                                                         | Fetch a session and all attendance records.                                      |
| POST   | `/api/v1/attendance/sessions/{session_id}/record` | Yes           | `admin`, `teacher`, `device` | Path: `session_id`; body: `student_id`, `confidence`, `method`             | Record one attendance event from a recognized student.                           |
| POST   | `/api/v1/attendance/sessions/{session_id}/sync`   | Yes           | `admin`, `teacher`, `device` | Path: `session_id`; body: `records: [{student_id, confidence, method}]`    | Bulk-sync offline attendance records from a Pi.                                  |

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

| Role      | Access level                                                                                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `admin`   | Full system admin access: create/update/delete students, courses, devices, teacher accounts, and face enrollments. Can list every teacher and view any teacher detail.    |
| `teacher` | Operational access to courses, students, attendance sessions, reports, and dashboard data. Can view only their own teacher profile and self-limited teacher listing data. |
| `device`  | Device-only access for session polling, attendance recording, device status, and recognition.                                                                             |

There is no dedicated `student` role in the current backend implementation.

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
