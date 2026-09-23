import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.embeddings import _request_embeddings as REAL_REQUEST_EMBEDDINGS

from .conftest import FAKE_ANSWER

DOCS = [
    {"id": "doc-autoencoders", "text": "Autoencoders are neural networks trained to reconstruct their input "
     "through a low-dimensional code.", "metadata": {"title": "Autoencoders"}},
    {"id": "doc-linear-algebra", "text": "A matrix is a rectangular array of numbers. Eigenvectors keep their "
     "direction under a linear transformation.", "metadata": {"title": "Linear algebra"}},
    {"id": "doc-factor-models", "text": "Linear factor models such as PCA explain observed variables with a few "
     "latent factors.", "metadata": {"title": "Linear factor models"}},
]

pytestmark = pytest.mark.meili


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def ingested(client, meili):
    r = client.post("/ingest", json=DOCS)
    assert r.status_code == 200, r.text
    meili.wait()
    return r.json()


def test_health_reports_embedding_dimension(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["embeddings_available"] is True
    assert r.json()["embedding_dimensions"] == settings.EMBED_DIM


def test_ingestion_pipeline_on_three_documents(ingested, meili, fake_embeddings):
    assert ingested["indexed"] == 3
    assert ingested["chunks_created"] == 3
    assert ingested["embeddings_generated"] == 3
    stats = meili.client.index(meili.CHUNKS_INDEX).get_stats()
    assert stats.number_of_documents == 3
    assert fake_embeddings.calls == [[d["text"] for d in DOCS]]


def test_hybrid_search_returns_a_result(client, ingested):
    r = client.post("/search-chunks", json={"query": "autoencoders reconstruct input", "k": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["search_method"] == "hybrid"
    # Fake vectors carry no semantics: only check that the hybrid query returns chunks
    assert body["hits"]
    assert {h["id"] for h in body["hits"]} <= {f"{d['id']}-chunk-0" for d in DOCS}


def test_rag_endpoint_with_fake_llm(client, ingested, fake_llm):
    r = client.post("/search", json={"query": "What are autoencoders?", "k": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] == FAKE_ANSWER
    assert body["search_method"] == "hybrid"
    assert body["chunks"]

    [call] = fake_llm.requests
    assert call["url"].endswith("/v1/chat/completions")
    assert call["payload"]["model"] == settings.LITELLM_MODEL
    assert "Context:" in call["payload"]["messages"][-1]["content"]
    # full chunk texts are returned for the RAGAS evaluation
    assert body["chunks"] and all(c in {d["text"] for d in DOCS} for c in call_contexts(client))


def call_contexts(client):
    from app.services.rag_service import rag_search
    import asyncio
    return asyncio.run(rag_search("What are autoencoders?", 2))["contexts"]


def test_direct_search_on_documents_index(client, ingested):
    r = client.post("/search-direct", json={"query": "matrix eigenvectors", "k": 3})
    assert r.status_code == 200, r.text
    assert r.json()["total"] >= 1
    assert r.json()["hits"][0]["id"] == "doc-linear-algebra"


def test_stats(client, ingested):
    r = client.get("/stats")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["documents"]["count"] == 3
    assert body["chunks"]["count"] == 3
    assert body["chunks"]["embeddings"] == 3


def test_pdf_ingestion_embeds_every_chunk_and_ids_are_stable(client, meili):
    from pathlib import Path
    pdf = Path(__file__).resolve().parents[2] / "pdf_files" / "linear_factor_models.pdf"
    first = client.post("/ingest-pdf", files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")})
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["chunks_created"] > 32  # more than one TEI batch
    assert body["embeddings_generated"] == body["chunks_created"]
    meili.wait()
    second = client.post("/ingest-pdf", files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")})
    meili.wait()
    # same file name -> same chunk ids -> no duplicates
    stats = meili.client.index(meili.CHUNKS_INDEX).get_stats()
    assert stats.number_of_documents == body["chunks_created"] == second.json()["chunks_created"]


def test_embeddings_are_requested_in_batches_of_32(monkeypatch):
    """TEI rejects more than 32 inputs per request: _request_embeddings must split the calls."""
    import asyncio
    import json
    from types import SimpleNamespace

    import httpx

    import app.services.embeddings as embeddings

    sizes = []

    def handler(request):
        payload = json.loads(request.content)
        sizes.append(len(payload["input"]))
        assert payload["model"] == settings.EMBEDDING_MODEL_NAME
        return httpx.Response(200, json={"data": [{"embedding": [0.0] * settings.EMBED_DIM} for _ in payload["input"]]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(embeddings, "httpx", SimpleNamespace(
        AsyncClient=lambda *a, **kw: real_client(*a, transport=httpx.MockTransport(handler), **kw)))
    # the autouse fixture replaces _request_embeddings: call the real implementation saved at import time
    data = asyncio.run(REAL_REQUEST_EMBEDDINGS([f"text {i}" for i in range(70)]))

    assert sizes == [32, 32, 6]
    assert len(data) == 70


def test_llm_failure_is_not_cached(client, ingested, monkeypatch):
    import app.services.rag_service as rag_service

    async def failing(query, context, search_method):
        return "I found relevant chunks but could not generate an answer."

    monkeypatch.setattr(rag_service, "generate_rag_answer", failing)
    first = client.post("/search", json={"query": "What are autoencoders?", "k": 2}).json()
    second = client.post("/search", json={"query": "What are autoencoders?", "k": 2}).json()
    assert first["cached"] is False and second["cached"] is False
