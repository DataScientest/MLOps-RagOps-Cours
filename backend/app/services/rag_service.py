from typing import Dict, Any, List
from app.core.config import settings
from app.core.clients import meili_client
from app.core.logging import logger
from app.services.embeddings import generate_embeddings
from app.services.llm_service import generate_rag_answer
from app.utils.hashing import md5_hash
from app.utils.cache import get_json, set_json

def _select_chunks(hits: List[dict], k: int) -> List[dict]:
    # Limit 2 chunks per document to keep context compact
    selected, per_doc = [], {}
    for h in hits:
        doc_id = h.get("document_id", "unknown")
        per_doc[doc_id] = per_doc.get(doc_id, 0)
        if per_doc[doc_id] < 2:
            selected.append(h)
            per_doc[doc_id] += 1
        if len(selected) >= k:
            break
    return selected

async def rag_search(query: str, k: int, use_embeddings: bool = True) -> Dict[str, Any]:
    """Retrieve chunks (hybrid if available) and synthesize an answer via LLM. Cached 10 min."""
    cache_key = f"rag:{md5_hash(f'{query}:{k}:{use_embeddings}')}"
    cached = get_json(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    chunks_index = meili_client.get_index(settings.CHUNKS_INDEX)
    search_method = "text"

    # Try hybrid search with query vector
    if use_embeddings:
        try:
            q_emb = await generate_embeddings([query])
            if q_emb:
                qv = q_emb[0]
                res = chunks_index.search(
                    query,
                    {
                        "vector": qv,
                        "hybrid": {"semanticRatio": 0.8, "embedder": "default"},
                        "limit": k * 2,
                        "attributesToRetrieve": ["*"]
                    }
                )
                search_method = "hybrid"
            else:
                res = chunks_index.search(query, {"limit": k * 2, "attributesToRetrieve": ["*"]})
        except Exception as e:
            logger.warning(f"Hybrid search failed, fallback to text. Error: {e}")
            res = chunks_index.search(query, {"limit": k * 2, "attributesToRetrieve": ["*"]})
    else:
        res = chunks_index.search(query, {"limit": k * 2, "attributesToRetrieve": ["*"]})

    hits = res.get("hits", [])
    if not hits:
        result = {
            "answer": "I couldn't find any relevant chunks to answer your question.",
            "chunks": [],
            "total_chunks_found": 0,
            "cached": False,
            "search_method": search_method
        }
        set_json(cache_key, {**result, "cached": False}, 600)
        return result

    selected = _select_chunks(hits, k)

    # Build LLM context + output chunk list
    context_parts, chunks, contexts = [], [], []
    for i, h in enumerate(selected):
        content = h.get("content") or h.get("text", "")
        title = h.get("title", h.get("metadata", {}).get("title", f"Chunk {i+1}"))
        doc_id = h.get("document_id", f"doc-{i}")
        idx = h.get("chunk_index", i)
        if not content:
            continue
        context_parts.append(f"Document: {title} (Chunk {idx})\nContent: {content}\n")
        contexts.append(content)  # full text, used by the RAGAS evaluation
        chunks.append({
            "id": h.get("id", f"chunk-{i}"),
            "document_id": doc_id,
            "chunk_index": idx,
            "content": content[:300] + "..." if len(content) > 300 else content,
            "metadata": {k: v for k, v in h.items() if k not in ["text", "content", "_vectors"]}
        })

    if not chunks:
        result = {
            "answer": "I found chunks but couldn't extract readable content from them.",
            "chunks": [],
            "total_chunks_found": len(hits),
            "cached": False,
            "search_method": search_method
        }
        set_json(cache_key, {**result, "cached": False}, 600)
        return result

    context = "\n".join(context_parts)
    answer = await generate_rag_answer(query, context, search_method)

    result = {
        "answer": answer,
        "chunks": chunks,
        "contexts": contexts,
        "total_chunks_found": len(hits),
        "cached": False,
        "search_method": search_method
    }
    set_json(cache_key, {**result, "cached": False}, 600)
    return result
