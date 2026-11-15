import numpy as np
from typing import Dict, List, Optional

_SENTENCE_MODEL = None
_EMBEDDINGS_CACHE: Dict[str, np.ndarray] = {}


def get_embedding_model():
    """
    Lazy singleton loader for the sentence-transformers model.
    Only instantiated on first demand so tests and server startup remain fast.
    """
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _SENTENCE_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _SENTENCE_MODEL


def get_embedding(text: str, use_cache: bool = True) -> np.ndarray:
    """
    Computes and optionally caches the dense vector representation of a text string.
    """
    cleaned = text.strip()
    cache_key = cleaned.lower()

    if use_cache and cache_key in _EMBEDDINGS_CACHE:
        return _EMBEDDINGS_CACHE[cache_key]

    model = get_embedding_model()
    # Normalize embeddings for direct dot product cosine similarity
    emb = model.encode(cleaned, normalize_embeddings=True)
    emb = np.array(emb, dtype=np.float32)

    if use_cache:
        _EMBEDDINGS_CACHE[cache_key] = emb

    return emb


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calculates cosine similarity between two 1D normalized numpy arrays.
    Returns a score clamped between 0.0 and 1.0.
    """
    if vec_a is None or vec_b is None or len(vec_a) == 0 or len(vec_b) == 0:
        return 0.0
    
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
    return max(0.0, min(1.0, sim))


def compute_text_similarity(text_a: str, text_b: str, use_cache: bool = False) -> float:
    """
    Direct helper to compute semantic similarity between two arbitrary texts.
    For long documents (JD vs Resume), caching is disabled by default to save memory.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vec_a = get_embedding(text_a, use_cache=use_cache)
    vec_b = get_embedding(text_b, use_cache=use_cache)
    return cosine_similarity(vec_a, vec_b)


def compute_skill_similarity(skill_a: str, skill_b: str) -> float:
    """
    Computes semantic similarity between two skill strings with caching enabled.
    """
    if not skill_a or not skill_b:
        return 0.0
    if skill_a.strip().lower() == skill_b.strip().lower():
        return 1.0
    vec_a = get_embedding(skill_a, use_cache=True)
    vec_b = get_embedding(skill_b, use_cache=True)
    return cosine_similarity(vec_a, vec_b)
