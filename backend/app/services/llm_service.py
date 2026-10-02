import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.models.chat import ChatMessage


async def generate_chat_completion(messages: List[ChatMessage], model: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
    """Call LiteLLM chat completions API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": model or settings.LITELLM_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": 2000
        }
        r = await client.post(f"{settings.PROXY_URL}/v1/chat/completions", json=payload, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return r.json()


async def generate_rag_answer(query: str, context: str, search_method: str) -> str:
    """Use LiteLLM with context from retrieved chunks."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": settings.LITELLM_MODEL,
                "messages": [
                    {"role": "system", "content": f"You are a helpful assistant. Answer based on document chunks. Retrieval used {search_method}."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            r = await client.post(f"{settings.PROXY_URL}/v1/chat/completions", json=payload, headers={"Content-Type": "application/json"})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            logger.error(f"LLM RAG failed: {r.text}")
            return "I found relevant chunks but could not generate an answer."
    except Exception as e:
        logger.error(f"RAG LLM error: {e}")
        return "I found chunks but could not generate an answer due to an error."
