# Phase 3 & 4 — Liveness Detection + Raspberry Pi Client

Complete implementation of the liveness detection anti-spoofing module (Phase 3) and the full Raspberry Pi IoT client application (Phase 4) as specified in [next_steps.md](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/next_steps.md).

---

## User Review Required

> [!IMPORTANT]
> **MiniFASNet ONNX Models:** The liveness module requires two model files (`MiniFASNetV1.onnx` and `MiniFASNetV2.onnx`) placed in `backend/models/`. These come from the [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing) repo. I will **not** download them automatically — you will need to place them manually. The mock adapter will be used when models are absent.
Ans: Auto-download MiniFASNet models on first run

> [!WARNING]
> **Serial port for ESP32:** The `.env` currently has `ESP32_SERIAL_PORT=/dev/ttyUSB0` (Linux). On Windows during development, this would be something like `COM3`. The ESP32 bridge is designed to gracefully degrade to no-ops if the port is not found, so this won't block development. Ans: Do what is best for now in dev and for in prod.

## Open Questions

> [!IMPORTANT]
> **RPi client `.env` separation:** Phase 4 creates a standalone `rpi-client/` directory with its own `.env`. Should it reuse the backend's `.env`, or should I create a separate one with only the RPi-relevant variables (`API_URL`, `COURSE_ID`, credentials, serial port, camera settings)?  
> **My recommendation:** Separate `.env` — the RPi client runs on a different machine from the backend. 
Ans: No hardcoded course_id — the RPi polls for ANY active session (since one device serves one room with many courses/teachers)
Separate .env for RPi client but API_URL defaults to localhost:8000 since both run on the same Pi

---

## Proposed Changes

### Phase 3 — Liveness Detection (Backend AI)

#### [NEW] [base.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/liveness/base.py)
Abstract base class `LivenessChecker` with a single method `check(image, face_data) -> dict` returning `{"is_live": bool, "score": float}`. Follows the exact same ABC pattern as [detection/base.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/detection/base.py) and [recognition/base.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/recognition/base.py).

#### [NEW] [mock_liveness.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/liveness/mock_liveness.py)
Mock implementation — always returns `{"is_live": True, "score": 1.0}`. Used when `USE_MOCK_AI=true`.

#### [NEW] [mini_fasnet.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/liveness/mini_fasnet.py)
Real ONNX Runtime implementation:
- Loads `MiniFASNetV1.onnx` and `MiniFASNetV2.onnx` from the `models/` directory
- Crops the face ROI from the full image using the bounding box from detection
- Pads the crop to a square, resizes to the model's expected input size (80×80)
- Runs inference through both models and fuses their softmax outputs (average)
- Returns `is_live=True` if the fused "real" probability exceeds a threshold (0.5)

#### [NEW] [__init__.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/liveness/__init__.py)
Package init file.

#### [MODIFY] [pipeline.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/ai/pipeline.py)
- Import `LivenessChecker`, `MockLiveness`, and `MiniFASNet` (with try/except fallback)
- In `__init__`: instantiate `self.liveness_checker` based on mock mode
- In `process_frame()`: replace the `pass # TODO` placeholder with actual liveness checking logic that rejects non-live faces
- Add `liveness_score` to the returned result dict

#### [MODIFY] [faces.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/backend/app/api/faces.py)
- Add `liveness_score` to the `/faces/recognize` response when liveness is enabled

---

### Phase 4 — Raspberry Pi Client

All files created under `rpi-client/` at the project root.

#### [NEW] [config.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/config.py)
Pydantic `Settings` dataclass reading from `.env`:
- `api_url`, `rpi_email`, `rpi_password`, `course_id`
- Camera: `camera_index`, `camera_width`, `camera_height`, `camera_fps`
- ESP32: `esp32_serial_port`, `esp32_baud_rate`
- Thresholds: `face_match_threshold`, `attendance_cooldown_seconds`

#### [NEW] [.env](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/.env)
Template `.env` file with sensible defaults pointing to `http://localhost:8000`.

#### [NEW] [camera/capture.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/camera/capture.py)
`WebcamCapture` class wrapping `cv2.VideoCapture(0)`:
- Opens camera with configured resolution and FPS
- `read_frame()` returns BGR ndarray or None
- Auto-reconnect after 5 consecutive failures
- `release()` for cleanup

#### [NEW] [api/client.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/api/client.py)
`AttendanceAPIClient` using synchronous `httpx.Client`:
- `login(email, password)` — authenticates and stores JWT
- `get_active_session(course_id)` — polls for active session
- `recognize_face(jpeg_bytes)` — multipart POST to `/api/v1/faces/recognize`
- `record_attendance(session_id, student_id, confidence, method)` — POST to record
- `sync_offline_records(session_id, records)` — bulk sync
- Auto-retry on 401 (re-login then retry once)
- Raises custom `NetworkError` on connection/timeout failures

#### [NEW] [offline/queue.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/offline/queue.py)
SQLite-based offline queue (standard library, no pip install):
- Creates table on init
- `enqueue(session_id, student_id, detected_at, confidence)`
- `get_pending()` — returns unsynced records
- `mark_synced(ids)` — marks records as synced
- `drain(api_client, session_id)` — syncs pending records to backend

#### [NEW] [hardware/esp32_bridge.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/hardware/esp32_bridge.py)
`ESP32Bridge` class using `pyserial`:
- `open_door()`, `buzz()`, `led_green()`, `led_red()`
- Graceful degradation: if serial port not found, all methods become no-ops (`self.available = False`)

#### [NEW] [ui/display.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/ui/display.py)
OpenCV overlay rendering:
- `draw_overlay(frame, status, student_name, confidence)` — draws status bar
- Status modes: `idle`, `matched`, `unknown`, `duplicate`, `no_face`
- Color-coded semi-transparent bars with text

#### [NEW] [main.py](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/main.py)
Main entry point with the recognition loop:
- Startup: load config → login to API → init camera → init ESP32 → init offline queue
- Session polling every 30s
- Per-frame: capture → encode JPEG → POST to `/faces/recognize` → cooldown check → record attendance → trigger ESP32 → draw overlay
- Offline fallback on network errors
- Queue drain every 5 minutes
- Graceful shutdown on `Ctrl+C`

#### [NEW] [requirements.txt](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/requirements.txt)
Minimal deps: `httpx`, `opencv-python-headless`, `pyserial`, `python-dotenv`, `numpy`, `pydantic-settings`.

#### [NEW] [README.md](file:///c:/Users/User/Documents/IOT/ai-iot-attendance/rpi-client/README.md)
Hardware setup guide: webcam connection, ESP32 wiring, `.env` configuration, how to run, and how to auto-start on boot via systemd.

#### Package init files
`__init__.py` for: `camera/`, `api/`, `offline/`, `hardware/`, `ui/`

---

## Verification Plan

### Automated Tests
- `cd backend && python -m pytest tests/ -v` — ensure existing backend tests still pass after pipeline changes
- Manually verify liveness mock returns `is_live: True` by hitting `/api/v1/faces/recognize` in Swagger

### Manual Verification
- Run the backend with `USE_MOCK_AI=true` and `LIVENESS_ENABLED=true` to verify the mock liveness path works end-to-end
- Run `python rpi-client/main.py` and verify it starts, connects to the backend API, polls for sessions, and shows the OpenCV window (or logs gracefully if no display is attached)
- Verify ESP32 bridge degrades gracefully when no serial device is connected
- Verify offline queue creates the SQLite DB and enqueues records when the API is unreachable
