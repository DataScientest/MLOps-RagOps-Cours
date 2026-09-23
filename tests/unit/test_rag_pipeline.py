import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

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
