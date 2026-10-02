# 🚀 RAGOPS Usage Guide

**Retrieval-Augmented Generation Operations System**  
*Complete semantic search and RAG solution with embeddings integration*

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

#### Interactive Demo
```bash
make demo
```
*Demonstrates semantic search and RAG capabilities*

### Manual Testing Examples

After running `make up`, try these manual tests:

#### 1. Health Verification
```bash
curl -s http://localhost:18000/health | jq .
```

#### 2. Sample Document Ingestion  
```bash
curl -X POST "http://localhost:18000/ingest" \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "ml-guide",
    "text": "Machine learning models use vector embeddings to represent text data. These numerical representations capture semantic relationships between words and enable similarity calculations for search and recommendation systems.",
    "metadata": {"title": "ML Embeddings Guide", "category": "ai"}
  }]' | jq .
```

#### 3. Semantic Search Test
```bash
curl -X POST "http://localhost:18000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do ML models represent text?", "k": 3}' | jq .
```

### Test Files Organization
All tests are in the `tests/` directory:
- `tests/test_phase2_comprehensive.py` - Complete Phase 2 validation
- `tests/test_all_features.py` - Comprehensive feature testing
- `tests/demo_phase2.py` - Interactive demonstrations
- `tests/chunking_validation.py` - Text chunking validation

---

## 📊 Performance & Monitoring  

### Performance Metrics
- **Health Check**: ~10ms
- **Embedding Generation**: ~500ms per batch
- **Document Ingestion**: 2-3s per document
- **Search Queries**: 300-800ms  
- **RAG Responses**: 3-5s (with LLM)

### Monitoring with Makefile

#### View Logs
```bash
make logs
```
*Shows backend service logs*

#### Development Logging
```bash
make dev-logs
```
*Follows logs from all services*

#### Check System Status
```bash
# After make up, check services
docker compose ps

# Check resource usage
docker stats
```

---

## 🛠️ Operations Guide

### Daily Operations

#### Start System
```bash
make up
```

#### Stop System
```bash
make down
```

#### Restart All Services
```bash
make restart
```

#### View Service Logs
```bash
make logs
```

### Development Operations

#### Rebuild Backend Only
```bash
make dev-rebuild
```
*Useful when making backend code changes*

#### Complete System Reset
```bash
make dev-reset  
```
*Stops everything, cleans volumes, restarts fresh*

#### Follow All Logs
```bash
make dev-logs
```
*Monitor all service logs in real-time*

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

---

## 🔍 Troubleshooting

### Using Makefile for Troubleshooting

#### Check System Health
```bash
make up
make test
```
*If test fails, indicates system issues*

#### Reset Everything
```bash
make dev-reset
```
*Nuclear option: completely fresh start*

#### Rebuild After Changes
```bash
make dev-rebuild
```
*When backend code changes*

#### Monitor Issues
```bash
make dev-logs
```
*Watch all services for error messages*

### Common Issues & Solutions

#### Issue: Services Won't Start
```bash
# Check for port conflicts
netstat -tlnp | grep -E "(18000|7700|4000|6379|8080)"

# Clean and restart
make clean
make up
```

#### Issue: Tests Failing
```bash
# Reset system and retest
make dev-reset
sleep 15
make test
```

#### Issue: Poor Performance
```bash
# Monitor resource usage during operations
make dev-logs &
make demo
```

#### Issue: API Key Problems
```bash
# Verify .env configuration
echo "GROQ_API_KEY=${GROQ_API_KEY:0:10}..."

# Restart with new configuration
make down
make up
```

---

## 🚀 Advanced Usage

### Custom Workflows

#### Batch Document Processing
```bash
# Start system
make up

# Run custom ingestion script
python3 your_custom_ingest.py

# Validate ingestion worked
make test
```

#### Development Workflow  
```bash
# Start development
make up
make test

# Make code changes to backend/app/main.py
make dev-rebuild

# Validate changes
make validate

# Monitor for issues
make dev-logs
```

#### Production Deployment
```bash
# Clean deployment
make clean
make up

# Validate production readiness
make validate

# Monitor ongoing operations
make logs
```

### Performance Optimization

#### Memory Optimization
```bash
# Add to .env file
REDIS_MAXMEMORY=512mb
MEILI_MAX_INDEXING_MEMORY=2048MB

# Restart with new settings
make restart
```

#### Cache Optimization
```bash
# Increase cache TTL
REDIS_CACHE_TTL=7200

# Restart services
make restart
```

---

## 🎯 Use Cases & Examples

### Use Case 1: Technical Documentation
```bash
# Start system
make up

# Ingest documentation
curl -X POST "http://localhost:18000/ingest" -d '[{
  "id": "api_guide", 
  "text": "API endpoints for document ingestion and search...",
  "metadata": {"type": "api_docs", "version": "v1"}
}]'

# Search documentation
curl -X POST "http://localhost:18000/search" -d '{
  "query": "How to authenticate API requests?", "k": 3
}'
```

### Use Case 2: Knowledge Base RAG
```bash
# Validate RAG functionality
make demo

# Custom RAG query
curl -X POST "http://localhost:18000/search" -d '{
  "query": "Best practices for embeddings in production?", "k": 5
}' | jq '.answer'
```

### Use Case 3: Content Discovery
```bash
# Test semantic similarity
curl -X POST "http://localhost:18000/search" -d '{
  "query": "neural networks machine learning", "k": 10
}' | jq '.chunks[].metadata'
```

---

## ✅ Status & Validation

### Current Status: 🚀 **PRODUCTION READY**

Validate current status with:
```bash
make test
```

**Expected Output**: 100% test suite passing (5/5 tests)

### System Validation Checklist
```bash
# 1. Start system
make up

# 2. Run comprehensive tests  
make test

# 3. Run feature demonstrations
make demo

# 4. Run full validation suite
make validate

# 5. Check logs for any issues
make logs
```

### Performance Validation
```bash
# Monitor system during demo
make dev-logs &
make demo

# Check resource usage
docker stats
```

---

## 📚 Technical Reference

### Model Configuration
- **Embedding Model**: BAAI/bge-small-en-v1.5
- **Dimensions**: 384
- **Languages**: 100+ supported
- **Performance**: ~1000 embeddings/second

### Makefile Targets Reference
```bash
make help          # Show all available commands
make build         # Build Docker images  
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # Show backend logs
make clean         # Clean Docker resources
make test          # Run Phase 2 tests
make demo          # Run demonstrations
make validate      # Complete validation
make dev-logs      # Follow all logs
make dev-rebuild   # Rebuild backend only
make dev-reset     # Complete reset
```

### Directory Structure
```
RAGOPS/
├── backend/           # FastAPI application
├── tests/            # All test and demo scripts
├── docker-compose.yml # Service orchestration
├── Makefile          # Operation commands
├── USAGE_GUIDE.md   # This guide
└── .env             # Configuration
```

---

## 🎉 Getting Started Checklist

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY
   ```

2. **Start System**
   ```bash
   make up
   ```

3. **Validate Installation**
   ```bash
   make test
   ```

4. **Try Demo**
   ```bash
   make demo
   ```

5. **Explore API**
   ```bash
   curl -s http://localhost:18000/health | jq .
   ```

**🚀 You're ready to use RAGOPS for production semantic search and RAG operations!**

---

*Use `make help` anytime to see available commands. All operations are designed to work through the Makefile for consistency and ease of use.*
