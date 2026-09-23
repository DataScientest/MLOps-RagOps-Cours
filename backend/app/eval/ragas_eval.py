import asyncio
import math
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextRecall,
    ContextPrecisionWithReference,
)

# Import app modules
from app.core.config import settings
from app.core.logging import logger

from app.services.rag_service import rag_search

# --- 1. Configure LLM and Embeddings for RAGAS ---

# Inputs expected by each metric (fields of a RAGAS sample)
METRIC_INPUTS = {
    "faithfulness": ("user_input", "response", "retrieved_contexts"),      # Is the answer grounded in the context?
    "answer_relevancy": ("user_input", "response"),                       # Is the answer relevant to the question?
    "context_recall": ("user_input", "retrieved_contexts", "reference"),  # Does the context cover the ground truth?
    "context_precision": ("user_input", "reference", "retrieved_contexts"),  # Is the retrieved context relevant?
}


def build_metrics(llm=None, embeddings=None) -> Dict[str, Any]:
    """Create the RAGAS metrics, by default on the LiteLLM proxy (Groq LLM + TEI embeddings)."""
    if llm is None or embeddings is None:
        # OpenAI-compatible client pointing to the LiteLLM proxy
        client = AsyncOpenAI(base_url=settings.LITELLM_URL, api_key=settings.PROXY_KEY or "dummy")
        llm = llm or llm_factory(settings.LITELLM_MODEL, client=client)
        embeddings = embeddings or embedding_factory(
            "openai", model=settings.EMBEDDING_MODEL_NAME, client=client
        )
    return {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_recall": ContextRecall(llm=llm),
        "context_precision": ContextPrecisionWithReference(llm=llm),
    }


# --- 2. Evaluation Logic ---

async def score_samples(samples: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Score each sample with each metric. A failing metric gives NaN instead of stopping the run."""

    async def score(metric, sample, inputs):
        try:
            result = await metric.ascore(**{k: sample[k] for k in inputs})
            return result.value
        except Exception as e:
            logger.error(f"{type(metric).__name__} failed for '{sample['user_input']}': {e}")
            return math.nan

    rows = []
    for sample in samples:
        values = await asyncio.gather(
            *(score(metric, sample, METRIC_INPUTS[name]) for name, metric in metrics.items())
        )
        rows.append({**sample, **dict(zip(metrics, values))})
    return rows


def average_scores(rows: List[Dict[str, Any]], metric_names) -> Dict[str, float]:
    averages = {}
    for name in metric_names:
        values = [r[name] for r in rows if not math.isnan(r[name])]
        averages[name] = sum(values) / len(values) if values else math.nan
    return averages


async def run_evaluation(testset: List[Dict[str, Any]], metrics: Optional[Dict[str, Any]] = None):
    """
    Runs the Ragas evaluation on a provided testset.

    Args:
        testset: A list of dicts, each containing 'question' and 'ground_truth'.
    """
    logger.info("Starting Ragas evaluation...")
    metrics = metrics or build_metrics()

    # Step 1: Execute RAG for all questions
    samples = []
    for item in testset:
        question = item['question']
        logger.info(f"Processing question: {question}")
        try:
            # Call your main RAG function
            rag_output = await rag_search(
                query=question,
                k=3, # Max 3 chunks is a good default for Ragas
                use_embeddings=True
            )

            # Build a RAGAS sample
            samples.append({
                'user_input': question,
                'response': rag_output['answer'],
                'retrieved_contexts': [c['content'] for c in rag_output['chunks']], # List of retrieved text chunks
                'reference': item['ground_truth'] # The expected correct answer
            })

        except Exception as e:
            logger.error(f"RAG execution failed for question '{question}': {e}")
            samples.append({
                'user_input': question,
                'response': "Error during RAG execution.",
                'retrieved_contexts': [],
                'reference': item['ground_truth']
            })
            continue

    # Step 2: Run Ragas Metrics
    rows = await score_samples(samples, metrics)
    scores = average_scores(rows, metrics)

    logger.info("Ragas Evaluation Complete.")
    print(scores)
    return rows, scores

# --- 3. Example Execution (for testing/manual profile) ---

if __name__ == "__main__":
    # A small synthetic testset (you would load a real one in production)
    example_testset = [
        {
            "question": "Define autoencoders",
            "ground_truth": "Autoencoders are a type of neural network used for learning efficient data codings in an unsupervised manner."
        },
        {
            "question": "What is the primary goal of linear factor models?",
            "ground_truth": "The primary goal of linear factor models, such as PCA, is to model the covariance structure among variables by a few latent factors."
        }
        # Add more questions relevant to autoencoders.pdf, linear_algebra.pdf, etc.
    ]

    # Run the async function
    asyncio.run(run_evaluation(example_testset))
