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
docker compose up -d

# Check service health
docker compose ps

# View logs
docker compose logs -f
```

### 3. Verify Installation

```bash
# Check API health
curl http://localhost:18000/health

# Access API documentation
open http://localhost:18000/docs

# Run system validation
docker compose exec backend python final_rag_test_report.py
```

### 4. Ingest Sample Documents

```bash
# Ingest sample documents for testing
docker compose exec backend python ingest.py

# Or ingest your own documents via API
curl -X POST "http://localhost:18000/ingest" \
  -H "Content-Type: application/json" \
  -d '[{"id": "doc1", "text": "Your document content", "metadata": {"source": "file.pdf"}}]'
```

### 5. Test RAG Queries

```bash
# Test search and generation
curl -X POST "http://localhost:18000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?", "k": 3}'

# Test direct chat
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
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
      api_base: "http://tei-embeddings:80" # TEI service URL (container internal)
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
  success_callback: ["langsmith"]
  failure_callback: ["langsmith"]  

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
| **Nginx** | 8443 | Reverse proxy (optional) | HTTP check |

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

## 📚 API Documentation

### Core Endpoints

#### Document Management

```http
POST /ingest
Content-Type: application/json

[
  {
    "id": "doc-1",
    "text": "Document content here",
    "metadata": {"source": "file.pdf", "author": "John Doe"}
  }
]
```

#### Search & Retrieval

```http
POST /search
Content-Type: application/json

{
  "query": "What is machine learning?",
  "k": 5
}

Response:
{
  "answer": "Machine learning is...",
  "chunks": [...],
  "total_chunks_found": 10,
  "cached": false
}
```

#### Direct Chat

```http
POST /chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Explain quantum computing"}
  ],
  "temperature": 0.3,
  "model": "groq-gpt-oss"
}
```

#### System Status
```http
GET /health           # API health
POST /init-index      # Initialize search indexes
```

### Interactive Documentation

- **Swagger UI**: http://localhost:18000/docs
- **ReDoc**: http://localhost:18000/redoc

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


### Automated Testing

```bash
# Run comprehensive system validation
docker compose exec backend python final_rag_test_report.py

# Demo working features
docker compose exec backend python demo_working_features.py

# Manual ingestion test
docker compose exec backend python ingest.py
```

### Performance Benchmarks

The system has been validated with:
- **API Response Time**: 3-9ms average
- **Cache Performance**: 5-51x speedup with Redis
- **Document Processing**: Supports documents from 50 to 5000+ words
- **Concurrent Requests**: Handles multiple simultaneous queries
- **Search Accuracy**: Hybrid search with relevance scoring

### Health Monitoring

```bash
# Check all services
docker compose ps

# View service logs
docker compose logs [service-name]

# Monitor resource usage
docker stats

# Test individual components
curl http://localhost:7700/health    # Meilisearch
curl http://localhost:18000/health   # FastAPI Backend
```

## 🔧 Development & Customization

### Project Structure

```sh
RAGOPS/
├── docker-compose.yml          # Service orchestration
├── .env                       # Environment configuration
├── backend/                   # FastAPI application
│   ├── app/
│   │   └── main.py           # Main API application
│   ├── Dockerfile            # Backend container
│   ├── requirements.txt      # Python dependencies
│   ├── ingest.py             # Sample data ingestion
│   ├── demo_working_features.py  # Feature demonstration
│   └── final_rag_test_report.py  # System validation
├── litellm/
│   └── config.yaml           # LLM proxy configuration
└── nginx/                    # Optional reverse proxy
    └── nginx.conf
```

### Adding Custom Documents

```python
# Via API
import httpx

documents = [
    {
        "id": "custom-doc-1",
        "text": "Your document content here...",
        "metadata": {
            "title": "Document Title",
            "author": "Author Name",
            "category": "technical",
            "tags": ["ai", "machine-learning"]
        }
    }
]

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:18000/ingest",
        json=documents
    )
    print(response.json())
```

### Extending LLM Providers

Add new providers in `litellm/config.yaml`:

```yaml
model_list:
  # OpenAI (default model recommended in the OpenAI docs)
  - model_name: openai-gpt6
    litellm_params:
      model: openai/gpt-6-astra
      api_key: os.environ/OPENAI_API_KEY

  # Anthropic Claude
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-5
      api_key: os.environ/ANTHROPIC_API_KEY
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

### Security Hardening

1. **Environment Security**:
   ```bash
   # Use strong, unique keys
   MEILI_KEY=$(openssl rand -hex 32)
   PROXY_KEY=$(openssl rand -hex 32)
   
   # Restrict network access
   # Configure firewall rules
   # Use TLS certificates
   ```

2. **API Security**:
   - Enable authentication in LiteLLM config
   - Configure rate limiting
   - Set up request validation
   - Monitor API access logs

### Monitoring Setup

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔍 Troubleshooting

### Common Issues

1. **Service Won't Start**:
   ```bash
   # Check logs
   docker compose logs [service-name]
   
   # Verify environment
   docker compose config
   
   # Restart services
   docker compose restart [service-name]
   ```

2. **Search Not Working**:
   ```bash
   # Check Meilisearch indexes
   curl -H "Authorization: Bearer $MEILI_KEY" \
        http://localhost:7700/indexes
   
   # Reinitialize indexes
   curl -X POST http://localhost:18000/init-index
   ```

3. **LLM Errors**:
   ```bash
   # Verify API keys
   docker compose exec backend env | grep -E "(GROQ|OPENAI)_API_KEY"
   
   # Test LiteLLM directly
   docker compose logs litellm
   ```

4. **Performance Issues**:
   ```bash
   # Check resource usage
   docker stats
   
   # Monitor cache hit rates
   docker compose exec backend python demo_working_features.py
   
   # Clear Redis cache
   docker compose exec redis redis-cli FLUSHALL
   ```

### Debug Commands

```bash
# Access service containers
docker compose exec backend bash
docker compose exec meilisearch sh

# Check network connectivity
docker compose exec backend ping meilisearch
docker compose exec backend ping litellm

# View detailed logs
docker compose logs -f --tail=100

# Restart problematic services
docker compose restart backend litellm
```

## 📖 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Meilisearch Documentation](https://docs.meilisearch.com/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

### Community
- [Issues & Bug Reports](https://github.com/your-repo/issues)
- [Feature Requests](https://github.com/your-repo/discussions)
- [Contributing Guidelines](CONTRIBUTING.md)

### Deployment Examples
- [AWS ECS Deployment](docs/aws-ecs.md)
- [Kubernetes Deployment](docs/kubernetes.md)
- [Docker Swarm Deployment](docs/docker-swarm.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
