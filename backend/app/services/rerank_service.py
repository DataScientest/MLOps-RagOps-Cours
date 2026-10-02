import httpx
import numpy as np
from typing import Dict, Any
from app.models.rerank import RerankRequest
from app.services.search_service import search_chunks
from app.core.config import settings

async def search_with_reranking(req: RerankRequest) -> Dict[str, Any]:
    base_results = await search_chunks(req.query, req.k, use_embeddings=True)
    hits = base_results.get("hits", [])
    if not hits:
        return {"query": req.query, "chunks": [], "rerank_scores": [], "total_chunks_found": 0, "search_method": "hybrid+rerank"}

    documents = [chunk["content"] for chunk in hits]

    headers = {"Authorization": f"Bearer {settings.PROXY_KEY}"}

    async with httpx.AsyncClient(timeout=60) as client:
        q_resp = await client.post(
            f"{settings.PROXY_URL}/v1/embeddings",
            json={"model": settings.EMBEDDING_MODEL_NAME, "input": req.query},
            headers=headers
        )
        d_resp = await client.post(
            f"{settings.PROXY_URL}/v1/embeddings",
            json={"model": settings.EMBEDDING_MODEL_NAME, "input": documents},
            headers=headers
        )

    query_embedding = q_resp.json()["data"][0]["embedding"]
    doc_embeddings = [d["embedding"] for d in d_resp.json()["data"]]

    def cosine_sim(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scores = [cosine_sim(query_embedding, emb) for emb in doc_embeddings]
    scored_chunks = [{"chunk": c, "score": s} for c, s in zip(hits, scores)]
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": req.query,
        "chunks": [sc["chunk"] for sc in scored_chunks],
        "rerank_scores": [sc["score"] for sc in scored_chunks],
        "total_chunks_found": base_results.get("total", len(hits)),
        "search_method": "hybrid+rerank"
    }
