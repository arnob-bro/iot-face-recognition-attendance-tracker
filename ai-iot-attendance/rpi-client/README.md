# Raspberry Pi Attendance Client

This client runs on a Raspberry Pi or other small Linux/Windows device and polls the backend API for active attendance sessions, captures webcam frames, performs face recognition, and optionally triggers an ESP32 door/indicator controller.

## 1. Install dependencies

```bash
cd rpi-client
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure environment

Edit the `.env` file in this directory and set:

- `API_URL` to the backend URL (default `http://localhost:8000`)
- `RPI_EMAIL` and `RPI_PASSWORD` to admin or teacher credentials
- `COURSE_ID` to a specific course, or leave blank to poll for any active session
- `CAMERA_INDEX`, `CAMERA_WIDTH`, `CAMERA_HEIGHT`, `CAMERA_FPS`
- `ESP32_SERIAL_PORT` such as `/dev/ttyUSB0` or `COM3`
- `FACE_MATCH_THRESHOLD` and `ATTENDANCE_COOLDOWN_SECONDS`

## 3. Hardware setup

### Webcam
- Connect a USB camera or Raspberry Pi camera module.
- Confirm the index is correct with OpenCV if detection fails.

### ESP32 bridge
- Connect the ESP32 serial RX/TX pins to the Pi serial interface depending on your board.
- Use `ESP32_SERIAL_PORT` to point at the correct device path.
- If no board is present, the software will continue running in no-op mode.

## 4. Run the client

```bash
python main.py
```

Use `q` to quit the app.

## 5. Auto-start on boot (systemd)

Create a service file such as `/etc/systemd/system/rpi-attendance.service`:

```ini
[Unit]
Description=Raspberry Pi Attendance Client
After=network.target

[Service]
WorkingDirectory=/home/pi/ai-iot-attendance/rpi-client
ExecStart=/home/pi/ai-iot-attendance/rpi-client/.venv/bin/python main.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable rpi-attendance.service
sudo systemctl start rpi-attendance.service
```
