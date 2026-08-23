# Cursor Build Prompt — AI-Integrated IoT Attendance System

## 1. Project Objective

Build a complete **AI-Integrated IoT Attendance System** for a university classroom.

The system should automatically identify students using facial recognition, mark their attendance, store attendance data in the cloud, and provide a web dashboard for teachers.

The system should be designed as a **real working prototype**, not just a UI mockup.

The core workflow is:

```text
Camera
   ↓
Face Detection
   ↓
Face Recognition
   ↓
Liveness / Anti-Spoofing
   ↓
Student Identification
   ↓
Attendance Recording
   ↓
Firebase / Cloud Database
   ↓
Teacher Dashboard
```

---

# 2. Important Requirement

Do **NOT** train a face-recognition neural network from scratch.

Use a **pre-trained face-recognition model**.

The system should use the pre-trained model to generate facial embeddings.

Student enrollment should work like this:

```text
Student Registration
        ↓
Capture several face images
        ↓
Face Detection
        ↓
Pre-trained Face Recognition Model
        ↓
Generate Face Embedding
        ↓
Store Embedding + Student ID
```

During attendance:

```text
Live Camera
     ↓
Detect Face
     ↓
Generate Embedding
     ↓
Compare with Stored Embeddings
     ↓
Similarity Above Threshold?
     ↓
YES → Identify Student
     ↓
Mark Attendance
```

Clearly separate **model training** from **student enrollment**.

---

# 3. Recommended Technology Stack

Use the following architecture unless there is a strong technical reason to change it.

## AI / Computer Vision

* Python
* OpenCV
* MediaPipe or YOLO for face detection
* FaceNet / MobileFaceNet / ArcFace for face recognition
* NumPy
* A suitable Python face-embedding library
* Liveness detection / anti-spoofing

Prefer a lightweight recognition model because the system is intended to run on a Raspberry Pi.

## Edge Device

Use:

* Raspberry Pi
* Raspberry Pi Camera or USB webcam

The Raspberry Pi should perform the camera capture and AI inference.

## IoT

Use:

* ESP32 Development Board

The ESP32 should be treated as an IoT/peripheral controller rather than the primary deep-learning processor.

It can be used for:

* OLED display
* RFID reader
* additional sensors/peripherals
* communication with the Raspberry Pi

Do not attempt to run a heavy face-recognition model directly on the ESP32 if it is not technically suitable.

## Backend

Use:

* Python
* Flask or FastAPI

Prefer **FastAPI** if there is no compatibility issue.

The backend should expose APIs for:

* student registration
* face enrollment
* attendance
* student management
* attendance history
* reports
* authentication

## Database / Cloud

Use:

* Firebase

Use Firebase for storing:

* student information
* face embeddings or suitable references
* attendance records
* timestamps
* classroom/course information

Do not store unnecessary raw facial images permanently unless required.

## Frontend

Use:

* React
* Vite
* Material UI or another clean component library
* Firebase/API integration

---

# 4. Project Structure

Create a clean monorepo structure:

```text
ai-iot-attendance/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── App.jsx
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── core/
│   │   └── main.py
│   │
│   ├── ai/
│   │   ├── detection/
│   │   ├── recognition/
│   │   ├── liveness/
│   │   └── embeddings/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── raspberry-pi/
│   ├── camera/
│   ├── ai_client/
│   ├── attendance_client/
│   └── main.py
│
├── esp32/
│   └── attendance_controller/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── setup.md
│
├── .env.example
├── README.md
└── docker-compose.yml
```

Keep AI code separated from API code.

Do not put everything into one Python file.

---

# 5. User Roles

Implement at least two roles:

## Admin

Admin can:

* add students
* edit students
* delete students
* enroll faces
* view all attendance
* manage courses/classes
* manage teachers

## Teacher

Teacher can:

* log in
* select a course/class
* start an attendance session
* view live attendance
* view attendance history
* view student attendance percentages
* generate reports

Students do not need a full login system for the first prototype.

---

# 6. Student Registration

Create a student registration page.

Fields:

```text
Student ID
Name
Department
Batch
Email
Course/Class
```

After creating the student, provide:

```text
Enroll Face
```

button.

The enrollment workflow should:

1. Open the camera.
2. Detect the student's face.
3. Ask the user to move slightly if necessary.
4. Capture multiple valid frames.
5. Reject frames where:

   * no face exists
   * multiple faces exist
   * face is too small
   * image quality is too poor
6. Generate embeddings.
7. Store a stable representative embedding.

Do not blindly store every frame.

Calculate a suitable representative embedding from multiple valid samples.

---

# 7. Face Recognition

Implement a dedicated recognition service.

Input:

```text
camera frame
```

Output:

```json
{
  "student_id": "20220104064",
  "name": "Student Name",
  "confidence": 0.92,
  "matched": true
}
```

Use an appropriate distance/similarity metric depending on the selected model.

Do not hard-code an arbitrary confidence threshold.

Make the threshold configurable:

```env
FACE_MATCH_THRESHOLD=...
```

Document how the threshold should be calibrated using validation data.

---

# 8. Liveness Detection

Implement anti-spoofing as a separate module.

The goal is to prevent:

```text
Printed photo
Mobile phone photo
Static image
```

from being accepted as a student.

For the prototype, use a practical lightweight approach.

Possible techniques:

* blink detection
* head movement
* temporal consistency
* facial landmark movement
* lightweight anti-spoofing model

Design the interface so the liveness implementation can later be replaced by a stronger model.

Example:

```python
result = liveness_detector.check(frames)

if result.is_live:
    continue_recognition()
else:
    reject_attempt()
```

Do not claim that basic blink detection provides perfect anti-spoofing.

---

# 9. Attendance Rules

Attendance should NOT simply be recorded every time a face appears.

Implement session-based attendance.

Example:

```text
Teacher starts:
CSE XXXX
Section: A
Date: 2026-08-24
Start: 10:00 AM
```

Students detected during that session are marked present.

Prevent duplicate records.

For example:

```text
Student A enters
→ Present

Student A appears again 10 seconds later
→ Do NOT create another attendance record
```

Use:

```text
course_id
student_id
session_id
date
timestamp
status
```

as appropriate.

---

# 10. Attendance Status

Initially support:

```text
Present
Absent
Late
Unknown
Rejected
```

The teacher should be able to configure the late threshold.

Example:

```text
Class starts: 10:00
Late after: 10:15
```

If the student enters after the configured threshold:

```text
Late
```

---

# 11. Teacher Dashboard

Build a professional university-style dashboard.

Dashboard should display:

### Today's statistics

```text
Total Students
Present
Absent
Late
Attendance Percentage
```

### Live Attendance

Display:

```text
Student ID
Name
Time
Status
Recognition Confidence
```

### Student attendance

Show:

```text
Student
Total Classes
Present
Absent
Late
Percentage
```

### Reports

Provide:

* daily report
* weekly report
* monthly report
* course-wise report
* student-wise report

Allow CSV export.

---

# 12. Live Attendance UI

Create a live attendance screen.

Example:

```text
┌───────────────────────────────────────────────┐
│ CSE XXXX — Attendance Session                │
├───────────────────────────────────────────────┤
│                                               │
│             CAMERA PREVIEW                   │
│                                               │
│              [ Student Face ]                │
│                                               │
├───────────────────────────────────────────────┤
│ Recently Recognized                          │
│                                               │
│ ✓ 20220104064  Student Name   10:03:21       │
│ ✓ 20220104065  Student Name   10:04:02       │
│ ✕ Unknown       —             10:04:15       │
└───────────────────────────────────────────────┘
```

Use clear visual states for:

* recognized
* unknown
* spoof detected
* processing

---

# 13. Firebase Database Design

Design the database logically.

Suggested collections:

```text
students
teachers
courses
enrollments
attendance_sessions
attendance_records
face_embeddings
```

Example student:

```json
{
  "studentId": "20220104064",
  "name": "Student Name",
  "department": "CSE",
  "batch": "XX",
  "email": "student@example.com"
}
```

Example attendance record:

```json
{
  "sessionId": "SESSION_ID",
  "studentId": "20220104064",
  "status": "present",
  "timestamp": "2026-08-24T10:03:21"
}
```

Do not expose sensitive credentials in frontend code.

---

# 14. Security

Implement basic security properly.

Requirements:

* environment variables for secrets
* Firebase credentials must not be committed
* authentication for teachers/admins
* role-based access
* backend validation
* input validation
* API error handling
* no hard-coded API keys/secrets
* avoid storing unnecessary biometric information
* do not expose all student data publicly

Create:

```text
.env.example
```

with placeholder values.

---

# 15. Raspberry Pi Workflow

The Raspberry Pi application should:

1. Initialize camera.
2. Capture frames.
3. Detect faces.
4. Run recognition.
5. Perform liveness verification.
6. Send recognized student information to backend.
7. Receive attendance response.
8. Display status locally if OLED is connected.

Example:

```text
Camera
 ↓
Frame
 ↓
Face Detection
 ↓
Liveness
 ↓
Face Recognition
 ↓
Student ID
 ↓
FastAPI
 ↓
Firebase
```

The Raspberry Pi should be able to operate locally even if the dashboard is temporarily unavailable.

Queue attendance events locally and synchronize them when the network becomes available.

---

# 16. ESP32 Workflow

Do not unnecessarily duplicate AI processing between ESP32 and Raspberry Pi.

The ESP32 should handle IoT/peripheral responsibilities.

Possible architecture:

```text
ESP32
 ├── OLED
 ├── RFID
 └── Peripheral communication
          ↓
     Raspberry Pi
          ↓
        AI
```

If RFID is enabled:

```text
RFID Card
   ↓
ESP32
   ↓
Raspberry Pi
   ↓
Verification
```

Make RFID/fingerprint optional so the core face-recognition system works without them.

---

# 17. Offline Handling

The system should not completely fail if the internet goes down.

Implement:

```text
Internet Available
→ Send attendance immediately

Internet Unavailable
→ Store event locally
→ Retry later
→ Synchronize with Firebase
```

Use a small local SQLite database or JSON queue on the Raspberry Pi.

Avoid duplicate synchronization.

---

# 18. Error Handling

Handle:

```text
No camera
Camera disconnected
No face detected
Multiple faces detected
Unknown face
Spoof detected
Poor lighting
Network unavailable
Firebase unavailable
Invalid student
Duplicate attendance
AI model unavailable
```

Display useful messages instead of crashing.

---

# 19. Development Strategy

Build the project in phases.

## Phase 1 — Backend

First create:

* FastAPI project
* Firebase integration
* student APIs
* attendance APIs
* authentication
* database models

Test everything with Postman/cURL.

## Phase 2 — AI

Implement:

* face detection
* face enrollment
* embedding generation
* face matching
* threshold configuration

Test using recorded images/videos before connecting the full system.

## Phase 3 — Liveness

Implement:

* liveness detection
* spoof rejection

Test using:

* real face
* printed photo
* phone screen

## Phase 4 — Raspberry Pi

Connect:

```text
Camera → Raspberry Pi → AI → Backend
```

## Phase 5 — Frontend

Build:

* login
* dashboard
* students
* enrollment
* live attendance
* reports

## Phase 6 — ESP32

Add:

* OLED
* RFID
* peripheral communication

## Phase 7 — Integration

Test the complete system.

---

# 20. Testing Requirements

Create automated tests where practical.

Test at least:

### Recognition

```text
Known student → Correct identity
Unknown person → Unknown
Multiple people → Handle correctly
```

### Liveness

```text
Real face → Accept
Printed photo → Reject
Phone photo → Reject
```

### Attendance

```text
First recognition → Present
Repeated recognition → No duplicate
Late arrival → Late
Unknown person → No attendance
```

### Network

```text
Internet available → Sync
Internet unavailable → Queue locally
Internet restored → Sync queue
```

---

# 21. UI Design

The UI should look like a real university management system.

Use:

* clean sidebar
* responsive layout
* dashboard cards
* tables
* charts
* modal dialogs
* toast notifications
* loading states
* empty states
* error states

Do not create an unnecessarily flashy design.

Prioritize usability.

---

# 22. Important AI Architecture Decision

Do not create fake AI.

Do NOT implement something like:

```python
if student_name == "Arnob":
    attendance = True
```

or random confidence values.

Every recognition result must come from the actual face-recognition pipeline.

If a model cannot run on the development machine, create a clearly separated development/mock adapter, but keep the production AI implementation separate.

Example:

```text
RecognitionService
    │
    ├── RealFaceRecognitionService
    │
    └── MockRecognitionService
```

The mock implementation must never be presented as the actual AI.

---

# 23. Configuration

Put configurable values into environment variables/configuration.

Examples:

```env
FACE_MATCH_THRESHOLD=
LIVENESS_ENABLED=true
CAMERA_INDEX=0
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY=
API_BASE_URL=
ATTENDANCE_COOLDOWN_SECONDS=
LATE_THRESHOLD_MINUTES=
```

Do not hard-code these values throughout the application.

---

# 24. Documentation

Create a comprehensive `README.md`.

It must explain:

1. Project overview
2. Architecture
3. Technologies
4. Installation
5. Environment configuration
6. Firebase setup
7. AI model setup
8. Student enrollment
9. Running backend
10. Running frontend
11. Running Raspberry Pi client
12. Running ESP32
13. API documentation
14. Troubleshooting
15. Security considerations

Also create:

```text
docs/architecture.md
docs/api.md
docs/setup.md
```

---

# 25. Build Rules for Cursor

Follow these rules strictly:

### Rule 1

Do not build the entire project blindly in one step.

Build it module-by-module and verify each module before moving to the next.

### Rule 2

Before installing a library, check whether it is compatible with:

* Python version
* Raspberry Pi architecture
* operating system

### Rule 3

Prefer stable, well-maintained libraries.

### Rule 4

Keep AI, backend, frontend, Raspberry Pi, and ESP32 code modular.

### Rule 5

Do not use fake data once the actual Firebase/backend integration has been implemented.

### Rule 6

Do not expose credentials.

### Rule 7

Add meaningful comments around complicated AI logic.

### Rule 8

Do not silently change the architecture.

If a proposed technology needs to change, explain why first.

### Rule 9

After completing each phase, run tests and fix errors before proceeding.

### Rule 10

Do not mark a feature as completed until it actually works.

---

# 26. First Task for Cursor

Start by analyzing this specification.

Do **not** immediately generate the entire project.

First:

1. Analyze the architecture.
2. Identify potential technical problems.
3. Identify incompatible libraries if any.
4. Propose the exact AI model/library combination.
5. Propose the Firebase database structure.
6. Propose the API structure.
7. Propose the final folder structure.
8. Explain how Raspberry Pi and ESP32 will communicate.
9. Explain the student enrollment workflow.
10. Explain the attendance workflow.
11. Identify what can run locally and what requires cloud connectivity.

Then wait for approval before implementing.

Once approved, implement **Phase 1: Backend + Firebase integration** first.

After each phase:

```text
Implement
    ↓
Run
    ↓
Test
    ↓
Fix errors
    ↓
Explain what was completed
    ↓
Proceed to next phase
```

The final result must be a **functional AI + IoT attendance prototype**, not merely a frontend demonstration.
