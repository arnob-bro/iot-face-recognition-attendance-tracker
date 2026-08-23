# Phase 2: AI Pipeline Implementation

I have successfully completed the implementation of Phase 2, integrating the core face detection and recognition architecture into the backend.

## What was built

1. **AI Pipeline Orchestrator** (`backend/app/ai/pipeline.py`)
   - Created the central `AIPipeline` class that coordinates the detection, liveness (placeholder for Phase 3), and recognition steps.
   - Designed it to dynamically switch between **Real** AI models (InsightFace) and **Mock** adapters based on your `.env` configuration (`USE_MOCK_AI=true`).

2. **Detection & Recognition Modules** (`backend/app/ai/`)
   - Implemented abstract base interfaces for both detection and recognition.
   - Implemented **SCRFDDetector** for face detection (locates faces and 5-point landmarks).
   - Implemented **ArcFaceRecognizer** for embedding generation (creates a 512-dimensional vector identifying the face).
   - Implemented **MockDetector** and **MockRecognizer** to allow development and testing on your Windows machine without downloading heavy ONNX models or requiring a GPU.

3. **Embedding Manager** (`backend/app/ai/embeddings/manager.py`)
   - Built a caching layer that synchronizes with Firebase on startup.
   - Converts 512-dimensional numpy arrays to Base64 strings for Firebase storage, and decodes them back to numpy arrays for fast in-memory similarity matching using Cosine Similarity.
   - Includes logic to calculate a "representative" embedding by averaging multiple photos.

4. **API Integration** (`backend/app/api/faces.py`)
   - Updated the `/faces/enroll/{student_id}` endpoint. Now when you upload a photo, it passes through the AI pipeline, generates an embedding, and stores it in Firebase.
   - Updated the `/faces/recognize` endpoint. Now when a frame is uploaded, it generates a live embedding and compares it against all enrolled students in the cache to find a match above the threshold (default `0.45`).

## How to Test

Since you have `USE_MOCK_AI=true` in your `.env`, you can test this right now from your browser without needing an actual camera or heavy AI models!

1. Make sure your server is running (`uvicorn app.main:app --reload` from the `backend` folder).
2. Go to **http://localhost:8000/docs**
3. **Login** using the admin credentials to get your token and click Authorize.
4. **Create a student** via `POST /api/v1/students/` (e.g., student ID `1001`).
5. **Enroll a face** via `POST /api/v1/faces/enroll/1001`. The API docs will let you upload an image file. Because mock mode is on, it will pretend it found a face and successfully save a mock embedding!
6. **Test Recognition** via `POST /api/v1/faces/recognize`. Upload another image file. The mock pipeline will process it, compare it against the cache, and return a match result!

> [!TIP]
> When we are ready to deploy to the Raspberry Pi (or if you want to test the real models on your PC), you just need to change `USE_MOCK_AI=false` in `.env`. The system will automatically download the InsightFace models and perform real face recognition!





1. Login (Authenticate)

Find the POST /api/v1/auth/login endpoint.
Click "Try it out" and enter the admin credentials you set in your .env file (e.g., admin@university.edu and changeme123).
Click Execute.
In the response, copy the access_token.
Scroll to the very top of the page, click the green "Authorize" button, paste the token, and click Authorize. Now you are "logged in" as the admin!
2. Create a Student

Go to POST /api/v1/students/, click "Try it out", and create a dummy student (give them a student_id like "123456").
3. Create a Course

Go to POST /api/v1/courses/, click "Try it out", and create a course (e.g., "AI-101"). Take note of the course_id returned in the response.
4. Enroll the Student

Go to POST /api/v1/courses/{course_id}/enroll, paste the course_id into the path parameter, and provide the student_id in the body.
5. Start an Attendance Session

Go to POST /api/v1/attendance/sessions. Pass the course_id to start a session. Take note of the session_id.
6. Simulate Face Recognition (Record Attendance)

Normally, the Raspberry Pi calls this API when it sees a face. You can simulate it manually!
Go to POST /api/v1/attendance/sessions/{session_id}/record. Use the session_id and pass the student_id.
7. View Reports

Go to GET /api/v1/reports/course/{course_id} to see the updated attendance stats!
