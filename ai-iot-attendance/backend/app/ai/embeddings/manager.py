"""
Embedding Manager — handles storage, retrieval, and caching of face embeddings.
"""

import logging
from datetime import datetime, timezone
from google.cloud.firestore_v1.base_query import FieldFilter
import numpy as np

from app.core.firebase import get_db
from .utils import encode_embedding, decode_embedding, cosine_similarity

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manages syncing face embeddings with Firebase and caching them locally
    for fast in-memory similarity comparisons during attendance.
    """

    def __init__(self):
        # Local cache of enrolled embeddings: {student_id: np.ndarray}
        self._cache: dict[str, np.ndarray] = {}
        self._cache_loaded = False

    def _get_db(self):
        return get_db()

    def load_cache(self):
        """
        Load all embeddings from Firebase into memory.
        Typically called on backend startup or RPi sync.
        """
        db = self._get_db()
        docs = db.collection("face_embeddings").stream()
        
        count = 0
        self._cache.clear()
        
        for doc in docs:
            data = doc.to_dict()
            student_id = data.get("student_id")
            b64_emb = data.get("embedding")
            
            if student_id and b64_emb:
                self._cache[student_id] = decode_embedding(b64_emb)
                count += 1
                
        self._cache_loaded = True
        logger.info(f"Loaded {count} face embeddings into local cache.")

    def get_embedding(self, student_id: str) -> np.ndarray | None:
        """Get a specific student's embedding from cache."""
        if not self._cache_loaded:
            self.load_cache()
        return self._cache.get(student_id)

    def save_enrollment(self, student_id: str, representative_emb: np.ndarray, num_samples: int, quality: float):
        """
        Save a finalized face enrollment to Firebase and update local cache.
        """
        db = self._get_db()
        
        # Check if already enrolled, if so, we'll overwrite it
        docs = db.collection("face_embeddings").where(
            filter=FieldFilter("student_id", "==", student_id)
        ).get()
        
        now = datetime.now(timezone.utc)
        
        data = {
            "student_id": student_id,
            "embedding": encode_embedding(representative_emb),
            "num_samples": num_samples,
            "quality": quality,
            "updated_at": now
        }
        
        if docs:
            # Update existing
            doc_ref = docs[0].reference
            data["created_at"] = docs[0].to_dict().get("created_at", now)
            doc_ref.update(data)
        else:
            # Create new
            data["created_at"] = now
            db.collection("face_embeddings").add(data)
            
        # Update local cache
        self._cache[student_id] = representative_emb
        
        # Also update the student document to mark face_enrolled = true
        student_docs = db.collection("students").where(
            filter=FieldFilter("student_id", "==", student_id)
        ).get()
        
        if student_docs:
            student_docs[0].reference.update({"face_enrolled": True})
            
        logger.info(f"Saved face enrollment for student {student_id}.")

    def find_best_match(self, query_emb: np.ndarray, threshold: float = 0.45) -> tuple[str | None, float]:
        """
        Compare a query embedding against all enrolled students in the cache.
        Returns the (student_id, confidence) of the best match above the threshold,
        or (None, 0.0) if no match is found.
        """
        if not self._cache_loaded:
            self.load_cache()
            
        if not self._cache:
            return None, 0.0
            
        best_student = None
        best_score = -1.0
        
        for student_id, stored_emb in self._cache.items():
            score = cosine_similarity(query_emb, stored_emb)
            if score > best_score:
                best_score = score
                best_student = student_id
                
        if best_score >= threshold:
            return best_student, best_score
            
        return None, best_score

# Global singleton instance
embedding_manager = EmbeddingManager()
