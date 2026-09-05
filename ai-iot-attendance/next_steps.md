# Next Steps — AI-IoT Attendance System Full Build Plan

## Decisions Made ✅

| Decision | Choice | Reason |
|---|---|---|
| Frontend framework | **React + Vite** | Fastest dev experience, SPA is fine |
| RPi camera | **USB webcam** | `cv2.VideoCapture(0)` — no Pi Camera driver needed |
| ESP32 comms | **USB Serial** | Simpler wiring, reliable, no WiFi config needed on ESP32 |
| Multi-photo enrollment | **Single photo** | Sufficient without liveness detection requiring multi-frame |
| Role structure | **Admin + Teacher only** | No student self-service portal needed |

---

## Current Status: What's Already Done ✅

The **FastAPI backend** is largely complete and production-ready:

| Module | Status | Notes |
|---|---|---|
| `app/core/` — Firebase, config, security, exceptions | ✅ Done | JWT auth, Firestore connection, admin bootstrap |
| `app/api/` — All REST endpoints | ✅ Done | auth, students, courses, attendance, faces, reports, dashboard |
| `app/services/` — Business logic | ✅ Done | All 5 services implemented |
| `app/schemas/` — Pydantic models | ✅ Done | All request/response models |
| `app/ai/detection/` — SCRFD face detector | ✅ Done | Real + Mock adapters |
| `app/ai/recognition/` — ArcFace embedder | ✅ Done | Real + Mock adapters |
| `app/ai/embeddings/` — Embedding manager | ✅ Done | Save/load/match logic |
| `app/ai/pipeline.py` — Orchestrator | ✅ Done | Plugs detection + recognition together |
| `backend/tests/` — Test suite | ✅ Done | Auth, students, attendance tests |

---

## What Still Needs to Be Built

| Phase | What | Priority | Est. Days |
|---|---|---|---|
| **3** | Liveness Detection (MiniFASNet in AI pipeline) | 🔴 High | 1–2 |
| **4** | Raspberry Pi Client (IoT device main loop) | 🔴 High | 3–4 |
| **5** | Frontend Dashboard (React + Vite) | 🟡 Medium | 5–7 |
| **6** | ESP32 Arduino Firmware | 🟢 Low | 1 |
| **7** | Production Hardening | 🟢 Low | 2–3 |

**Total remaining: ~12–17 working days**

---

## Phase 3 — Liveness Detection (Backend AI)

> Prevents photo spoofing. The `pipeline.py` already has a `# TODO: Implement MiniFASNet integration` placeholder ready to fill.

### Files to create

```
backend/app/ai/liveness/
├── __init__.py
├── base.py           # LivenessChecker abstract base class
├── mini_fasnet.py    # Real ONNX-based implementation
└── mock_liveness.py  # Dev mock — always returns is_live=True
```

### Checklist

- [ ] **`liveness/base.py`** — define `LivenessChecker` ABC with `check(image, face_data) -> dict` returning `{is_live: bool, score: float}`
- [ ] **`liveness/mock_liveness.py`** — always return `{"is_live": True, "score": 1.0}` for local dev
- [ ] **`liveness/mini_fasnet.py`** — load `MiniFASNetV1.onnx` + `MiniFASNetV2.onnx` from `models/` via ONNX Runtime; crop face ROI and run inference; fuse both model outputs
- [ ] **`pipeline.py` `__init__`** — instantiate `MockLiveness` (mock mode) or `MiniFASNet` (real mode) and assign to `self.liveness_checker`
- [ ] **`pipeline.py` `process_frame()`** — replace the `pass # TODO` with:
  ```python
  liveness_result = self.liveness_checker.check(image, face_data)
  if not liveness_result["is_live"]:
      return {"success": False, "message": "Liveness check failed. Please don't use a photo."}
  ```
- [ ] Add `liveness_score: float` to the `/faces/recognize` response (in `schemas/`)
- [ ] Keep `LIVENESS_ENABLED=false` in `.env` during development; flip to `true` for deployment

### MiniFASNet model download

The two ONNX models come from the [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing) repo. Place them in `backend/models/`:
- `MiniFASNetV1.onnx` (~1.1 MB)
- `MiniFASNetV2.onnx` (~1.1 MB)

---

## Phase 4 — Raspberry Pi Client

> The IoT device that physically runs in the classroom. The backend already exposes every API endpoint the RPi needs.

### Directory structure

```
rpi-client/
├── main.py               # Entry point — main recognition loop
├── config.py             # Settings dataclass (reads from .env)
├── requirements.txt
├── .env                  # API_URL, RPi_EMAIL, RPi_PASSWORD, COURSE_ID
├── README.md             # Hardware setup & wiring guide
├── camera/
│   ├── __init__.py
│   └── capture.py        # USB webcam wrapper (cv2.VideoCapture(0))
├── api/
│   ├── __init__.py
│   └── client.py         # HTTP client (httpx) talking to backend
├── ui/
│   ├── __init__.py
│   └── display.py        # OpenCV overlay rendering
├── hardware/
│   ├── __init__.py
│   └── esp32_bridge.py   # pyserial bridge to ESP32
└── offline/
    ├── __init__.py
    └── queue.py          # SQLite offline queue
```

### Step 4.1 — `config.py`

- [ ] Dataclass / pydantic model reading from `.env`:
  - `api_url`, `rpi_email`, `rpi_password`, `course_id`
  - `camera_index = 0` (USB webcam), `camera_width = 640`, `camera_height = 480`, `camera_fps = 15`
  - `esp32_serial_port` (e.g. `/dev/ttyUSB0` on Linux, `COM3` on Windows), `esp32_baud_rate = 115200`
  - `face_match_threshold = 0.45`
  - `attendance_cooldown_seconds = 60` (don't re-record same student within this window)

### Step 4.2 — `camera/capture.py`

- [ ] Class `WebcamCapture`:
  - `__init__(index=0, width=640, height=480, fps=15)` — opens `cv2.VideoCapture(index)`, sets resolution + FPS props
  - `read_frame() -> np.ndarray | None` — returns BGR frame or `None` if failed
  - `release()` — `self.cap.release()`
- [ ] On `read_frame()` returning `None` 5 times in a row: log error and attempt re-open
- [ ] **Note:** `cv2.VideoCapture(0)` for USB webcam — no extra driver needed

### Step 4.3 — `api/client.py`

- [ ] Class `AttendanceAPIClient(base_url)` using `httpx.Client` (synchronous for simplicity on RPi):
  - `login(email, password) -> str` — `POST /api/v1/auth/login`, stores token internally
  - `get_active_session(course_id) -> dict | None` — `GET /api/v1/attendance/sessions/active?course_id=...`
  - `recognize_face(jpeg_bytes: bytes) -> dict` — `POST /api/v1/faces/recognize`, multipart upload
  - `record_attendance(session_id, student_id, confidence, method="face_recognition") -> dict`
  - `sync_offline_records(session_id, records: list[dict]) -> list` — `POST /api/v1/attendance/sessions/{id}/sync`
- [ ] On any `httpx.ConnectError` or `httpx.TimeoutException`: raise a custom `NetworkError` so `main.py` can catch and queue
- [ ] Token auto-refresh: if response is 401, call `login()` again then retry once

### Step 4.4 — `offline/queue.py`

- [ ] Uses `sqlite3` (standard library — no pip install needed)
- [ ] Table schema:
  ```sql
  CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    confidence REAL,
    method TEXT DEFAULT 'face_recognition',
    synced INTEGER DEFAULT 0
  );
  ```
- [ ] `enqueue(session_id, student_id, detected_at, confidence)` — insert row
- [ ] `get_pending() -> list[dict]` — `SELECT * FROM queue WHERE synced=0`
- [ ] `mark_synced(ids: list[int])` — `UPDATE queue SET synced=1 WHERE id IN (...)`
- [ ] `drain(api_client, session_id)` — called on startup and every 5 min; calls `api_client.sync_offline_records()` then marks synced

### Step 4.5 — `hardware/esp32_bridge.py`

- [ ] Class `ESP32Bridge(port, baud_rate=115200)`:
  - `__init__()` — open `serial.Serial(port, baud_rate, timeout=1)`, log success
  - `send(command: str)` — write `command + "\n"` encoded as bytes
  - `open_door()` — `send("OPEN")`
  - `buzz()` — `send("BUZZ")`
  - `led_green()` — `send("LED_GREEN")`
  - `led_red()` — `send("LED_RED")`
  - `close()` — `self.ser.close()`
- [ ] If `serial.SerialException` on init (port not found): log warning and set `self.available = False` — all methods become no-ops so the software loop still works without hardware connected

### Step 4.6 — `ui/display.py`

- [ ] Function `draw_overlay(frame, status, student_name="", confidence=0.0) -> np.ndarray`:
  - `status` can be `"idle"`, `"matched"`, `"unknown"`, `"duplicate"`, `"no_face"`
  - Draw a semi-transparent status bar at the bottom of the frame
  - Green bar + student name + confidence % for `"matched"`
  - Red bar + "Unknown Person" for `"unknown"`
  - Yellow bar + "Already Recorded" for `"duplicate"`
  - Grey bar + "Waiting for session..." for `"idle"`
- [ ] Function `show(frame)` — `cv2.imshow("Attendance System", frame)`

### Step 4.7 — `main.py` (main loop)

```
Startup
  └─ load config → login to API → init WebcamCapture → init ESP32Bridge → init OfflineQueue

Main loop (runs forever)
  ├─ Every 30s: poll get_active_session(course_id)
  │     ├─ If session found: set active_session_id, update overlay to "active"
  │     └─ If no session: show "idle" overlay, skip recognition
  │
  └─ Per frame (when session is active):
        ├─ read_frame() from webcam
        ├─ POST frame to /faces/recognize
        │     ├─ matched=True, confidence >= threshold:
        │     │     ├─ Check local cooldown dict (student_id → last_recorded_time)
        │     │     ├─ If cooldown not expired → overlay "duplicate", skip
        │     │     └─ Else → record_attendance() → ESP32 OPEN + LED_GREEN → update cooldown
        │     ├─ matched=False:
        │     │     └─ ESP32 BUZZ + LED_RED → overlay "unknown"
        │     └─ NetworkError:
        │           └─ enqueue to offline SQLite → overlay "offline"
        └─ draw_overlay() → cv2.imshow()

Shutdown (Ctrl+C)
  └─ webcam.release() → esp32.close() → cv2.destroyAllWindows()
```

Checklist:
- [ ] Implement startup sequence
- [ ] Implement session polling (background thread or time-based in main loop)
- [ ] Implement per-frame recognition loop
- [ ] Implement local cooldown dict `{student_id: datetime}` to prevent duplicate records
- [ ] Implement graceful shutdown with `try/finally`
- [ ] Run offline queue drain every 5 minutes (use `time.time()` diff in main loop)

### Step 4.8 — `requirements.txt`

```
httpx>=0.27.0
opencv-python-headless>=4.9.0
pyserial>=3.5
python-dotenv>=1.0.0
numpy>=1.24.0
```

### Step 4.9 — `README.md` (hardware setup)

Document:
- How to connect USB webcam to RPi
- How to connect ESP32 via USB to RPi (which `/dev/ttyUSB*` port)
- How to set up `.env` with `API_URL` pointing to the backend server's local network IP
- How to run: `python main.py`
- How to auto-start on boot (systemd service unit)

---

## Phase 5 — Frontend Dashboard (React + Vite)

> Admin/teacher web UI. Two roles only: **admin** and **teacher**.

### Step 5.1 — Scaffold

```bash
npx create-vite@latest frontend --template react
cd frontend
npm install axios react-router-dom @tanstack/react-query recharts react-dropzone
```

### Step 5.2 — Directory structure

```
frontend/src/
├── main.jsx
├── App.jsx               # Router setup
├── index.css             # Global design system (CSS variables)
├── contexts/
│   └── AuthContext.jsx   # JWT storage, login/logout, axios interceptor
├── components/
│   ├── ProtectedRoute.jsx
│   ├── Sidebar.jsx
│   ├── StatCard.jsx
│   ├── AttendanceTable.jsx
│   ├── AttendanceChart.jsx
│   ├── FaceEnrollWidget.jsx
│   └── LiveFeed.jsx
└── pages/
    ├── Login.jsx
    ├── Dashboard.jsx
    ├── Students.jsx
    ├── StudentDetail.jsx
    ├── Courses.jsx
    ├── CourseDetail.jsx
    ├── LiveSession.jsx
    ├── ReportCourse.jsx
    ├── ReportStudent.jsx
    └── Settings.jsx
```

### Step 5.3 — Routes

| Page | Route | Roles |
|---|---|---|
| Login | `/login` | Public |
| Dashboard | `/` | Admin, Teacher |
| Students list | `/students` | Admin, Teacher |
| Student detail + face enroll | `/students/:id` | Admin |
| Courses list | `/courses` | Admin, Teacher |
| Course detail + enrollment | `/courses/:id` | Admin, Teacher |
| Live session monitor | `/sessions/:id/live` | Admin, Teacher |
| Course report | `/reports/course/:id` | Admin, Teacher |
| Student report | `/reports/student/:id` | Admin, Teacher |
| Settings | `/settings` | Admin |

### Step 5.4 — `AuthContext.jsx`

- [ ] Store `access_token` and `user` (role, name) in `localStorage`
- [ ] Provide `login(email, password)` — calls `POST /api/v1/auth/login`
- [ ] Provide `logout()` — clears storage, redirects to `/login`
- [ ] Set up `axios` default interceptor: attach `Authorization: Bearer <token>` to every request
- [ ] On 401 response: auto-logout

### Step 5.5 — Component details

- [ ] **`StatCard`** — icon + label + large number, with subtle number count-up animation on load
- [ ] **`AttendanceTable`** — columns: Student ID, Name, Status badge, Time, Confidence %; sortable columns; color-coded status badges (green/red/yellow)
- [ ] **`AttendanceChart`** — Recharts `AreaChart` showing daily attendance % over the last 30 days
- [ ] **`FaceEnrollWidget`** — `react-dropzone` image drop zone; on drop, POST to `/api/v1/faces/enroll/{student_id}`; show success/error toast; show current enrollment status
- [ ] **`LiveFeed`** — polls `GET /api/v1/dashboard/stats` every 5 seconds using React Query; renders a scrolling activity feed of recent recognitions
- [ ] **`<ExportButton>`** — `GET /api/v1/reports/export/csv` → trigger `window.URL.createObjectURL` file download

### Step 5.6 — Design system (`index.css`)

```css
:root {
  --bg-primary:    #0F172A;   /* Deep navy */
  --bg-secondary:  #1E293B;   /* Card background */
  --accent:        #7C3AED;   /* Purple */
  --success:       #10B981;   /* Green */
  --danger:        #EF4444;   /* Red */
  --warning:       #F59E0B;   /* Amber */
  --text-primary:  #F1F5F9;
  --text-muted:    #94A3B8;
  --border:        rgba(255,255,255,0.08);
  --glass:         rgba(255,255,255,0.04);
}
```

- Google Font: **Inter** (via `<link>` in `index.html`)
- Cards: `background: var(--glass); backdrop-filter: blur(12px); border: 1px solid var(--border);`
- Smooth hover transitions: `transition: transform 0.2s, box-shadow 0.2s;`

---

## Phase 6 — ESP32 Firmware

Create `esp32/` at the project root:

```
esp32/
├── firmware/
│   └── attendance_controller.ino
└── README.md
```

### `attendance_controller.ino`

- [ ] `Serial.begin(115200)` in `setup()`
- [ ] In `loop()`: read until `\n`, parse command string
- [ ] Commands and GPIO actions:

| Command | Action | Pin |
|---|---|---|
| `OPEN` | Pulse relay HIGH for 3000 ms, then LOW | GPIO 25 |
| `BUZZ` | Tone on buzzer for 500 ms | GPIO 14 |
| `LED_GREEN` | Set green LED HIGH, red LOW | GPIO 26 |
| `LED_RED` | Set red LED HIGH, green LOW | GPIO 27 |

- [ ] Wiring table in `esp32/README.md`:

| ESP32 Pin | Component | Notes |
|---|---|---|
| GPIO 25 | Relay IN | Use 5V relay module; powers door strike |
| GPIO 26 | Green LED (+ 220Ω resistor) | Present indicator |
| GPIO 27 | Red LED (+ 220Ω resistor) | Unknown person indicator |
| GPIO 14 | Passive buzzer | 500 Hz tone |
| GND | Common ground | Connect RPi GND too |

---

## Phase 7 — Production Hardening

- [ ] **Dockerfile** for backend (`python:3.11-slim`, COPY app, `pip install -r requirements.txt`, `CMD uvicorn ...`)
- [ ] **`docker-compose.yml`** — backend service + optional nginx reverse proxy with HTTPS
- [ ] **Rate limiting** — add `slowapi` on `POST /faces/recognize` (max 2 req/s per IP)
- [ ] **Firestore composite indexes** — add indexes for:
  - `attendance_records`: `session_id ASC + student_id ASC`
  - `attendance_sessions`: `course_id ASC + session_date DESC`
- [ ] **Refresh token endpoint** — `POST /api/v1/auth/refresh` to extend sessions without re-login
- [ ] **Structured logging** — swap to `python-json-logger` for machine-readable logs
- [ ] **GitHub Actions CI** — `pytest` on every PR; Docker build on merge to `main`
- [ ] **`.env.example`** file in `backend/` (already referenced in README — create it)

---

## Recommended Build Order

```
Phase 3 (Liveness)  →  Phase 4 (RPi Client)  →  Phase 5 (Frontend)  →  Phase 6 (ESP32)  →  Phase 7 (Hardening)
    1-2 days               3-4 days                  5-7 days               1 day              2-3 days
```

### Minimal Viable Demo (fastest classroom test)

1. ✅ Backend is already running — `uvicorn app.main:app --reload`
2. Keep `USE_MOCK_AI=true` and `LIVENESS_ENABLED=false` in `.env` while developing RPi client
3. Build **Phase 4 in order: 4.1 → 4.2 → 4.3 → 4.7** (skip offline queue + ESP32 bridge for first demo)
4. Enroll a face via Swagger (`POST /api/v1/faces/enroll/{student_id}`)
5. Start a session via Swagger (`POST /api/v1/attendance/sessions`)
6. Run `python rpi-client/main.py` — watch attendance records appear in Firestore
7. Then flip `USE_MOCK_AI=false` to test real face recognition with the ArcFace model
8. Then build the Frontend dashboard (Phase 5)
