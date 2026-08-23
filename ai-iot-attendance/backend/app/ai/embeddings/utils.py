"""
Utility functions for embedding math and serialization.
"""

import base64
import numpy as np


def encode_embedding(embedding: np.ndarray) -> str:
    """
    Convert a numpy array embedding to a Base64 string.
    This allows storing raw float arrays in Firebase Firestore.
    """
    if embedding is None:
        return ""
    # Ensure float32 format
    embedding_f32 = embedding.astype(np.float32)
    # Convert bytes to base64 string
    b64_bytes = base64.b64encode(embedding_f32.tobytes())
    return b64_bytes.decode("utf-8")


def decode_embedding(b64_string: str) -> np.ndarray:
    """
    Convert a Base64 string back into a 512-dimensional float32 numpy array.
    """
    if not b64_string:
        return np.array([])
        
    b64_bytes = b64_string.encode("utf-8")
    raw_bytes = base64.b64decode(b64_bytes)
    # Reconstruct the numpy array
    embedding = np.frombuffer(raw_bytes, dtype=np.float32)
    return embedding


def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Calculate the cosine similarity between two embeddings.
    Assumes embeddings are already L2 normalized.
    Returns a float between -1.0 and 1.0.
    """
    if emb1 is None or emb2 is None or emb1.size == 0 or emb2.size == 0:
        return 0.0
        
    # Since embeddings should be L2 normalized, cosine similarity is just the dot product
    return float(np.dot(emb1, emb2))


def calculate_representative_embedding(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    Calculate a single representative embedding from a list of embeddings.
    Averages them and L2 normalizes the result.
    """
    if not embeddings:
        raise ValueError("Cannot calculate representative embedding from an empty list.")
        
    # Stack arrays and calculate mean across the batch dimension
    mean_emb = np.mean(np.stack(embeddings), axis=0)
    
    # L2 normalize
    norm = np.linalg.norm(mean_emb)
    if norm > 0:
        mean_emb = mean_emb / norm
        
    return mean_emb
