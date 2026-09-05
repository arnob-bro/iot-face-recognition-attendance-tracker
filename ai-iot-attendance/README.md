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
2. Create a student with `POST /api/v1/students/`.
3. Create a course with `POST /api/v1/courses/` and enroll the student.
4. Start a session with `POST /api/v1/attendance/sessions`.
5. Enroll a face with `POST /api/v1/faces/enroll/{student_id}`.
6. Recognize a frame with `POST /api/v1/faces/recognize`.
7. Review attendance and reports through the attendance, dashboard, and reports endpoints.

Recognition responses include a confidence value and, when liveness is enabled, a `liveness_score`. Face enrollment currently stores one representative sample per upload.

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
