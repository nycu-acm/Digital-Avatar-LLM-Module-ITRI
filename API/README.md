# 🤖 RAG + LLM API Service

A standalone API service that exposes the RAG + LLM functionality from the integrated pipeline. This service allows team members to access the knowledge extraction and language model capabilities via HTTP API endpoints.

## ✨ Features

- **Streaming Responses**: Real-time text streaming as the LLM generates responses
- **RAG Integration**: Context-aware answers using document retrieval
- **Session Management**: Maintain chat history per session
- **Elegant Connection Close**: Graceful client disconnection with automatic session cleanup
- **END_FLAG Support**: Clear indication when response generation is complete
- **Multi-language Support**: English, Traditional Chinese (zh-tw) support
- **Health Monitoring**: Built-in health check and status endpoints
- **Model Warmup**: Preload models to reduce first-request latency

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /workspace/API
pip install -r requirements.txt
```

### 2. Start the API Service

```bash
# Basic startup
python rag_llm_api.py

# With auto-initialization
python rag_llm_api.py --auto-init

# Custom host/port
python rag_llm_api.py --host 0.0.0.0 --port 5002 --auto-init
```

### 3. Test the Service

```bash
# Check health
curl http://localhost:5002/health

# Warmup models (recommended after startup)
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Run example client
python client_example.py
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1234567890.123
}
```

### RAG + LLM Query (Streaming)
```http
POST /api/rag-llm/query
Content-Type: application/json

{
  "text_user_msg": "What is ITRI?",
  "session_id": "optional_session_id",
  "include_history": true
}
```

**Response:**
- **Content-Type**: `text/plain`
- **Streaming**: Text chunks followed by `END_FLAG`

**Example:**
```
ITRI (Industrial Technology Research Institute) is Taiwan's largest... END_FLAG
```

### Initialize RAG System
```http
POST /api/rag-llm/init
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
```http
# Get session history
GET /api/rag-llm/sessions/{session_id}/history

# Clear session history
DELETE /api/rag-llm/sessions/{session_id}/history
```

### Model Warmup
```http
POST /api/rag-llm/warmup
```

**Response:**
```json
{
  "embedding_model": {
    "status": "success",
    "message": "Embedding model warmed up successfully", 
    "time_ms": 150.23,
    "test_query": "ITRI warmup test",
    "results_found": 1
  },
  "llm_model": {
    "status": "success",
    "message": "LLM model warmed up successfully",
    "time_ms": 2341.67,
    "test_response": "OK"
  },
  "overall_success": true,
  "timestamp": 1234567890.123
}
```

**Purpose**: Preloads both embedding model and LLM to reduce first-request latency. Recommended to call this after starting the service.

### Elegant Connection Close
```http
POST /api/rag-llm/close
Content-Type: application/json
{ "session_id": "your_session_id" }
```

**Response:**
```json
{
  "success": true,
  "session_id": "your_session_id",
  "message": "Connection closed successfully",
  "session_existed": true,
  "messages_cleared": 15,
  "timestamp": 1234567890.123
}
```

**Purpose**: Client calls this function before program termination. Server will clear the history of the client based on the chat_session_id.

## 💬 Sample Questions

Here are some example questions you can ask the RAG + LLM API service about ITRI (Industrial Technology Research Institute):

### Traditional Chinese Questions (繁體中文)
```
工研院有什麼研究領域？
工研院的主要任務是什麼？
工研院成立於什麼時候？
工研院有哪些重要的技術發展？
工研院的組織架構如何？
工研院院長是誰？
工研院有哪些重要成就？
工研院如何推動產業升級？
工研院的人才培育計畫有哪些？
工研院與產業界如何合作？
```

### English Questions
```
What is ITRI?
What research areas does ITRI focus on?
When was ITRI established?
What are ITRI's main technological achievements?
How does ITRI contribute to Taiwan's industrial development?
What is ITRI's organizational structure?
Who is the current president of ITRI?
How does ITRI support talent development?
What are ITRI's key innovation programs?
How does ITRI collaborate with industry partners?
```

### Mixed Language Questions
```
What is 工研院's role in Taiwan's technology ecosystem?
告訴我 ITRI 的 AI research programs
How does 工研院 promote 產業創新?
Explain ITRI's semiconductor 研究計畫
```

### Example API Calls
```bash
# Traditional Chinese
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "工研院有什麼研究領域？", "session_id": "demo"}' \
  --no-buffer

# English
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "What research areas does ITRI focus on?", "session_id": "demo"}' \
  --no-buffer
```

## 🔧 Usage Examples

### Python Client

```python
import requests

# Streaming query
def query_rag_llm(text_msg, session_id="my_session"):
    url = "http://localhost:5002/api/rag-llm/query"
    payload = {
        "text_user_msg": text_msg,
        "session_id": session_id
    }
    
    with requests.post(url, json=payload, stream=True) as response:
        accumulated = ""
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                if "END_FLAG" in chunk:
                    break
                accumulated += chunk
                print(chunk, end="", flush=True)
        
        return accumulated

# Warmup models (recommended after service start)
def warmup_models():
    url = "http://localhost:5002/api/rag-llm/warmup"
    response = requests.post(url, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        print(f"🔥 Model Warmup Results:")
        print(f"  Overall Success: {result['overall_success']}")
        print(f"  📚 Embedding: {result['embedding_model']['status']}")
        print(f"  🤖 LLM: {result['llm_model']['status']}")
        return result['overall_success']
    return False

# Example usage
warmup_models()  # Warm up models first
response = query_rag_llm("工研院有什麼研究領域？")  # Traditional Chinese
# Or in English: query_rag_llm("What research areas does ITRI focus on?")

# Close connection before program termination
def close_session(session_id="my_session"):
    url = "http://localhost:5002/api/rag-llm/close"
    payload = {"session_id": session_id}
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"Connection closed: {result['messages_cleared']} messages cleared")
        return True
    return False

# Always close before termination
close_session("my_session")
```

### Curl Examples

```bash
# Health check
curl http://localhost:5002/health

# Initialize RAG system
curl -X POST http://localhost:5002/api/rag-llm/init

# Warmup models (recommended after startup)
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Stream a query
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "What is ITRI?", "session_id": "test_session"}' \
  --no-buffer

# Get session history
curl http://localhost:5002/api/rag-llm/sessions/test_session/history

# Clear session history
curl -X DELETE http://localhost:5002/api/rag-llm/sessions/test_session/history

# Close connection elegantly (before program termination)
curl -X POST http://localhost:5002/api/rag-llm/close \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session"}'
```

### JavaScript/Node.js Client

```javascript
async function queryRAGLLM(textMsg, sessionId = "js_session") {
    const response = await fetch('http://localhost:5002/api/rag-llm/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text_user_msg: textMsg,
            session_id: sessionId
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let accumulated = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        if (chunk.includes('END_FLAG')) {
            break;
        }
        
        accumulated += chunk;
        process.stdout.write(chunk);
    }
    
    return accumulated;
}

// Warmup models function
async function warmupModels() {
    try {
        const response = await fetch('http://localhost:5002/api/rag-llm/warmup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        console.log('🔥 Model Warmup Results:');
        console.log(`  Overall Success: ${result.overall_success}`);
        console.log(`  📚 Embedding: ${result.embedding_model.status}`);
        console.log(`  🤖 LLM: ${result.llm_model.status}`);
        return result.overall_success;
    } catch (error) {
        console.error('Model warmup failed:', error);
        return false;
    }
}

// Close connection function
async function closeConnection(sessionId = "js_session") {
    try {
        const response = await fetch('http://localhost:5002/api/rag-llm/close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        const result = await response.json();
        console.log(`Connection closed: ${result.messages_cleared} messages cleared`);
        return result.success;
    } catch (error) {
        console.error('Connection close failed:', error);
        return false;
    }
}

// Example usage
warmupModels()  // Warm up models first
    .then(success => {
        if (success) {
            console.log("✅ Models warmed up successfully");
            return queryRAGLLM("工研院有什麼研究領域？");  // Traditional Chinese
        } else {
            console.log("⚠️ Model warmup failed, continuing anyway...");
            return queryRAGLLM("What research areas does ITRI focus on?");  // English
        }
    })
    .then(response => {
        console.log("\nComplete response:", response);
        // Always close connection before termination
        return closeConnection("js_session");
    })
    .then(closed => {
        if (closed) {
            console.log("✅ Connection closed successfully");
        } else {
            console.log("⚠️ Connection close may have failed");
        }
    });
```

## 🔧 Configuration

### Environment Variables

- `OLLAMA_HOST`: Ollama service host (default: localhost)
- `OLLAMA_PORT`: Ollama service port (default: 11435)
- `RAG_MODEL`: LLM model to use (default: linly-llama3.1:70b-instruct-q4_0)

### Service Configuration

- **Default Port**: 5002
- **Default Host**: 0.0.0.0 (all interfaces)
- **Max Chat History**: 10 messages per session
- **RAG Context Limit**: 2000 characters
- **Temperature**: 0.3 (for consistent responses)

## 📋 Requirements

1. **Ollama Service**: Must be running on localhost:11435
2. **LLM Model**: `linly-llama3.1:70b-instruct-q4_0` must be available
3. **ChromaDB**: Optional - service will auto-detect or create ChromaDB
4. **Python**: 3.8+ with required packages

**Note**: The API service automatically searches for existing ChromaDB in multiple locations:
- f"{CHROMA_DB_PATH}"

If no existing ChromaDB is found, the service will create a new one with sample data.

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**:
   - Check if port 5002 is available
   - Ensure all dependencies are installed

2. **RAG initialization fails**:
   - Service will auto-detect or create ChromaDB - check logs for specific errors
   - Ensure write permissions in workspace directory for ChromaDB creation
   - Check if existing ChromaDB collections are accessible

3. **Ollama connection fails**:
   - Ensure Ollama service is running: `ollama serve`
   - Verify model is available: `ollama list`

4. **Empty responses**:
   - Initialize RAG system: `POST /api/rag-llm/init`
   - Check Ollama model availability

### Debug Mode

Run with debug mode for detailed logs:
```bash
python rag_llm_api.py --debug
```

## 🔄 Integration

This API service is designed to work alongside the main integrated pipeline. Both services can run simultaneously on different ports:

- **Main Pipeline**: http://localhost:5001 (ASR + RAG + TTS)
- **RAG API Service**: http://localhost:5002 (RAG + LLM only)

## 📊 Performance Notes

- **First Query**: May take longer due to model initialization
- **Subsequent Queries**: Optimized with cached system prompts
- **Session History**: Kept in memory (restart clears all sessions)
- **Concurrent Sessions**: Supported via Flask threading