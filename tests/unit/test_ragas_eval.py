"""RAGAS evaluation on 2 examples.

RAGAS collections metrics only accept RAGAS LLM/embedding objects (not LangChain models), so the offline
test uses a canned RAGAS LLM and wraps LangChain's DeterministicFakeEmbedding. The live test calls a real
OpenAI-compatible endpoint (LiteLLM proxy by default): `pytest -m live`.
"""
import asyncio
import math
import os

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from ragas.embeddings.base import BaseRagasEmbedding
from ragas.llms.base import InstructorBaseRagasLLM

import app.eval.ragas_eval as ragas_eval

TESTSET = [
    {"question": "Define autoencoders",
     "ground_truth": "Autoencoders are neural networks that learn efficient codings of their input."},
    {"question": "What is the primary goal of linear factor models?",
     "ground_truth": "Linear factor models explain observed variables with a few latent factors."},
]
CONTEXTS = {
    "Define autoencoders": "An autoencoder is a neural network trained to copy its input to its output "
                           "through a low-dimensional code, learning efficient codings.",
    "What is the primary goal of linear factor models?": "Linear factor models such as PCA describe observed "
                                                         "variables with a small number of latent factors.",
}

# Structured outputs returned by the fake LLM, keyed by the pydantic model RAGAS asks for
CANNED = {
    "StatementGeneratorOutput": {"statements": ["The answer is supported by the context."]},
    "NLIStatementOutput": {"statements": [{"statement": "The answer is supported by the context.",
                                           "reason": "Stated in the context.", "verdict": 1}]},
    "ContextRecallOutput": {"classifications": [{"statement": "Reference statement.",
                                                 "reason": "Found in the context.", "attributed": 1}]},
    "ContextPrecisionOutput": {"reason": "The context is useful.", "verdict": 1},
    "AnswerRelevanceOutput": {"question": "Define autoencoders", "noncommittal": 0},
}


class FakeRagasLLM(InstructorBaseRagasLLM):
    def __init__(self):
        self.calls = []

    def generate(self, prompt, response_model):
        self.calls.append(response_model.__name__)
        return response_model.model_validate(CANNED[response_model.__name__])

    async def agenerate(self, prompt, response_model):
        return self.generate(prompt, response_model)


class FakeRagasEmbedding(BaseRagasEmbedding):
    def __init__(self, size: int = 384):
        self._model = DeterministicFakeEmbedding(size=size)

    def embed_text(self, text, **kwargs):
        return self._model.embed_query(text)

    async def aembed_text(self, text, **kwargs):
        return self.embed_text(text)


@pytest.fixture
def fake_rag(monkeypatch):
    async def _rag_search(query, k, use_embeddings=True):
        return {"answer": f"Answer about: {query}", "chunks": [{"content": CONTEXTS[query]}]}

    monkeypatch.setattr(ragas_eval, "rag_search", _rag_search)


def test_ragas_evaluation_offline(fake_rag):
    llm = FakeRagasLLM()
    metrics = ragas_eval.build_metrics(llm=llm, embeddings=FakeRagasEmbedding())

    rows, scores = asyncio.run(ragas_eval.run_evaluation(TESTSET, metrics=metrics))

    assert len(rows) == 2
    assert set(scores) == {"faithfulness", "answer_relevancy", "context_recall", "context_precision"}
    for name, value in scores.items():
        assert not math.isnan(value), name
        assert 0.0 <= value <= 1.0, name
    assert rows[0]["retrieved_contexts"] == [CONTEXTS["Define autoencoders"]]
    assert {"NLIStatementOutput", "ContextRecallOutput", "ContextPrecisionOutput"} <= set(llm.calls)


def test_default_metrics_use_litellm_aliases():
    metrics = ragas_eval.build_metrics()
    assert metrics["faithfulness"].llm.model == ragas_eval.settings.LITELLM_MODEL
    assert metrics["answer_relevancy"].embeddings.model == ragas_eval.settings.EMBEDDING_MODEL_NAME


@pytest.mark.live
def test_ragas_evaluation_live():
    """Real LLM + embeddings. Configure with RAGAS_LIVE_BASE_URL / RAGAS_LIVE_API_KEY /
    RAGAS_LIVE_LLM_MODEL / RAGAS_LIVE_EMBEDDING_MODEL (defaults: LiteLLM proxy settings)."""
    from openai import AsyncOpenAI
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory

    settings = ragas_eval.settings
    api_key = os.getenv("RAGAS_LIVE_API_KEY", settings.PROXY_KEY)
    if not api_key:
        pytest.skip("RAGAS_LIVE_API_KEY (or PROXY_KEY) is not set")
    client = AsyncOpenAI(base_url=os.getenv("RAGAS_LIVE_BASE_URL", settings.LITELLM_URL), api_key=api_key)
    metrics = ragas_eval.build_metrics(
        llm=llm_factory(os.getenv("RAGAS_LIVE_LLM_MODEL", settings.LITELLM_MODEL), client=client),
        embeddings=embedding_factory("openai", model=os.getenv("RAGAS_LIVE_EMBEDDING_MODEL",
                                                              settings.EMBEDDING_MODEL_NAME), client=client),
    )
    samples = [{"user_input": t["question"], "response": t["ground_truth"],
                "retrieved_contexts": [CONTEXTS[t["question"]]], "reference": t["ground_truth"]}
               for t in TESTSET]

    rows = asyncio.run(ragas_eval.score_samples(samples, metrics))
    scores = ragas_eval.average_scores(rows, metrics)

    print(scores)
    for name, value in scores.items():
        assert not math.isnan(value), name
        assert 0.0 <= value <= 1.0, name
    assert scores["faithfulness"] > 0.5
