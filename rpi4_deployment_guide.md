# Raspberry Pi 4 (8GB) Deployment Guide — AI-IoT Attendance System

## Project Overview

Your project is a **two-component system**:

| Component | Role | Where it runs |
|-----------|------|---------------|
| **Backend** ([backend/](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/backend)) | FastAPI server + AI pipeline (SCRFD detection, ArcFace recognition, MiniFASNet liveness) + Firebase Firestore | Server or RPi |
| **RPi Client** ([rpi-client/](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/rpi-client)) | Camera capture, sends JPEG frames to backend API, shows OpenCV overlay, ESP32 serial bridge, SQLite offline queue | Raspberry Pi |

> [!IMPORTANT]
> The RPi client is a **thin client** — it captures frames and sends them to the backend for AI processing. It does **not** run face detection/recognition/liveness locally. This is a critical architectural distinction that affects your deployment options.

---

## Deployment Architecture Options

### Option A: Backend on a Separate PC/Server, RPi Client on Pi (Recommended for Performance)

```
┌────────────────────┐         HTTP/API          ┌──────────────────────┐
│   Raspberry Pi 4   │  ──────────────────────▶  │  PC / Cloud Server   │
│                    │                            │                      │
│  • Camera capture  │  ◀──────────────────────  │  • FastAPI backend   │
│  • RPi Client      │        JSON response       │  • AI Pipeline       │
│  • ESP32 bridge    │                            │  • Firebase          │
│  • Offline queue   │                            │  • InsightFace       │
└────────────────────┘                            └──────────────────────┘
```

**Pros**: Fast inference (~50-200ms per frame on a modern CPU), RPi stays cool and responsive.
**Cons**: Requires network connectivity; two devices to manage.

### Option B: Everything on the Raspberry Pi 4 (All-in-One)

```
┌──────────────────────────────────────────────┐
│              Raspberry Pi 4 (8GB)             │
│                                               │
│  • RPi Client (camera, ESP32, offline queue)  │
│  • FastAPI backend (localhost:8000)            │
│  • AI Pipeline (SCRFD + ArcFace + MiniFASNet) │
│  • Firebase connection                        │
└──────────────────────────────────────────────┘
```

**Pros**: Fully self-contained, works offline with local queue, single device.
**Cons**: Slower inference (~1-3 seconds per frame), higher CPU/memory usage, runs warm.

> [!TIP]
> With **8GB RAM** you have plenty of memory for either option. The bottleneck on RPi is **CPU speed** for ONNX inference, not memory.

---

## Recommended Approach: Option B (All-in-One on RPi 4)

For a university classroom IoT prototype, running everything on the Pi is the cleanest solution. Here's how to make it work well:

---

## Step-by-Step Setup on Raspberry Pi 4

### 1. OS Setup

```bash
# Use Raspberry Pi OS (64-bit, Bookworm) — 64-bit is critical for performance
# Flash with Raspberry Pi Imager, enable SSH, set hostname, configure WiFi

# After booting, update everything
sudo apt update && sudo apt upgrade -y

# Install system dependencies for OpenCV and building Python packages
sudo apt install -y \
    python3-dev python3-venv python3-pip \
    libopencv-dev python3-opencv \
    libatlas-base-dev libhdf5-dev \
    libffi-dev libssl-dev \
    git cmake build-essential \
    v4l-utils
```

> [!IMPORTANT]
> Use the **64-bit** Raspberry Pi OS. InsightFace and ONNX Runtime have significantly better support and performance on aarch64 vs armhf (32-bit).

### 2. Clone the Project

```bash
cd ~
git clone <your-repo-url> ai-iot-attendance
cd ai-iot-attendance
```

### 3. Set Up the Backend

```bash
cd ~/ai-iot-attendance/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel

# Install ONNX Runtime for ARM64 (pre-built wheel)
pip install onnxruntime

# Install InsightFace (may take a while to build on Pi)
pip install insightface

# Install the rest
pip install -r requirements.txt
```

> [!WARNING]
> `insightface` installation can take 10-20 minutes on the Pi because it compiles Cython extensions. If it fails, try:
> ```bash
> pip install cython numpy
> pip install insightface --no-build-isolation
> ```

### 4. Configure the Backend `.env`

Edit [backend/.env](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/backend/.env):

```dotenv
# --- Firebase ---
FIREBASE_PROJECT_ID=iot-attendance-project-c37e2
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# --- Authentication ---
JWT_SECRET_KEY=<generate-a-strong-random-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# --- API ---
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# --- AI / Face Recognition ---
FACE_MATCH_THRESHOLD=0.45
LIVENESS_ENABLED=true
USE_MOCK_AI=false          # ← Set to false for real AI!
MODEL_DIR=./models

# --- Attendance ---
ATTENDANCE_COOLDOWN_SECONDS=60
LATE_THRESHOLD_MINUTES=15

# --- Admin ---
ADMIN_EMAIL=admin@university.edu
ADMIN_PASSWORD=<strong-password>
ADMIN_NAME=System Administrator
```

> [!CAUTION]
> Change `JWT_SECRET_KEY` and `ADMIN_PASSWORD` from the defaults before any real use. The current `.env` has `JWT_SECRET_KEY=meow` which is extremely insecure.

### 5. Download AI Models

The InsightFace `buffalo_l` models will auto-download on first run. For liveness, the [MiniFASNet ONNX models](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/models) (~1.7MB each) are already in the `models/` directory and will also auto-download if missing.

```bash
# Verify the liveness models exist
ls ~/ai-iot-attendance/models/
# Should show: MiniFASNetV1SE.onnx  MiniFASNetV2.onnx

# Copy them to backend/models/ as well
cp ~/ai-iot-attendance/models/*.onnx ~/ai-iot-attendance/backend/models/
```

### 6. Start the Backend

```bash
cd ~/ai-iot-attendance/backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> [!NOTE]
> Don't use `--reload` in production on the Pi — it adds overhead. First startup will be slow (~30-60s) as InsightFace downloads and loads the `buffalo_l` model pack (~300MB).

### 7. Set Up the RPi Client

```bash
cd ~/ai-iot-attendance/rpi-client

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 8. Configure the RPi Client `.env`

Edit [rpi-client/.env](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/rpi-client/.env):

```dotenv
API_URL=http://localhost:8000    # localhost since backend is on same Pi
RPI_EMAIL=admin@university.edu
RPI_PASSWORD=<your-admin-password>
COURSE_ID=                        # Leave blank to poll any active session

CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=15                     # Consider lowering to 10 on Pi

ESP32_SERIAL_PORT=/dev/ttyUSB0    # Or /dev/ttyACM0, or blank if no ESP32
ESP32_BAUD_RATE=115200

FACE_MATCH_THRESHOLD=0.45
ATTENDANCE_COOLDOWN_SECONDS=60
```

### 9. Start the Client

```bash
cd ~/ai-iot-attendance/rpi-client
source .venv/bin/activate
python main.py
```

---

## Performance Tuning for RPi 4

### CPU & Thermal

```bash
# Check CPU temperature (should stay below 80°C)
vcgencmd measure_temp

# Check CPU frequency throttling
vcgencmd get_throttled
# 0x0 means no throttling — good!
```

> [!TIP]
> **Use a heatsink + fan case** (like the official Raspberry Pi case with fan). Running ONNX inference continuously will heat up the CPU. Throttling at 80°C will dramatically slow inference.

### ONNX Runtime Threading

The [MiniFASNet liveness checker](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/backend/app/ai/liveness/mini_fasnet.py#L184-L186) already limits threads to 1, which is good for the Pi's 4 cores:

```python
sess_options.inter_op_num_threads = 1
sess_options.intra_op_num_threads = 1
```

For InsightFace (SCRFD + ArcFace), consider setting the same globally:

```bash
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
```

### Camera Settings

For smoother operation on Pi, consider lowering resolution/FPS in `.env`:

```dotenv
CAMERA_WIDTH=640      # 640x480 is already good — don't go higher
CAMERA_HEIGHT=480
CAMERA_FPS=10         # Lower from 15 to 10 to reduce CPU load from capture
```

### Reduce Recognition Frequency

The RPi client currently sends **every frame** to the backend for recognition. This is the biggest performance issue. Consider these improvements:

| Strategy | Impact |
|----------|--------|
| Skip frames (process every 3rd-5th frame) | ~3-5× reduction in API calls |
| Only send when motion is detected | Massive reduction when no one is present |
| Add a cooldown between recognition attempts | Prevents hammering the AI pipeline |

---

## Auto-Start on Boot (systemd)

The [rpi-client/README.md](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/rpi-client/README.md#L47-L72) already provides a systemd template. Here's a complete setup for **both** services:

### Backend Service

```bash
sudo nano /etc/systemd/system/attendance-backend.service
```

```ini
[Unit]
Description=AI-IoT Attendance Backend
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/ai-iot-attendance/backend
ExecStart=/home/pi/ai-iot-attendance/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
User=pi
Environment=PATH=/home/pi/ai-iot-attendance/backend/.venv/bin:/usr/bin
Environment=OMP_NUM_THREADS=2

[Install]
WantedBy=multi-user.target
```

### RPi Client Service

```bash
sudo nano /etc/systemd/system/rpi-attendance.service
```

```ini
[Unit]
Description=Raspberry Pi Attendance Client
After=attendance-backend.service
Requires=attendance-backend.service

[Service]
WorkingDirectory=/home/pi/ai-iot-attendance/rpi-client
ExecStartPre=/bin/sleep 15
ExecStart=/home/pi/ai-iot-attendance/rpi-client/.venv/bin/python main.py
Restart=always
RestartSec=10
User=pi
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

### Enable Both Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-backend.service
sudo systemctl enable rpi-attendance.service
sudo systemctl start attendance-backend.service
sudo systemctl start rpi-attendance.service

# Check status
sudo systemctl status attendance-backend.service
sudo systemctl status rpi-attendance.service

# View logs
journalctl -u attendance-backend.service -f
journalctl -u rpi-attendance.service -f
```

> [!NOTE]
> The `ExecStartPre=/bin/sleep 15` gives the backend time to fully initialize (load AI models) before the client starts sending requests.

---

## Hardware Wiring Summary

### Camera
- **USB Webcam**: Plug into any USB port, set `CAMERA_INDEX=0`
- **Pi Camera Module**: Enable via `sudo raspi-config` → Interface Options → Camera. Use `CAMERA_INDEX=0` (OpenCV uses V4L2 backend)

### ESP32 Bridge
- Connect ESP32 via USB cable to Pi
- Find the port: `ls /dev/ttyUSB* /dev/ttyACM*`
- Set `ESP32_SERIAL_PORT=/dev/ttyUSB0` (or whichever appears)
- The [ESP32Bridge](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/rpi-client/hardware/esp32_bridge.py) sends serial commands: `OPEN`, `BUZZ`, `LED_GREEN`, `LED_RED`
- If no ESP32 is connected, the bridge runs in no-op mode — no crash

### Network
- WiFi or Ethernet for Firebase connectivity
- The [OfflineQueue](file:///c:/iot-face-recognition-attendance-tracker/ai-iot-attendance/rpi-client/offline/queue.py) handles network outages using a local SQLite database

---

## Expected Performance on RPi 4 (8GB)

| Metric | Estimated Value |
|--------|----------------|
| RAM usage (backend + client) | ~1.5-2.5 GB |
| First startup time | 30-90 seconds (model loading) |
| SCRFD face detection | ~200-500ms per frame |
| ArcFace embedding generation | ~100-300ms per frame |
| MiniFASNet liveness (2 models) | ~50-150ms per frame |
| **Total per-frame pipeline** | **~400ms - 1s** |
| CPU temperature under load | 65-80°C (with heatsink) |

> [!TIP]
> At ~1 second per frame, you'll process roughly **1 face per second**. This is perfectly fine for a classroom entrance where students enter one at a time. You do NOT need 15 FPS for recognition — you need 15 FPS only for the camera preview display.

---

## Key Recommendations Summary

1. **Use 64-bit Raspberry Pi OS** — critical for ONNX Runtime and InsightFace ARM64 support
2. **Use a heatsink + fan** — continuous inference will throttle without cooling
3. **Set `USE_MOCK_AI=false`** in backend `.env` — currently set to `false` which is correct
4. **Lower `CAMERA_FPS` to 10** — reduces unnecessary CPU load from frame capture
5. **Add frame-skipping logic** — don't send every frame for recognition, process every 3rd-5th frame
6. **Use systemd services** — auto-start both backend and client on boot
7. **Change default credentials** — `JWT_SECRET_KEY=meow` and `ADMIN_PASSWORD=changeme123` are not safe
8. **Copy liveness models** to `backend/models/` — the MiniFASNet `.onnx` files from the root `models/` directory
9. **Monitor with `htop` and `vcgencmd measure_temp`** — keep an eye on CPU and temperature
10. **Consider Option A** (separate server) if you need faster recognition or are processing multiple cameras

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `insightface` fails to install | Install `cython` and `numpy` first, use `--no-build-isolation` |
| Camera not detected | Run `v4l2-ctl --list-devices`, try different `CAMERA_INDEX` |
| `onnxruntime` import error | Ensure you're using 64-bit OS; install via `pip install onnxruntime` |
| Backend crashes on startup | Check `firebase-credentials.json` exists and `.env` is correct |
| Very slow inference | Check `vcgencmd get_throttled` — if not `0x0`, improve cooling |
| ESP32 not responding | Check port with `ls /dev/ttyUSB*`, ensure baud rate matches |
| `cv2.imshow` fails (headless) | Use `opencv-python-headless` and remove `cv2.imshow` calls, or run with `DISPLAY=:0` |
| No active session found | Create a session first via the backend API at `/docs` |
