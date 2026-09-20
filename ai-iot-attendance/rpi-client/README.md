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
- `DEVICE_ID` and `DEVICE_SECRET` from the admin device-registration endpoint
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

If startup reports that `cv2.VideoCapture` is unavailable, verify that the virtual
environment is loading the expected OpenCV package:

```bash
python -c "import cv2; print(cv2.__file__); print(cv2.__version__); print(hasattr(cv2, 'VideoCapture'))"
```

The final value must be `True`. If it is `False`, repair the active environment:

```bash
python -m pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
python -m pip install --force-reinstall opencv-python-headless
```

Run those commands from `rpi-client` with its `.venv` activated. Also check that
there is no file or directory named `cv2.py` or `cv2` in the client directory.

## 6. Long-run heat test

Run the attendance client normally, then open a second SSH session and start the logger:
for 2 hours within 5mins interval

```bash
cd /home/pi/ai-iot-attendance/rpi-client
python tools/heat_test.py --output logs/heat-test.csv --interval 5 --duration 7200
```

for long run within 5mins interval

```bash
cd /home/pi/ai-iot-attendance/rpi-client
python tools/heat_test.py --output logs/heat-test.csv --interval 5
```

The logger records a row every five seconds for two hours. Use `--duration 0` to run until `Ctrl+C`.
The CSV includes UTC time, elapsed time, CPU temperature, CPU usage, memory usage, attendance process count,
and the Raspberry Pi throttling status. The file is flushed after every row, so data already recorded survives
an unexpected shutdown.

During the test, keep the camera and recognition workload representative of normal use. Review the CSV after
the test and check for rising temperature, `attendance_processes` becoming `0` or greater than `1`, and a
`throttled` value other than `0x0`. Raspberry Pi thermal throttling is indicated by the throttled status and
can cause the camera preview and recognition to slow down.

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
