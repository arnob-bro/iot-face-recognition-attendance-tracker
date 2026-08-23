"""
FastAPI application entry point.

Configures:
- CORS middleware
- Application lifespan (Firebase init/close, admin bootstrap)
- All API route registrations under /api/v1/
- Global exception handling
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.firebase import init_firebase, close_firebase
from app.api import auth, students, courses, attendance, faces, reports, dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — runs startup and shutdown logic.

    Startup:
      1. Initialize Firebase connection
      2. Bootstrap admin account if none exists

    Shutdown:
      1. Close Firebase connection
    """
    # --- Startup ---
    logger.info("Starting AI-IoT Attendance System backend...")
    init_firebase()

    # Bootstrap admin account on first run
    from app.services.auth_service import bootstrap_admin

    await bootstrap_admin(
        email=settings.admin_email,
        password=settings.admin_password,
        name=settings.admin_name,
    )

    logger.info(f"Backend ready at {settings.api_base_url}")
    logger.info(f"API docs: {settings.api_base_url}/docs")

    yield

    # --- Shutdown ---
    close_firebase()
    logger.info("Backend shut down.")


# Create the FastAPI app
app = FastAPI(
    title="AI-IoT Attendance System",
    description=(
        "Backend API for the AI-Integrated IoT Attendance System. "
        "Provides student management, face enrollment, attendance tracking, "
        "and reporting for university classrooms."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent raw stack traces
    from reaching the client. Logs the full error server-side.
    """
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later."
        },
    )


# --- Register API Routers ---
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(students.router, prefix=API_PREFIX)
app.include_router(courses.router, prefix=API_PREFIX)
app.include_router(attendance.router, prefix=API_PREFIX)
app.include_router(faces.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


# --- Health Check ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-iot-attendance-backend",
        "version": "1.0.0",
    }


# --- Run with uvicorn ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
