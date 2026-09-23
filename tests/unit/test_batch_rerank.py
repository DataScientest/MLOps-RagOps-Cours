import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

from .test_rag_pipeline import DOCS

PDF_DIR = Path(__file__).resolve().parents[2] / "pdf_files"

pytestmark = pytest.mark.meili


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_proxy_embeddings(monkeypatch, fake_embeddings):
    """rerank_service calls LiteLLM /v1/embeddings directly: answer with the fake embedding model."""
    import app.services.rerank_service as rerank_service

    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        texts = payload["input"] if isinstance(payload["input"], list) else [payload["input"]]
        vectors = fake_embeddings.model.embed_documents(texts)
        return httpx.Response(200, json={"data": [{"embedding": v, "index": i} for i, v in enumerate(vectors)]})

    def async_client(*args, **kwargs):
        return httpx.AsyncClient(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(rerank_service, "httpx", SimpleNamespace(AsyncClient=async_client))
    return requests


def test_batch_pdf_ingestion(client, meili):
    files = [("files", (p.name, p.read_bytes(), "application/pdf"))
             for p in (PDF_DIR / "autoencoders.pdf", PDF_DIR / "linear_factor_models.pdf")]
    r = client.post("/ingest-pdf-batch", files=files)
    assert r.status_code == 200, r.text
    results = r.json()
    assert [res["filename"] for res in results] == ["autoencoders.pdf", "linear_factor_models.pdf"]
    for res in results:
        assert "error" not in res, res
        assert res["chunks_created"] > 0 and res["pages_processed"] >= 1
        assert res["embeddings_generated"] == res["chunks_created"]


def test_search_with_reranking(client, meili, fake_proxy_embeddings):
    assert client.post("/ingest", json=DOCS).status_code == 200
    meili.wait()

    r = client.post("/search-rerank", json={"query": "latent factors", "k": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["search_method"] == "hybrid+rerank"
    assert body["chunks"]
    assert body["rerank_scores"] == sorted(body["rerank_scores"], reverse=True)
    assert {p["model"] for p in fake_proxy_embeddings} == {settings.EMBEDDING_MODEL_NAME}
