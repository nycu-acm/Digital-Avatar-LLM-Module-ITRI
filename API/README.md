# API Module Documentation

## Overview

The `API` folder contains the Flask-based REST API service and supporting utilities for the ITRI Museum RAG + LLM system. This module provides HTTP endpoints for intelligent question-answering with dynamic tone adaptation, session management, and real-time streaming responses.

## Folder Structure

```
API/
├── rag_llm_api.py                    # Main Flask API service (Port 5002)
├── tone_system_prompts_no_tag.py     # Tone conversion prompts (no expression tags)
├── tone_system_prompts.py            # Tone conversion prompts (with expression tags)
├── client_utils.py                   # Client utility functions
├── random_user_description_server.py  # Vision API simulator (Port 5003)
├── model_warmup_server.py            # Model warmup service
├── api_client_example.py             # Basic API client example
├── api_client_tone_example.py        # Tone conversion client example
├── test_rag_llm_api.py               # API testing script
└── model-warmup.service              # Systemd service file
```

## Core Components

### 1. RAG LLM API Service (`rag_llm_api.py`)

**Purpose**: Main Flask API server that provides RAG + LLM functionality via HTTP endpoints.

**Key Features**:
- **Streaming Responses**: Real-time text streaming with END_FLAG termination
- **Dynamic Tone Adaptation**: Automatic tone selection based on visual user analysis
- **Parallel Processing**: Simultaneously fetches user descriptions and generates QA responses
- **Session Management**: Maintains conversation history per session
- **Query Rewriting**: Intelligently rewrites queries for better document retrieval
- **Hybrid RAG Search**: Combines dense (ChromaDB) and sparse (TF-IDF) retrieval
- **Multi-language Support**: English and Traditional Chinese (繁體中文)

**Default Port**: 5002

**Key Endpoints**:
- `POST /api/rag-llm/query`: Main query endpoint with optional tone conversion
- `POST /api/rag-llm/query-with-tone`: Query with automatic dynamic tone conversion
- `POST /api/rag-llm/convert-tone`: Standalone tone conversion service
- `POST /api/rag-llm/init`: Initialize RAG system
- `POST /api/rag-llm/warmup`: Preload models
- `POST /api/rag-llm/close`: Graceful session cleanup
- `GET /api/rag-llm/sessions/{id}/history`: Get session history
- `DELETE /api/rag-llm/sessions/{id}/history`: Clear session history
- `GET /health`: Health check

### 2. Tone System Prompts (`tone_system_prompts_no_tag.py`)

**Purpose**: System prompts for tone conversion without expression tags.

**Supported Tones**:
- `child_friendly`: For children (0-17 years) - "科學探險隊隊長" role
- `elder_friendly`: For elderly (65+ years) - "資深導覽員" role
- `professional_friendly`: For business/professional contexts - "官方專家導覽員" role
- `casual_friendly`: For general adults (default) - "科技嚮導" role

**Key Functions**:
- `get_tone_system_prompt(tone, target_lang)`: Get tone-specific system prompt
- `build_tone_selector_system_prompt(target_lang)`: Create tone selection agent prompt
- `build_fixed_system_prompt(response_restriction)`: Create QA agent system prompt
- `build_query_rewriter_prompt(target_lang)`: Create query rewriting agent prompt

**Note**: `tone_system_prompts.py` is the older version with expression tags. The system uses `tone_system_prompts_no_tag.py` by default.

### 3. Client Utilities (`client_utils.py`)

**Purpose**: Utility functions for building API clients.

**Key Functions**:
- `stream_rag_llm_query(api_url, text_user_msg, session_id)`: Stream query to API
- `check_service_health(api_url)`: Check if service is healthy
- `initialize_rag_system(api_url)`: Initialize RAG system via API
- `warmup_models(api_url)`: Preload models to reduce latency
- `close_connection(api_url, session_id)`: Gracefully close session
- `convert_tone(text, tone, ...)`: Convert text tone (non-streaming)
- `stream_convert_tone(text, tone, ...)`: Convert text tone (streaming)

### 4. Random User Description Server (`random_user_description_server.py`)

**Purpose**: Simulates Vision Context API for testing dynamic tone selection.

**Default Port**: 5003

**Endpoints**:
- `GET /sessions`: Get active sessions
- `GET /visual-context/{sessionid}`: Get random visual description
- `GET /api/simulator/pool`: Get description pool info

**Use Case**: Development and testing when real VLM is not available.

### 5. Model Warmup Server (`model_warmup_server.py`)

**Purpose**: Standalone service that periodically warms up models to keep them ready.

**Features**:
- Runs warmup every 10 minutes (configurable)
- Monitors API service health
- Tracks warmup statistics
- Graceful shutdown handling

**Usage**:
```bash
python model_warmup_server.py --api-url http://localhost:5002 --interval 60
```

### 6. Example Clients

**`api_client_example.py`**: Basic example showing how to use the API service
- Health check
- RAG initialization
- Model warmup
- Query streaming
- Tone conversion
- Session cleanup

**`api_client_tone_example.py`**: Comprehensive tone conversion examples
- Standalone tone conversion
- Query with automatic tone conversion
- Original query with optional tone
- Non-streaming tone conversion

## Quick Start

### Step 1: Install Dependencies

```bash
pip install flask flask-cors requests chromadb numpy scikit-learn jieba
```

### Step 2: Start Supporting Services (Optional)

**Random User Description Server** (for testing):
```bash
python random_user_description_server.py --port 5003
```

**Model Warmup Server** (optional, for production):
```bash
python model_warmup_server.py --api-url http://localhost:5002 --interval 10
```

### Step 3: Start Main API Server

```bash
# Basic startup
python rag_llm_api.py

# With auto-initialization
python rag_llm_api.py --auto-init

# With Vision API integration
python rag_llm_api.py --auto-init --user-description-server http://localhost:5003

# Custom host/port
python rag_llm_api.py --host 0.0.0.0 --port 5002 --auto-init --debug
```

### Step 4: Test the Service

```bash
# Health check
curl http://localhost:5002/health

# Warmup models
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Run example client
python api_client_example.py
```

## API Endpoints Reference

### Health Check

**GET** `/health`

Check service status and RAG initialization state.

**Response**:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1234567890.123
}
```

### RAG + LLM Query

**POST** `/api/rag-llm/query`

Main query endpoint with optional tone conversion.

**Request Body**:
```json
{
  "text_user_msg": "What is ITRI?",
  "session_id": "optional_session_id",
  "include_history": true,
  "user_description": "visual description (optional)",
  "convert_tone": false
}
```

**Response**: Streaming text chunks followed by `END_FLAG`

**Example**:
```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "What is ITRI?", "session_id": "demo"}' \
  --no-buffer
```

### Query with Automatic Tone Conversion

**POST** `/api/rag-llm/query-with-tone`

Query with automatic dynamic tone conversion based on user description.

**Request Body**:
```json
{
  "text_user_msg": "What is ITRI?",
  "session_id": "session_id",
  "user_description": "a young boy wearing glasses",
  "convert_tone": true
}
```

**Response**: Streaming tone-adapted response with `END_FLAG`

**Workflow**:
1. Parallel processing: Fetch user description + Generate QA response
2. Determine tone from user description
3. Convert response to selected tone
4. Stream adapted response

### Standalone Tone Conversion

**POST** `/api/rag-llm/convert-tone`

Convert text tone without RAG query.

**Request Body**:
```json
{
  "text": "Text to convert",
  "tone": "child_friendly",
  "stream": true,
  "user_description": "visual description (optional)",
  "user_msg": "original user message (optional)"
}
```

**Response** (streaming):
- Text chunks followed by `END_FLAG`

**Response** (non-streaming):
```json
{
  "success": true,
  "original_text": "...",
  "converted_text": "...",
  "tone": "child_friendly",
  "user_description": "..."
}
```

### Initialize RAG System

**POST** `/api/rag-llm/init`

Initialize the RAG system (loads ChromaDB, builds indices).

**Response**:
```json
{
  "success": true,
  "rag_initialized": true,
  "message": "RAG system initialized successfully"
}
```

### Model Warmup

**POST** `/api/rag-llm/warmup`

Preload embedding model and LLM to reduce latency.

**Response**:
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

**Purpose**: Recommended to call after starting the service to reduce first-request latency.

### Session Management

**GET** `/api/rag-llm/sessions/{session_id}/history`

Get conversation history for a session.

**Response**:
```json
{
  "session_id": "demo_session",
  "history": [
    {"role": "user", "content": "What is ITRI?"},
    {"role": "assistant", "content": "ITRI is..."}
  ],
  "message_count": 2
}
```

**DELETE** `/api/rag-llm/sessions/{session_id}/history`

Clear conversation history for a session.

### Graceful Connection Close

**POST** `/api/rag-llm/close`

Gracefully close session and clean up history.

**Request Body**:
```json
{
  "session_id": "session_to_close"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "session_to_close",
  "message": "Connection closed successfully",
  "session_existed": true,
  "messages_cleared": 15,
  "timestamp": 1234567890.123
}
```

**Purpose**: Client should call this before program termination to clean up session data.

## Usage Examples

### Python Client Example

```python
from client_utils import (
    stream_rag_llm_query, 
    check_service_health, 
    warmup_models, 
    close_connection
)

API_URL = "http://localhost:5002"
SESSION_ID = "my_session"

# Check service health
if check_service_health(API_URL):
    # Warmup models
    warmup_models(API_URL)
    
    # Query with streaming
    response = stream_rag_llm_query(
        API_URL, 
        "What is ITRI?", 
        SESSION_ID
    )
    
    # Close connection
    close_connection(API_URL, SESSION_ID)
```

### Direct API Calls

```python
import requests

# Query with tone conversion
payload = {
    "text_user_msg": "工研院是什麼？",
    "session_id": "demo",
    "user_description": "a young boy wearing glasses",
    "convert_tone": True
}

response = requests.post(
    "http://localhost:5002/api/rag-llm/query-with-tone",
    json=payload,
    stream=True
)

for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
    if chunk:
        if "END_FLAG" in chunk:
            break
        print(chunk, end="", flush=True)
```

### Tone Conversion Example

```python
from client_utils import stream_convert_tone

# Convert text to child-friendly tone
converted = stream_convert_tone(
    "ITRI was founded in 1973.",
    tone="child_friendly"
)
```

## Configuration

### Command Line Arguments

**`rag_llm_api.py`**:
```bash
python rag_llm_api.py \
  --host 0.0.0.0 \              # Host to bind to
  --port 5002 \                 # Port to bind to
  --debug \                     # Enable debug mode
  --auto-init \                 # Auto-initialize RAG on startup
  --user-description-server http://localhost:5004  # Vision API URL
```

**`random_user_description_server.py`**:
```bash
python random_user_description_server.py \
  --host 0.0.0.0 \
  --port 5003 \
  --debug
```

**`model_warmup_server.py`**:
```bash
python model_warmup_server.py \
  --api-url http://localhost:5002 \
  --interval 10 \               # Warmup interval in minutes
  --test                         # Run single test and exit
```

### Environment Variables

```bash
# GPU Configuration
export CUDA_VISIBLE_DEVICES=0,1,2,3

# Ollama Configuration
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_MODELS=/usr/share/ollama/.ollama/models
export OLLAMA_SCHED_SPREAD=1
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE=60m
```

### Configuration File (`config.py` in parent directory)

```python
# LLM Model Configuration
LLM_MODEL_NAME = "linly-llama3.1:70b-instruct-q4_0"

# ChromaDB Path Configuration
CHROMA_DB_PATH = "/path/to/chroma_db_golden"
```

## System Architecture

### Parallel Processing Flow

The API service uses parallel processing to minimize latency:

```
Client Request
     │
     ├─────────────────────────────────────────┐
     │                                          │
     ▼                                          ▼
┌─────────────────────┐              ┌──────────────────────┐
│ Fetch User Desc     │              │ Generate QA Response │
│ from Vision API     │   PARALLEL   │ using RAG + LLM      │
│ (Task 1)            │   EXECUTION  │ (Task 2)             │
└─────────────────────┘              └──────────────────────┘
     
     │         Wait for both to complete        │
     └─────────────────┬────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Determine Tone from  │
            │ User Description     │
            └──────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Convert QA Response  │
            │ to Selected Tone     │
            └──────────────────────┘
                       │
                       ▼
            Stream Response to Client
```

### Service Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│              (Web, Mobile, Desktop, CLI Tools)              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask API Server (Port 5002)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         RAGLLMAPIService Class                       │   │
│  │  • Session Management                                │   │
│  │  • Parallel Processing Orchestration                 │   │
│  │  • Tone Conversion Coordination                      │   │
│  │  • Streaming Response Handling                       │   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬───────────────────┬───────────────────┬─────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌────────────────┐   ┌──────────────┐
│  RAG Pipeline│   │ Vision Context │   │  Ollama LLM  │
│  (ChromaDB)  │   │  API (VLM)     │   │ (Port 11435) │
│              │   │  (Port 5004)   │   │              │
│  • Document  │   │  or Simulator  │   │  • QA Agent  │
│    Loading   │   │  (Port 5003)   │   │  • Tone      │
│  • Chunking  │   │                │   │    Converter │
│  • Embedding │   │  • Visual      │   │  • Query     │
│  • Hybrid    │   │    Analysis    │   │    Rewriter  │
│    Search    │   │  • User Desc   │   │              │
└──────────────┘   └────────────────┘   └──────────────┘
```

## Tone Conversion System

### Available Tones

1. **child_friendly**: For children and teenagers (0-17 years)
   - Role: "科學探險隊隊長" (Science Adventure Team Leader)
   - Style: Energetic, curious, vivid metaphors, interactive phrases
   - Example: "哇！被你發現這個超酷的秘密了！這棵大樹的頭頂上藏著六個超強的「隱形小風扇」喔！"

2. **elder_friendly**: For elderly users (65+ years)
   - Role: "資深導覽員" (Senior Guide)
   - Style: Warm, storytelling-based, respectful, gentle expressions
   - Example: "您說的對，其實這棵大樹背後有很深的情感與科學。說起這棵樹的運作方式啊..."

3. **professional_friendly**: For business/professional contexts
   - Role: "官方專家導覽員" (Official Expert Guide)
   - Style: Professional, authoritative, formal vocabulary ("您" instead of "你")
   - Example: "關於生態樹的溫控機制，其核心在於透過高效能的空氣循環系統來達成。"

4. **casual_friendly**: For general adult users (default)
   - Role: "科技嚮導" (Tech Guide)
   - Style: Chill, conversational, like talking to a friend
   - Example: "其實這棵樹的設計蠻聰明的。簡單來說，它的頂端藏了六台風扇..."

### Tone Selection Logic

The system automatically determines tone based on user description:

- **Age 0-17**: `child_friendly`
- **Age 55+**: `elder_friendly`
- **Business/formal context**: `professional_friendly`
- **General adults/unclear**: `casual_friendly` (default)

### Tone Conversion Features

- **First Message Behavior**: Mandatory appearance reference for first messages
- **Subsequent Messages**: 20% probability to reference appearance (configurable via `PERCENTAGE`)
- **Context Integration**: Includes user appearance and original message
- **Language Detection**: Automatic Chinese/English detection
- **Streaming Support**: Real-time tone conversion streaming

## Session Management

### Session Storage

- **Storage Type**: In-memory dictionary (`chat_sessions[session_id]`)
- **Format**: List of message dictionaries with `role` and `content`
- **History Storage**: Stores original (pre-tone) responses for context
- **Cleanup**: Automatic cleanup on `/api/rag-llm/close`

### Session Lifecycle

1. **Create**: Automatically created on first query with `session_id`
2. **Update**: Messages appended to history after each query
3. **Retrieve**: Use `GET /api/rag-llm/sessions/{id}/history`
4. **Clear**: Use `DELETE /api/rag-llm/sessions/{id}/history`
5. **Close**: Use `POST /api/rag-llm/close` before program termination

## Query Processing Pipeline

### Step 1: Query Reception

- Parse JSON request body
- Validate required fields (`text_user_msg`)
- Retrieve session history (if `include_history=true`)
- Detect input language (Chinese/English)

### Step 2: Parallel Processing

**Task 1: Fetch User Description** (if not provided)
- Calls Vision Context API (`http://localhost:5004/visual-context/{session_id}`)
- Waits 2 seconds before fetching (allows VLM to process)
- Returns visual description like: "a young boy wearing glasses, and is smiling"

**Task 2: Generate QA Response**
- Query rewriting using chat history context
- RAG retrieval (hybrid search: ChromaDB + TF-IDF)
- Context processing and ranking
- LLM generation with structured JSON prompt
- Response collection (max 150 chars for tone conversion)

### Step 3: Tone Determination

- Visual analysis of user description
- Tone selection: `child_friendly`, `elder_friendly`, `professional_friendly`, or `casual_friendly`
- Default fallback: `casual_friendly` if no description available

### Step 4: Tone Conversion (if enabled)

- System prompt selection for selected tone
- Context integration (appearance, original message, first message flag)
- Streaming conversion via Ollama LLM
- Maintains factual accuracy while adapting emotional tone

### Step 5: Response Delivery

- Stream tone-converted chunks (or original if no conversion)
- Send `END_FLAG` when complete
- Update session history with original (pre-tone) response

## Testing

### Run Example Clients

```bash
# Basic API client example
python api_client_example.py

# Tone conversion example
python api_client_tone_example.py
```

### Run Test Script

```bash
python test_rag_llm_api.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:5002/health

# Initialize RAG
curl -X POST http://localhost:5002/api/rag-llm/init

# Warmup models
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Query
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{"text_user_msg": "What is ITRI?", "session_id": "test"}' \
  --no-buffer

# Query with tone conversion
curl -X POST http://localhost:5002/api/rag-llm/query-with-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "test",
    "user_description": "a young boy wearing glasses",
    "convert_tone": true
  }' \
  --no-buffer
```

## Troubleshooting

### Issue: Service Won't Start

**Symptoms**: Port already in use or binding errors

**Solutions**:
```bash
# Check if port is in use
lsof -i :5002

# Use different port
python rag_llm_api.py --port 5003

# Check dependencies
pip install flask flask-cors requests chromadb
```

### Issue: RAG Initialization Fails

**Symptoms**: "RAG initialization failed" or ChromaDB errors

**Solutions**:
```bash
# Check ChromaDB path in config.py
cat ../config.py | grep CHROMA_DB_PATH

# Verify ChromaDB exists
ls -la $(python -c "from config import CHROMA_DB_PATH; print(CHROMA_DB_PATH)")

# Rebuild database
cd ../LLM_Chat
python create_showroom_db.py --golden --reload
```

### Issue: Ollama Connection Errors

**Symptoms**: Cannot connect to Ollama API

**Solutions**:
```bash
# Check if Ollama is running
curl http://localhost:11435/api/tags

# Verify models are downloaded
ollama list

# Restart Ollama
pkill ollama
ollama serve
```

### Issue: Vision API Connection Failed

**Symptoms**: "Could not connect to Vision Context API"

**Solutions**:
- Check if Vision API server is running: `curl http://localhost:5004/sessions`
- Use random description server for testing: `--user-description-server http://localhost:5003`
- System will fallback to `casual_friendly` tone if Vision API unavailable

### Issue: Empty Responses

**Solutions**:
```bash
# Initialize RAG system
curl -X POST http://localhost:5002/api/rag-llm/init

# Check health
curl http://localhost:5002/health

# Verify ChromaDB collection exists
python -c "import chromadb; client = chromadb.PersistentClient(path='chroma_db_golden'); print([c.name for c in client.list_collections()])"
```

### Issue: Slow First Request

**Solutions**:
```bash
# Warmup models before first real request
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Or use model warmup server
python model_warmup_server.py --api-url http://localhost:5002
```

## Production Deployment

### Systemd Service (Model Warmup)

The `model-warmup.service` file can be used to run the warmup server as a systemd service:

```bash
# Copy service file
sudo cp model-warmup.service /etc/systemd/system/

# Enable and start
sudo systemdctl daemon-reload
sudo systemctl enable model-warmup.service
sudo systemctl start model-warmup.service

# Check status
sudo systemctl status model-warmup.service
```

### Recommended Startup Sequence

1. **Start Ollama Server**:
```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
OLLAMA_HOST=127.0.0.1:11435 \
ollama serve
```

2. **Start Vision Context API** (if using real VLM):
```bash
python vision_api_multi_session.py
```

3. **Start Random Description Server** (for testing):
```bash
python random_user_description_server.py --port 5003
```

4. **Start Main API Server**:
```bash
python rag_llm_api.py --auto-init --user-description-server http://localhost:5003
```

5. **Start Model Warmup Server** (optional):
```bash
python model_warmup_server.py --api-url http://localhost:5002 --interval 10
```

### Performance Optimization

- **Model Warmup**: Always warmup models after startup
- **Session Management**: Clear old sessions periodically
- **Parallel Processing**: Already implemented for optimal latency
- **Caching**: System prompts are cached for faster response

## Integration with Other Components

### RAG Pipeline Integration

The API service integrates with `LLM_Chat/RAG_LLM_realtime.py`:

```python
from LLM_Chat.RAG_LLM_realtime import ImprovedRAGPipeline

# Initialize RAG pipeline
self.rag_pipeline = ImprovedRAGPipeline()

# Use for hybrid search
results = self.rag_pipeline.hybrid_search(query, chroma_collection, top_k=6)
```

### Vision Context API Integration

The API service can integrate with real Vision Context API or use the simulator:

- **Production**: `http://localhost:5004` (real VLM)
- **Development**: `http://localhost:5003` (random descriptions)

### ChromaDB Integration

The API service loads ChromaDB collections created by:
- `LLM_Chat/create_showroom_db.py` (structured data, collection: `chroma_db_golden`)
- `LLM_Chat/RAG_LLM_realtime.py` (general documents, collection: `itri_museum_collection`)

## Additional Resources

- [Main README](../README.md) - Complete system documentation
- [RAG Pipeline Documentation](../LLM_Chat/README.md) - Core RAG pipeline details
- [API Server Methodology](../RAG_LLM_Server_Methodology.md) - Technical deep dive
- [Client Utils Documentation](README_client_utils.md) - Client development guide
- [Tone Conversion Guide](README_tone_conversion.md) - Tone system details

## License

This module is part of the ITRI Museum RAG system, developed for educational and research purposes at the Industrial Technology Research Institute (ITRI).
