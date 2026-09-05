"""
Face enrollment and recognition routes.

Integrates with the AI Pipeline to process images, generate embeddings,
and perform face matching.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import cv2
import numpy as np

from app.api.deps import get_current_user, require_admin
from app.schemas.auth import UserInToken
from app.ai.pipeline import ai_pipeline
from app.ai.embeddings.manager import embedding_manager
from app.ai.embeddings.utils import calculate_representative_embedding
from app.core.config import settings

router = APIRouter(prefix="/faces", tags=["Face Recognition"])


async def _read_image(file: UploadFile) -> np.ndarray:
    """Helper to read an uploaded image file into an OpenCV BGR numpy array."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    return img


@router.post("/enroll/{student_id}")
async def enroll_face(
    student_id: str,
    file: UploadFile = File(...),
    _: UserInToken = Depends(require_admin),
):
    """
    Upload a face image for enrollment.
    
    This endpoint should be called multiple times (e.g., 5 times) with different
    photos of the student to build a robust representative embedding.
    """
    img = await _read_image(file)
    
    # Run image through AI pipeline
    result = ai_pipeline.process_frame(img)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    embedding = result["embedding"]
    
    # In a real app, we'd temporarily store these in a session until we get 5 valid samples,
    # then calculate the representative. For simplicity here, we simulate getting
    # multiple samples by storing the one and pretending it's the final representative,
    # or you can implement a multi-upload endpoint.
    
    # We will just directly save this embedding as the representative one for now.
    # A real UI would upload an array of files to a batch endpoint.
    embedding_manager.save_enrollment(
        student_id=student_id,
        representative_emb=embedding,
        num_samples=1,
        quality=result["face_data"].get("det_score", 0.99)
    )
    
    return {
        "status": "success",
        "message": f"Face enrolled for student {student_id}.",
        "student_id": student_id,
        "quality": result["face_data"].get("det_score", 0.99)
    }


@router.get("/status/{student_id}")
async def get_enrollment_status(
    student_id: str,
    _: UserInToken = Depends(get_current_user),
):
    """Check if a student has a face enrollment."""
    # We can check the local cache
    emb = embedding_manager.get_embedding(student_id)
    if emb is not None:
        return {
            "enrolled": True,
            "student_id": student_id,
        }
    
    # Fallback to DB check
    from app.core.firebase import get_db
    db = get_db()
    docs = db.collection("face_embeddings").where("student_id", "==", student_id).limit(1).get()
    
    if docs:
        data = docs[0].to_dict()
        return {
            "enrolled": True,
            "student_id": student_id,
            "num_samples": data.get("num_samples", 0),
            "quality": data.get("quality", 0.0),
        }

    return {
        "enrolled": False,
        "student_id": student_id,
    }


@router.delete("/{student_id}", dependencies=[Depends(require_admin)])
async def delete_enrollment(student_id: str):
    """Remove a student's face enrollment."""
    from app.core.firebase import get_db
    db = get_db()
    docs = db.collection("face_embeddings").where("student_id", "==", student_id).get()

    if not docs:
        return {"message": f"No face enrollment found for student '{student_id}'."}

    for doc in docs:
        doc.reference.delete()
        
    # Remove from cache
    if student_id in embedding_manager._cache:
        del embedding_manager._cache[student_id]
        
    # Update student status
    student_docs = db.collection("students").where("student_id", "==", student_id).get()
    if student_docs:
        student_docs[0].reference.update({"face_enrolled": False})

    return {"message": f"Face enrollment removed for student '{student_id}'."}


@router.post("/recognize")
async def recognize_face(
    file: UploadFile = File(...),
    _: UserInToken = Depends(get_current_user),
):
    """
    Submit a camera frame for face recognition.
    Returns the identified student (if matched) with confidence score.
    """
    img = await _read_image(file)
    
    # 1. Process frame
    result = ai_pipeline.process_frame(img)
    
    if not result["success"]:
        payload = {
            "matched": False,
            "message": result["message"]
        }
        if settings.liveness_enabled and "liveness_score" in result:
            payload["liveness_score"] = float(result["liveness_score"])
        return payload

    embedding = result["embedding"]
    
    # 2. Match against cache
    threshold = settings.face_match_threshold
    student_id, confidence = embedding_manager.find_best_match(embedding, threshold=threshold)
    
    if student_id:
        response = {
            "matched": True,
            "student_id": student_id,
            "confidence": confidence,
            "message": f"Matched student {student_id}"
        }
        if settings.liveness_enabled:
            response["liveness_score"] = float(result.get("liveness_score", 1.0))
        return response

    response = {
        "matched": False,
        "confidence": confidence,
        "message": "Face detected, but no matching student found."
    }
    if settings.liveness_enabled:
        response["liveness_score"] = float(result.get("liveness_score", 1.0))
    return response
