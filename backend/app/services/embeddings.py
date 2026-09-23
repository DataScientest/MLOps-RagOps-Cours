import httpx
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.utils.hashing import md5_hash
from app.utils.cache import get_json, set_json

_CACHE_TTL = 3600  # seconds

async def _request_embeddings(texts: List[str]) -> Optional[List[dict]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{settings.PROXY_URL}/v1/embeddings",
            json={"model": settings.EMBEDDING_MODEL_NAME, "input": texts},
            headers={"Content-Type": "application/json"}
        )
        if r.status_code != 200:
            logger.error(f"Embedding request failed: {r.status_code} - {r.text}")
            return None
        return r.json().get("data", [])

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate sentence embeddings via LiteLLM (TEI backend), with Redis cache.
    Uses utils.hashing + utils.cache for keys & JSON storage.
    """
    results: List[Optional[List[float]]] = [None] * len(texts)
    uncached, idxs = [], []

    # 1) cache lookups
    for i, t in enumerate(texts):
        key = f"embedding:{md5_hash(t)}"
        cached_vec = get_json(key)
        if cached_vec is not None:
            results[i] = cached_vec
        else:
            uncached.append(t)
            idxs.append(i)

    # 2) remote call if needed
    if uncached:
        data = await _request_embeddings(uncached)
        if data is None:
            # Fail closed: return only cached results
            return [v for v in results if v is not None]

        for i, emb in zip(idxs, data):
            vec = emb.get("embedding", emb)
            if isinstance(vec, dict) and "default" in vec:
                vec = vec["default"]
            results[i] = vec
            set_json(f"embedding:{md5_hash(texts[i])}", vec, _CACHE_TTL)

    # 3) flatten and filter
    return [v for v in results if v is not None]
