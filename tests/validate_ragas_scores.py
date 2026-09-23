#!/usr/bin/env python3
import asyncio
import sys
import os
import sys; sys.path.insert(0, "/app")
import httpx
from app.core.logging import logger
from app.eval.ragas_eval import run_evaluation

TEST_DOCS = [
    {"id": "Neural Networks", "text": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes called neurons."},
    {"id": "Machine Learning", "text": "Machine learning is a subset of AI that enables systems to learn from data. It includes supervised and unsupervised learning."},
    {"id": "Python Programming", "text": "Python is a high-level programming language known for simplicity. It is widely used in data science and web development."}
]

TEST_CASES = [
    {"question": "What are neural networks?", "ground_truth": "Neural networks are computing systems inspired by biological neural networks."},
    {"question": "What is machine learning?", "ground_truth": "Machine learning is a subset of AI that enables systems to learn from data."}
]

async def ingest_docs():
    logger.info("Ingesting test documents...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post("http://backend:8000/ingest", json=TEST_DOCS)
            if r.status_code == 200:
                logger.info(f"Ingested {len(TEST_DOCS)} documents successfully")
            else:
                logger.error(f"Ingestion failed: {r.status_code} - {r.text}")
        except Exception as e:
            logger.error(f"Error: {e}")
    logger.info("Waiting 10 seconds for Meilisearch to index documents...")
    await asyncio.sleep(10)  # Wait for Meilisearch indexing

async def run_validation():
    logger.info("Running RAGAS validation...")
    rows, avg = await run_evaluation(TEST_CASES)
    print("\nRAGAS SCORES")
    for row in rows:
        print(row["user_input"], {k: round(row[k], 4) for k in avg})
    print("\nAVERAGE SCORES")
    for k, v in avg.items():
        print(f"{k}: {v:.4f}")
    checks = 0
    if all(0 <= v <= 1 for v in avg.values()):
        print("✓ All scores in valid range")
        checks += 1
    if avg["faithfulness"] > 0 or avg["answer_relevancy"] > 0:
        print("✓ Non-zero scores")
        checks += 1
    return checks == 2

async def main():
    await ingest_docs()
    success = await run_validation()
    if success:
        print("\n✓ RAGAS validation successful!")

if __name__ == "__main__":
    asyncio.run(main())
