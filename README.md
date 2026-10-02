# RAGOPS - Production-Ready RAG Pipeline

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com)
[![Meilisearch](https://img.shields.io/badge/Meilisearch-Search-orange)](https://meilisearch.com)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Proxy-purple)](https://litellm.ai)

A production-ready Retrieval-Augmented Generation (RAG) pipeline built with modern technologies, designed for CPU deployment with enterprise-grade features.

## 🏗️ Architecture Overview

```txt
┌─────────────────────────────────────────────────────────────────────┐
│                           RAGOPS ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │────│   Nginx     │────│  FastAPI    │────│ Meilisearch │
│ Application │    │  (Optional) │    │  Backend    │    │   Search    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                              │                    │
                                              │              ┌──────────┐
                                              │              │ Document │
                                              │              │ & Chunks │
                                              │              │ Indexes  │
                                              │              └──────────┘
                                              │
                    ┌─────────────┐          │          ┌─────────────┐
                    │   Redis     │──────────┼──────────│  LiteLLM    │
                    │  Caching    │          │          │   Proxy     │
                    └─────────────┘          │          └─────────────┘
                                              │                    │
                                              │              ┌──────────┐
                                              │              │   Groq   │
                                              └──────────────│   LLM    │
                                                            │ Provider │
                    ┌─────────────┐                         └──────────┘
                    │     TEI     │                               │
                    │ Embeddings  │───────────────────────────────┘
                    │  Service    │          
                    └─────────────┘          

Flow:
1. Documents → Ingestion → Chunking → Embeddings → Meilisearch
2. Query → FastAPI → Meilisearch (Hybrid Search) → Context → LLM → Response
3. Redis caches embeddings and responses for performance
```

## 🚀 Key Features

### Core Capabilities
- **🔍 Hybrid Search**: Combines vector similarity and BM25 text search
- **📄 Document Processing**: Supports multiple document types with intelligent chunking
- **🧠 LLM Integration**: Groq LLMs via LiteLLM proxy with fallback support
- **⚡ High Performance**: Redis caching with 5-50x speed improvements
- **🎯 Semantic Retrieval**: TEI embeddings for semantic understanding
- **🔧 Production Ready**: Docker Compose orchestration with health checks

### Technical Features
- **CPU Optimized**: Runs efficiently on CPU-only infrastructure
- **Scalable Architecture**: Microservices design with independent scaling
- **Enterprise Security**: Authentication, authorization, and secure communication
- **Monitoring & Logging**: Comprehensive observability stack
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 📋 Prerequisites

- **Docker & Docker Compose**: Latest versions
- **4GB+ RAM**: Recommended for optimal performance
- **API Keys**: Groq API key for LLM access
- **Storage**: 2GB+ free disk space for models and indexes

## ⚡ Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd RAGOPS

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)
```

### 2. Start the Stack

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify health

```bash
# Check API health
curl http://localhost:18000/health
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Meilisearch Configuration
MEILI_KEY=your_secure_master_key_here
MEILI_INDEX=documents
EMBED_DIM=384

# LLM Provider Configuration  
PROXY_KEY=your_proxy_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Additional LLM providers
OPENAI_API_KEY=your_openai_key_here
HUGGINGFACE_API_KEY=your_hf_key_here

# Service URLs (Docker internal)
MEILI_URL=http://meilisearch:7700
PROXY_URL=http://litellm:4000
REDIS_URL=redis://redis:6379
```

### LiteLLM Model Configuration

Edit `litellm/config.yaml` to customize:

```yaml
# LiteLLM Configuration for RAG stack (CPU-only) using Redis cache + TEI embeddings + Groq LLM

model_list:
  # Primary chat/completions model on Groq
  - model_name: groq-gpt-oss
    litellm_params:
      model: groq/openai/gpt-oss-20b
      api_key: os.environ/GROQ_API_KEY
      reasoning_effort: low  # gpt-oss is a reasoning model: keep most of max_tokens for the answer

  # Fallback chat model on Groq (separate rate limits)
  - model_name: groq-gpt-oss-120b
    litellm_params:
      model: groq/openai/gpt-oss-120b
      api_key: os.environ/GROQ_API_KEY
      reasoning_effort: low

  # Local embeddings served by TEI (OpenAI-compatible embeddings API)
  - model_name: local-embeddings
    litellm_params:
      model: openai/BAAI/bge-small-en-v1.5  # informative only: TEI serves the model set by --model-id in docker-compose.yml
      api_key: os.environ/GROQ_API_KEY
      api_base: "http://tei-embeddings:80" 
      custom_llm_provider: openai
      timeout: 60

# Global LiteLLM settings
litellm_settings:
  cache: true
  cache_params:
    type: "redis"
    url: "redis://redis:6379"
    ttl: 1800
    supported_call_types: ["completion", "chat_completion", "embedding", "acompletion", "aembedding"]

# Prompt Injection basic guards
prompt_injection_params:
  heuristics_check: true
  similarity_check: false
  vector_db_check: false

# Routing / fallbacks
router_settings:
  fallbacks:
    - "groq-gpt-oss": ["groq-gpt-oss-120b"]
```

## 📊 Service Architecture

### Core Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **FastAPI Backend** | 18000 | Main API server | `GET /health` |
| **Meilisearch** | 7700 | Search & vector database | `GET /health` |
| **LiteLLM Proxy** | 4000 | LLM routing proxy | `GET /health` |
| **TEI Embeddings** | 80 | Text embeddings service | `GET /health` |
| **Redis** | 6379 | Caching layer | TCP check |

### Data Flow

1. **Document Ingestion**:
   ```
   Documents → FastAPI → Processing → Embeddings (TEI) → Meilisearch
   ```

2. **Query Processing**:
   ```
   Query → FastAPI → Embeddings (TEI) → Search (Meilisearch) → Context → LLM (Groq) → Response
   ```

3. **Caching Layer**:
   ```
   Redis caches: Embeddings (1h TTL) | LLM Responses (10min TTL)
   ```

## 🧪 Testing & Validation

### Offline test suite (pytest)

The `tests/unit` suite runs without any API key: embeddings come from LangChain's
`DeterministicFakeEmbedding`, the LLM is a `FakeListChatModel` behind a fake LiteLLM endpoint and Redis is
replaced by `fakeredis`. Only Meilisearch must be running, because hybrid search is computed by Meilisearch.

```bash
pip install -r backend/requirements-dev.txt
docker compose up -d meilisearch meili-init
make unit-test        # = pytest (tests marked `live` are skipped by default)
```

### Health Monitoring

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs [service-name]

# Monitor resource usage
docker stats

# Test individual components
curl http://localhost:7700/health    # Meilisearch
curl http://localhost:18000/health   # FastAPI Backend
```

## 🔧 Development & Customization

### Project Structure

```sh
.
├── Makefile
├── README.md
├── backend
│   ├── Dockerfile
│   ├── app
│   │   ├── __init__.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   ├── embeddings.py
│   │   │   ├── health.py
│   │   │   ├── ingest.py
│   │   │   ├── pdf.py
│   │   │   ├── search.py
│   │   │   └── stats.py
│   │   ├── core
│   │   │   ├── clients.py
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── health.py
│   │   │   ├── responses.py
│   │   │   └── search.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── ingestion.py
│   │   │   ├── llm_service.py
│   │   │   ├── pdf_processor.py
│   │   │   ├── rag_service.py
│   │   │   └── search_service.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── cache.py
│   │       └── hashing.py
│   ├── requirements.txt
│   └── seed_data.py
├── docker-compose.yml
├── litellm
│   └── config.yaml
├── pdf_files
│   ├── autoencoders.pdf
│   ├── linear_algebra.pdf
│   └── linear_factor_models.pdf
├── scripts
│   └── meili-init.sh
└── tests
    ├── chunking_validation.py
    ├── debug_vector_search.py
    ├── demo_phase2.py
    ├── demo_working_features.py
    ├── final_rag_test_report.py
    ├── test_all_features.py
    ├── test_direct_ingest.py
    └── test_phase2_comprehensive.py
```

## 📈 Production Deployment

### Scaling Considerations

1. **Horizontal Scaling**:
   ```yaml
   # In docker-compose.yml
   backend:
     deploy:
       replicas: 3
   
   redis:
     deploy:
       replicas: 1  # Redis should remain single instance
   ```

2. **Resource Allocation**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
   ```

3. **Data Persistence**:
   ```yaml
   volumes:
     meili_data:
       driver: local
       driver_opts:
         type: none
         o: bind
         device: /data/meilisearch
   ```
- - -
# Next Evolution: Advanced Document Processing and Search Enhancement

## 🎯 Overview

Phase 3 will extend RAGOPS with advanced document processing capabilities and search result reranking to create a comprehensive enterprise-grade RAG system.

### Current Status
- ✅ **Phase 1**: Text-based chunking and ingestion
- ✅ **Phase 2**: Embeddings integration with semantic search
- 🎯 **Phase 3**: PDF processing + reranking (this document)

---

## 🏗️ Architecture Enhancement

### New Components
```
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   PDF Upload    │───▶│   LangChain  │───▶│   Existing     │
│   Interface     │    │   Processor  │    │   Pipeline     │
└─────────────────┘    └──────────────┘    └────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  Cross-      │
                       │  Encoder     │
                       │  Reranker    │
                       └──────────────┘
```

### Enhanced Data Flow
1. **PDF Upload** → pypdf `PdfReader` → Page extraction
2. **Text Processing** → RecursiveCharacterTextSplitter → Smart chunking
3. **Metadata Enrichment** → Page numbers, file info, structure
4. **Existing Pipeline** → Embeddings → Meilisearch storage
5. **Enhanced Search** → Initial retrieval → Cross-encoder reranking → Final results

---

## 🎯 Quick Start

### 1. Start the System
```bash
make up
```
*This builds images, starts all services, and waits for readiness*

### 2. Validate Installation
```bash
make test
```
*Runs comprehensive Phase 2 validation suite*

### 3. Try a Demo
```bash
make demo
```
*Interactive demonstration of key features*

### 4. Check All Features
```bash
make validate
```
*Complete system validation and feature testing*

---

## 🛠️ Available Commands

Run `make help` to see all available commands:

```bash
make help
```

### Core Operations
- `make up` - Start all RAGOPS services
- `make down` - Stop all services  
- `make restart` - Restart all services
- `make logs` - Show backend service logs
- `make clean` - Clean up Docker resources

### Testing & Validation
- `make test` - Run Phase 2 comprehensive tests
- `make demo` - Run feature demonstrations  
- `make validate` - Validate all system features

### Development
- `make dev-logs` - Follow all service logs
- `make dev-rebuild` - Rebuild and restart backend only
- `make dev-reset` - Complete system reset with fresh data

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   Frontend      │───▶│   Backend    │───▶│  Meilisearch   │
│   (Future)      │    │   FastAPI    │    │   + Vector     │
└─────────────────┘    └──────────────┘    └────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐    ┌────────────────┐
                       │   LiteLLM    │    │     Redis      │
                       │   Proxy      │    │    Cache       │
                       └──────────────┘    └────────────────┘
                              │
                              ▼
                       ┌──────────────┐    ┌────────────────┐
                       │     TEI      │    │     Groq       │
                       │ Embeddings   │    │     LLM        │
                       └──────────────┘    └────────────────┘
```

### Services Overview
- **Backend** (Port 18000): FastAPI with Phase 2 embeddings
- **Meilisearch** (Port 7700): Vector-enabled search engine
- **TEI-Embeddings** (Port 8080): Text embeddings inference
- **LiteLLM** (Port 4000): Multi-provider LLM proxy
- **Redis** (Port 6379): Embedding cache layer
- **Meili-Init**: Automated index configuration

---

## 📡 API Reference

### Core Endpoints

#### Health Check
```bash
curl -s http://localhost:18000/health | jq .
```
**Response**:
```json
{
  "status": "healthy",
  "embeddings_available": true,
  "embedding_dimensions": 384
}
```

#### Document Ingestion
```bash
curl -X POST "http://localhost:18000/ingest" \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "doc1",
    "text": "Your document content here...",
    "metadata": {"title": "Document Title", "category": "docs"}
  }]' | jq .
```

#### Semantic Search & RAG
```bash
curl -X POST "http://localhost:18000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are vector embeddings?", "k": 5}' | jq .
```

#### Test Embeddings
```bash
curl -X POST "http://localhost:18000/test-embeddings" \
  -H "Content-Type: application/json" \
  -d '["text to embed", "another text"]' | jq .
```

#### Initialize Indexes
```bash
curl -X POST "http://localhost:18000/init-index"
```

---

## 🔧 Configuration

### Environment Setup
Create a `.env` file with your configuration:

```bash
# Required: Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Meilisearch Configuration  
MEILI_KEY=change_me_master_key

# Performance Settings (optional)
REDIS_CACHE_TTL=3600
MAX_CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Service Configuration
All service URLs are automatically configured for Docker Compose:
- `PROXY_URL=http://litellm:4000`
- `MEILISEARCH_URL=http://meilisearch:7700`
- `REDIS_URL=redis://redis:6379`
- `TEI_URL=http://tei-embeddings:8080`

---

## 🧪 Testing & Validation

### Using Makefile Commands

#### Quick Validation
```bash
make test
```
*Runs comprehensive Phase 2 test suite*

#### Full System Validation
```bash
make validate  
```
*Tests all features and generates detailed reports*


### Test Files Organization
All tests are in the `tests/` directory:
- `tests/test_phase2_comprehensive.py` - Complete Phase 2 validation
- `tests/test_all_features.py` - Comprehensive feature testing
- `tests/chunking_validation.py` - Text chunking validation

---

#### Check System Status
```bash
# After make up, check services
docker compose ps

# Check resource usage
docker stats
```

### Maintenance Tasks

#### Clean Docker Resources
```bash
make clean
```
*Removes containers, volumes, and prunes system*

#### Manual Cache Clear
```bash
docker compose exec redis redis-cli FLUSHALL
```

#### Backup Data
```bash
# Backup documents
curl -H "Authorization: Bearer $MEILI_KEY" \
  "http://localhost:7700/indexes/documents/documents" > backup_documents.json

# Backup chunks  
curl -H "Authorization: Bearer $MEILI_KEY" \
  "http://localhost:7700/indexes/chunks/documents" > backup_chunks.json
```
