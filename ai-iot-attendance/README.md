# AI-Integrated IoT Attendance System — Developer Guide

This guide will help developers set up and run the backend of the AI-Integrated IoT Attendance System from scratch. 

## Prerequisites

1. **Python 3.11+** installed on your machine.
2. A **Firebase** account and project (for Firestore database).
3. *(Windows Only)* **Visual Studio C++ Build Tools** installed (required to compile the `insightface` AI library).

---

## 1. Firebase Setup

This project uses Firebase Firestore as its primary database.

1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Create a new project (e.g., `ai-iot-attendance`).
3. In the left sidebar, navigate to **Build > Firestore Database** and click **Create database**. Start it in Test Mode for development.
4. Go to **Project Settings** (gear icon top left) > **Service accounts**.
5. Click **Generate new private key**. This will download a `.json` file.
6. Rename this file to `firebase-credentials.json` and place it in the `backend/` folder of this project.

> **WARNING:** Never commit `firebase-credentials.json` to Git! It contains your database secrets.

---

## 2. Environment Configuration

1. Navigate to the `backend/` directory.
2. Copy the `.env.example` file and rename it to `.env`.
3. Open `.env` and configure the variables:
   - `FIREBASE_PROJECT_ID`: Set this to your Firebase project ID.
   - `JWT_SECRET_KEY`: Change this to a random secure string.
   - `USE_MOCK_AI`: Set to `true` if you don't want to download the 300MB AI models during development. Set to `false` to use the real ArcFace/SCRFD models.

---

## 3. Python Virtual Environment Setup

Open a terminal and navigate to the `backend/` directory, then run the following commands:

**Windows:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

---

## 4. Installing Dependencies

With the virtual environment activated, install the required packages:

```powershell
pip install -r requirements.txt
```

> **IMPORTANT BUG FIX NOTE:** There is a known compatibility issue between the `passlib` library and `bcrypt >= 4.0.0`. This project requires `bcrypt==3.2.2`. If you encounter a `ValueError: password cannot be longer than 72 bytes` during startup, ensure you explicitly run:
> `pip install bcrypt==3.2.2`

---

## 5. Running the Backend Server

Start the FastAPI server using Uvicorn:

```powershell
uvicorn app.main:app --reload
```

When the server starts, it will automatically connect to Firebase and bootstrap an initial Admin account based on the credentials in your `.env` file (Default: `admin@university.edu` / `changeme123`).

If `USE_MOCK_AI=false`, the server will take an extra 1-2 minutes on the very first run to download the ONNX face recognition models into the `models/` directory.

---

## 6. Testing the API (Workflow)

FastAPI automatically generates an interactive documentation dashboard. Open your browser and go to:
**http://localhost:8000/docs**

### API Workflow:

1. **Login (Authenticate)**
   - Find the `POST /api/v1/auth/login` endpoint.
   - Click **"Try it out"** and enter the admin credentials from your `.env` file.
   - Click **Execute**.
   - Copy the `access_token` from the response.
   - Scroll to the very top of the page, click the green **"Authorize"** button, paste the token, and click Authorize.

2. **Create a Student**
   - Go to `POST /api/v1/students/`, click "Try it out", and create a dummy student (e.g., student_id `"1001"`).

3. **Create a Course**
   - Go to `POST /api/v1/courses/`, click "Try it out", and create a course. Note the `course_id`.

4. **Enroll the Student in the Course**
   - Go to `POST /api/v1/courses/{course_id}/enroll`, paste the `course_id`, and provide the `student_id`.

5. **Start an Attendance Session**
   - Go to `POST /api/v1/attendance/sessions`. Pass the `course_id` to start a session. Note the `session_id`.

6. **Enroll Face & Test Recognition**
   - **Enroll:** Go to `POST /api/v1/faces/enroll/{student_id}` and upload a photo of a face. The AI pipeline will extract the embedding and save it to Firebase.
   - **Recognize:** Go to `POST /api/v1/faces/recognize`, upload another photo of that same person. The system will match it against the database and return the matched `student_id` and confidence score.

7. **View Reports**
   - Go to `GET /api/v1/reports/course/{course_id}` to see updated attendance stats.
