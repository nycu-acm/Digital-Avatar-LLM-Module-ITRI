# rag_llm_api.py Module Documentation

## Overview

The `rag_llm_api.py` module provides a Flask-based REST API service that exposes the RAG + LLM functionality as HTTP endpoints. It serves as the web service layer for the ITRI Museum question-answering system, providing streaming responses and session management.

## Core Components

### RAGLLMAPIService Class

The main Flask application class that orchestrates API endpoints, RAG pipeline integration, and session management.

#### Key Features

- **RESTful API**: Clean HTTP endpoints for all RAG operations
- **Streaming Responses**: Real-time text streaming with END_FLAG termination
- **Session Management**: Per-client conversation history tracking
- **Auto-initialization**: Optional RAG system setup on startup
- **Health Monitoring**: System status and diagnostics endpoints
- **CORS Support**: Cross-origin requests enabled for web applications
- **Model Warmup**: Preloading endpoints to reduce first-request latency

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Client   │────│   Flask API      │────│  RAG Pipeline   │
│   (Web/Mobile)  │    │   Service        │    │  (ChromaDB)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Session        │    │   Streaming      │    │   Ollama LLM    │
│  Management     │    │   Response       │    │   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation & Dependencies

### Required Python Packages

```bash
pip install flask flask-cors requests chromadb numpy scikit-learn jieba
```

### System Requirements

- **Ollama Service**: Running LLM inference server
- **Python 3.8+**: Modern Python with async support
- **Memory**: 4GB+ RAM for API service (additional for models)

## Quick Start

### Basic Server Launch

```bash
# Start with default settings
python rag_llm_api.py

# Start with auto-initialization
python rag_llm_api.py --auto-init

# Custom host and port
python rag_llm_api.py --host 0.0.0.0 --port 5002

# Debug mode
python rag_llm_api.py --debug
```

### Programmatic Usage

```python
from rag_llm_api import RAGLLMAPIService

# Create service instance
service = RAGLLMAPIService()

# Initialize RAG system
success = service._initialize_rag_system()

# Run server
service.run(host='0.0.0.0', port=5002)
```

## API Endpoints

### Health Check

**GET** `/health`

Check service status and RAG initialization state.

```bash
curl http://localhost:5002/health
```

**Response:**
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1671234567.89
}
```

### RAG Query (Streaming)

**POST** `/api/rag-llm/query`

Main endpoint for question-answering with streaming response.

**Request Body:**
```json
{
  "text_user_msg": "What is ITRI?",
  "session_id": "optional_session_id",
  "include_history": true
}
```

**Response:** Streaming text with `END_FLAG` termination

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "工研院是什麼？", "session_id": "test_session"}'
```

### RAG System Initialization

**POST** `/api/rag-llm/init`

Initialize or reinitialize the RAG system.

```bash
curl -X POST http://localhost:5002/api/rag-llm/init
```

**Response:**
```json
{
  "success": true,
  "rag_initialized": true,
  "message": "RAG system initialized successfully"
}
```

### Session History Management

**GET** `/api/rag-llm/sessions/<session_id>/history`

Retrieve chat history for a specific session.

```bash
curl http://localhost:5002/api/rag-llm/sessions/my_session/history
```

**Response:**
```json
{
  "session_id": "my_session",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "message_count": 2
}
```

**DELETE** `/api/rag-llm/sessions/<session_id>/history`

Clear chat history for a specific session.

```bash
curl -X DELETE http://localhost:5002/api/rag-llm/sessions/my_session/history
```

### Connection Close

**POST** `/api/rag-llm/close`

Graceful connection closure with session cleanup.

**Request Body:**
```json
{
  "session_id": "your_session_id"
}
```

```bash
curl -X POST http://localhost:5002/api/rag-llm/close \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session"}'
```

**Response:**
```json
{
  "success": true,
  "session_id": "test_session",
  "message": "Connection closed successfully",
  "session_existed": true,
  "messages_cleared": 8,
  "timestamp": 1671234567.89
}
```

### Model Warmup

**POST** `/api/rag-llm/warmup`

Preload embedding and LLM models to reduce first-request latency.

```bash
curl -X POST http://localhost:5002/api/rag-llm/warmup
```

**Response:**
```json
{
  "embedding_model": {
    "status": "success",
    "message": "Embedding model warmed up successfully", 
    "time_ms": 150.5,
    "test_query": "ITRI warmup test",
    "results_found": 3
  },
  "llm_model": {
    "status": "success", 
    "message": "LLM model warmed up successfully",
    "time_ms": 2341.2,
    "test_response": "OK"
  },
  "overall_success": true,
  "timestamp": 1671234567.89
}
```

## Session Management

### Session Storage

The API maintains in-memory session storage with automatic cleanup:

```python
# Session structure
self.chat_sessions = {
    "session_id": [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"},
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "Answer 2"}
    ]
}
```

### Session Lifecycle

1. **Creation**: Automatic on first query with session_id
2. **Update**: Conversation history appended after each exchange  
3. **Cleanup**: Manual via `/close` endpoint or server restart

## Streaming Response Format

### Response Protocol

- **Content Chunks**: Raw text content streamed character-by-character
- **Termination**: `END_FLAG` string indicates response completion
- **Error Handling**: `ERROR:` prefix for error messages

### Client Processing Example

```python
def process_streaming_response(response):
    accumulated = ""
    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            if "END_FLAG" in chunk:
                # Remove END_FLAG from final content
                final_text = chunk.replace("END_FLAG", "")
                if final_text:
                    accumulated += final_text
                break
            else:
                accumulated += chunk
                print(chunk, end="", flush=True)
    return accumulated
```

## Configuration

### Command Line Arguments

```bash
python rag_llm_api.py --help
```

**Available Options:**

- `--host`: Host to bind to (default: `0.0.0.0`)
- `--port`: Port to bind to (default: `5002`) 
- `--debug`: Enable Flask debug mode
- `--auto-init`: Auto-initialize RAG system on startup

### Environment Variables

The service uses these environment paths:

- **ChromaDB Paths**: Multiple fallback locations for vector database
- **Ollama Service**: `http://localhost:11435` for LLM and embeddings

### Custom Configuration

```python
# Custom initialization
service = RAGLLMAPIService()

# Modify RAG pipeline settings
service.rag_pipeline.chunk_size = 400
service.rag_pipeline.chunk_overlap = 100

# Custom ChromaDB path
custom_paths = ["/custom/path/to/chroma_db"]
# Implementation handles path discovery automatically
```

## Error Handling

### HTTP Status Codes

- **200**: Success with data
- **400**: Bad request (missing parameters)
- **500**: Internal server error

### Error Response Format

```json
{
  "error": "Description of error",
  "timestamp": 1671234567.89
}
```

### Common Error Scenarios

**RAG Not Initialized:**
```json
{
  "error": "RAG system not initialized. Call /api/rag-llm/init first"
}
```

**Missing Parameters:**
```json
{
  "error": "text_user_msg is required"
}
```

**Ollama Service Unavailable:**
```json
{
  "error": "Could not connect to LLM service (check if Ollama is running)"
}
```

## Advanced Features

### RAG System Auto-Discovery

The service automatically discovers existing ChromaDB collections:

```python
# Attempts multiple paths
potential_paths = [
   f"{CHROMA_DB_PATH}"
]

# Tries multiple collection names
collection_names = [
    "itri_museum_collection",
    "itri_museum_docs", 
    "museum_collection",
    "default_collection"
]
```

### Fallback Modes

**LLM-Only Mode**: When RAG initialization fails, the service continues with direct LLM responses without retrieval augmentation.

**Minimal Collection**: Creates sample data collection if no existing data found.

### Warmup Optimization

The warmup endpoint provides detailed performance metrics:

- **Embedding Model**: Tests similarity search capability
- **LLM Model**: Validates response generation  
- **Dimension Checking**: Detects embedding compatibility issues

## Performance Optimization

### Connection Pooling

```python
# Flask runs with threading enabled
app.run(threaded=True)
```

### Memory Management  

- **Session History**: Limited to recent messages per session
- **Batch Processing**: ChromaDB operations batched for efficiency
- **Lazy Loading**: Models loaded on first request

### Caching Strategies

- **System Prompt**: Cached and reused across requests
- **TF-IDF Index**: Built once and reused for sparse retrieval
- **Embedding Model**: Kept warm in Ollama service

## Monitoring & Logging

### Logging Configuration

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Console Output

The service provides colored console output for monitoring:

- **🔄 Blue**: Initialization and setup
- **✅ Green**: Success operations
- **⚠️ Yellow**: Warnings and fallbacks  
- **❌ Red**: Errors and failures

### Health Monitoring

Regular health checks should monitor:

```bash
# Basic health check
curl http://localhost:5002/health

# RAG initialization status  
curl -X POST http://localhost:5002/api/rag-llm/init

# Model performance
curl -X POST http://localhost:5002/api/rag-llm/warmup
```

## Security Considerations

### CORS Configuration

```python
from flask_cors import CORS
CORS(self.app)  # Enables cross-origin requests
```

### Input Validation

- **JSON Schema**: Request payloads validated
- **Parameter Sanitization**: User inputs cleaned
- **Session ID**: Simple string validation

### Rate Limiting

Consider implementing rate limiting for production:

```python
# Example with Flask-Limiter
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)
```

## Testing

### Unit Testing

```python
import unittest
from rag_llm_api import RAGLLMAPIService

class TestRAGAPI(unittest.TestCase):
    def setUp(self):
        self.service = RAGLLMAPIService()
        self.service.app.config['TESTING'] = True
        self.client = self.service.app.test_client()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
```

### Integration Testing

```bash
# Test complete workflow
curl -X POST http://localhost:5002/api/rag-llm/init
curl -X POST http://localhost:5002/api/rag-llm/warmup  
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "Test question"}'
```

## Deployment

### Production Setup

```bash
# Use production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 rag_llm_api:app
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5002

CMD ["python", "rag_llm_api.py", "--host", "0.0.0.0", "--port", "5002", "--auto-init"]
```

### Environment Setup

```bash
# Production environment variables
export FLASK_ENV=production
export OLLAMA_HOST=127.0.0.1:11435
export CUDA_VISIBLE_DEVICES=0,1
```

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check port availability
netstat -ln | grep 5002

# Check Python dependencies
pip list | grep flask
```

**RAG Initialization Fails:**  
```bash
# Check ChromaDB permissions
ls -la /path/to/chroma_db/
chmod 755 /path/to/chroma_db/
```

**Ollama Connection Issues:**
```bash
# Verify Ollama service
curl http://localhost:11435/api/tags

# Check model availability
ollama list
```

### Debug Mode

```bash
# Enable detailed logging
python rag_llm_api.py --debug --auto-init
```

### Performance Issues

- **Memory**: Monitor with `htop` or `free -h`
- **Response Time**: Use `/warmup` endpoint before queries
- **Network**: Check latency to Ollama service

## API Client Examples

### Python Client

```python
import requests

def query_rag_api(question, session_id="default"):
    url = "http://localhost:5002/api/rag-llm/query"
    payload = {
        "text_user_msg": question,
        "session_id": session_id
    }
    
    with requests.post(url, json=payload, stream=True) as response:
        result = ""
        for chunk in response.iter_content(decode_unicode=True):
            if "END_FLAG" in chunk:
                break
            result += chunk
        return result

# Usage
answer = query_rag_api("工研院是什麼？")
print(answer)
```

### JavaScript Client

```javascript
async function queryRAG(question, sessionId = 'default') {
    const response = await fetch('http://localhost:5002/api/rag-llm/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text_user_msg: question,
            session_id: sessionId
        })
    });
    
    const reader = response.body.getReader();
    let result = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        if (chunk.includes('END_FLAG')) break;
        result += chunk;
    }
    
    return result;
}
```

## License

This module is part of the ITRI Museum RAG system, developed for educational and research purposes.
