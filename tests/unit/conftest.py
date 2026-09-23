"""Shared fixtures for the offline test suite.

- Redis is replaced by fakeredis.
- Embeddings come from langchain_core DeterministicFakeEmbedding (no TEI, no LiteLLM).
- The LLM is a langchain_core FakeListChatModel exposed behind a fake LiteLLM /v1/chat/completions.
- Meilisearch is real (hybrid search is computed by Meilisearch itself): start it with
  `docker compose up -d meilisearch meili-init`. Tests use throwaway indexes.
"""
import json
import os
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import dotenv_values

    _dotenv = dotenv_values(ROOT / ".env") if (ROOT / ".env").exists() else {}
except ImportError:  # pragma: no cover
    _dotenv = {}

# Host-side values (the .env file holds Docker-internal URLs)
os.environ["MEILI_URL"] = os.getenv("MEILI_TEST_URL", "http://localhost:7700")
os.environ.setdefault("MEILI_KEY", _dotenv.get("MEILI_KEY") or "password123")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")  # never reached: fakeredis
os.environ.setdefault("PROXY_URL", "http://litellm.test:4000")  # never reached: fake LLM / embeddings
os.environ.setdefault("LITELLM_MODEL", "groq-llama3")
os.environ.setdefault("EMBEDDING_MODEL_NAME", "local-embeddings")
os.environ.setdefault("EMBED_DIM", "384")

import fakeredis  # noqa: E402
import httpx  # noqa: E402
import meilisearch  # noqa: E402
from langchain_core.embeddings import DeterministicFakeEmbedding  # noqa: E402
from langchain_core.language_models.fake_chat_models import FakeListChatModel  # noqa: E402
from langchain_core.messages import convert_to_messages  # noqa: E402

from app.core.config import settings  # noqa: E402

FAKE_ANSWER = "Autoencoders learn compressed representations of their input."


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import app.core.clients as clients
    import app.utils.cache as cache

    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(clients, "redis_client", r)
    monkeypatch.setattr(cache, "redis_client", r)
    return r


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    """Replace the LiteLLM/TEI call with deterministic fake vectors of dimension EMBED_DIM."""
    import app.services.embeddings as embeddings

    model = DeterministicFakeEmbedding(size=settings.EMBED_DIM)
    calls = []

    async def _fake_request(texts):
        calls.append(list(texts))
        return [{"embedding": v} for v in model.embed_documents(texts)]

    monkeypatch.setattr(embeddings, "_request_embeddings", _fake_request)
    return SimpleNamespace(model=model, calls=calls)


@pytest.fixture
def fake_llm(monkeypatch):
    """Serve FakeListChatModel answers through a fake LiteLLM chat completions endpoint."""
    import app.services.llm_service as llm_service

    model = FakeListChatModel(responses=[FAKE_ANSWER])
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append({"url": str(request.url), "payload": payload})
        reply = model.invoke(convert_to_messages(payload["messages"]))
        return httpx.Response(200, json={
            "id": "fake", "object": "chat.completion", "model": payload["model"],
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": reply.content}}],
        })

    def async_client(*args, **kwargs):
        kwargs.pop("transport", None)
        return httpx.AsyncClient(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(llm_service, "httpx", SimpleNamespace(AsyncClient=async_client))
    return SimpleNamespace(model=model, requests=requests)


def wait_for_index(client: meilisearch.Client, uid: str, timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pending = client.get_tasks({"indexUids": [uid], "statuses": ["enqueued", "processing"]})
        if not pending.results:
            failed = client.get_tasks({"indexUids": [uid], "statuses": ["failed"]})
            assert not failed.results, failed.results[0].error
            return
        time.sleep(0.2)
    raise TimeoutError(f"Meilisearch tasks on {uid} still pending")


@pytest.fixture
def meili(monkeypatch):
    """Throwaway `documents`/`chunks` indexes configured like scripts/meili-init.sh."""
    client = meilisearch.Client(settings.MEILI_URL, settings.MEILI_KEY)
    try:
        client.health()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Meilisearch unreachable at {settings.MEILI_URL}: {exc}")

    suffix = uuid.uuid4().hex[:8]
    uids = {"MEILI_INDEX": f"test_documents_{suffix}", "CHUNKS_INDEX": f"test_chunks_{suffix}"}
    index_settings = {
        "embedders": {"default": {"source": "userProvided", "dimensions": settings.EMBED_DIM}},
        "searchableAttributes": ["content", "title"],
        "displayedAttributes": ["id", "content", "title", "metadata", "source", "tags"],
        "filterableAttributes": ["source", "tags", "metadata.sha", "metadata.lang"],
        "sortableAttributes": ["created_at", "updated_at"],
    }
    for attr, uid in uids.items():
        client.create_index(uid, {"primaryKey": "id"})
        client.index(uid).update_settings(index_settings)
        wait_for_index(client, uid)
        monkeypatch.setattr(settings, attr, uid)

    # Only the chunks index is awaited: whole documents are added without `_vectors` while the
    # `documents` index declares a userProvided embedder, so Meilisearch rejects that task.
    yield SimpleNamespace(client=client, wait=lambda: wait_for_index(client, uids["CHUNKS_INDEX"]), **uids)

    for uid in uids.values():
        client.delete_index(uid)
