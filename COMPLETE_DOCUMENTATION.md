# ITRI Museum RAG + LLM System - Complete Documentation

**Version:** 1.0  
**Last Updated:** 2026-01-06  
**Project:** ITRI Cultural AI Agent  
**Organization:** Industrial Technology Research Institute (ITRI)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Core Components](#core-components)
5. [Technical Implementation](#technical-implementation)
6. [API Reference](#api-reference)
7. [Configuration Guide](#configuration-guide)
8. [Deployment Guide](#deployment-guide)
9. [Usage Examples](#usage-examples)
10. [Troubleshooting](#troubleshooting)
11. [Performance Optimization](#performance-optimization)
12. [Future Enhancements](#future-enhancements)

---

## Executive Summary

The ITRI Museum RAG + LLM System is a comprehensive **Retrieval-Augmented Generation (RAG)** platform that provides intelligent, context-aware question-answering with **automatic tone adaptation** based on visual user analysis. The system combines advanced document retrieval, large language models, and vision language models to deliver personalized responses in both English and Traditional Chinese (繁體中文).

### Key Capabilities

- **Intelligent Q&A**: Context-aware answers using document retrieval from ITRI knowledge base
- **Dynamic Tone Adaptation**: Automatic response style adjustment (child-friendly, elder-friendly, professional, casual)
- **Multi-modal Integration**: Vision-based user analysis for personalized interactions
- **Real-time Streaming**: Immediate feedback with progressive response generation
- **Session Management**: Conversation context maintenance across interactions
- **Multi-language Support**: English and Traditional Chinese (繁體中文)

### Technology Stack

- **LLM**: Ollama (linly-llama3.1:70b-instruct-q4_0)
- **Embeddings**: bge-m3:latest (via Ollama)
- **Vector Database**: ChromaDB
- **API Framework**: Flask
- **Search**: Hybrid (Dense 70% + Sparse TF-IDF 30%)
- **Text Processing**: Jieba (Chinese tokenization)

---

## Project Overview

### Problem Statement

Traditional museum guides provide static, one-size-fits-all information. The ITRI Museum system addresses this by creating a **dynamic, personalized museum guide** that adapts to visitor demographics, appearance, and context.

### Use Case Scenario

**Cultural Museum AI Guide Workflow:**

1. **Visitor Arrival**: Visitor enters the exhibition hall
2. **Vision & Greeting**: Avatar detects user features (emotion, age, accessories, environment)
   - *Example detected*: Boy, 6 years old, glasses, happy
3. **Interaction**: User speaks (e.g., "Wow! This looks cool!")
4. **AI Processing**: System generates text, audio, and lip-sync responses
5. **Agent Reply**: Dynamic, personalized response delivered in appropriate tone (e.g., Surprised & Excited)

### Project Goals

- Provide accurate, factual information about ITRI
- Adapt communication style to user demographics
- Maintain conversation context for follow-up questions
- Deliver responses in real-time with streaming
- Support multiple languages (English/繁體中文)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                      │
│              (Web, Mobile, Desktop, CLI Tools)              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST API (Port 5002)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask API Server (Port 5002)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                RAGLLMAPIService Class                │   │
│  │          • Session Management                        │   │
│  │          • Parallel Processing Orchestration         │   │
│  │          • Tone Conversion Coordination              │   │
│  │          • Streaming Response Handling               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────┬────────────────────┬───────────────────┬──────────┘
          │                    │                   │
          ▼                    ▼                   ▼
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

### Three Main Modules

#### 1. Multi-Modal Perception

- **ASR**: Whisper handles user voice and text input
- **Visual Input**: VLM processes images/video frames for semantic expression
- **User Description**: Extracts age, emotion, accessories, environment

#### 2. Auto-Prompt based RAG

- **User Query Rewriting**: Enhances retrieval accuracy
- **Vector DB**: ChromaDB for document storage
- **Auto Prompt Generation**: Role, Task, Style, Tone selection
- **Llama LLM Generation**: Context-aware response generation

**Note**: Currently uses fixed tone-converting prompts selected based on user description. Future enhancement: dynamic auto-prompt methodology.

#### 3. Emotional Talk Avatar

- **Thread Pool Framework**: Parallel processing for TTS and avatar rendering
- **Emotional TTS**: Tone-adapted speech synthesis
- **Audio-driven Avatar**: H.264 Video + Audio output

### Data Flow

```
               ┌─────────┐
               │ Client  │
               └────┬────┘
                    │ POST /api/rag-llm/query-with-tone
                    ▼
┌─────────────────────────────────────────┐
│      Flask API Server (Port 5002)       │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │       Parallel Processing         │  │
│  │  ┌──────────────┐ ┌─────────────┐ │  │
│  │  │ Task 1:      │ │ Task 2:     │ │  │
│  │  │ Vision API   │ │ RAG + LLM   │ │  │
│  │  └──────┬───────┘ └──────┬──────┘ │  │
│  └─────────┼────────────────┼────────┘  │
│            │                │           │
└────────────┼────────────────┼───────────┘
             │                │
             ▼                ▼
  ┌──────────────┐  ┌──────────────────┐
  │ Vision API   │  │  ChromaDB        │
  │ (Port 5004)  │  │  + Ollama LLM    │
  │              │  │  (Port 11435)    │
  │ GET /visual- │  │  • Embedding     │
  │ context/{id} │  │  • Hybrid Search │
  └──────┬───────┘  │  • QA Generation │
         │          └────────┬─────────┘
         │                   │
         └─────────┬─────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Tone Selection  │
          │ + Conversion    │
          │ (Ollama LLM)    │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Stream Response │
          │ to Client       │
          └─────────────────┘
```

---

## Core Components

### 1. API Module (`API/`)

**Purpose**: Flask-based REST API service providing HTTP endpoints for RAG + LLM functionality.

#### 1.1 RAG LLM API Service (`rag_llm_api.py`)

**Key Features**:
- Streaming responses with END_FLAG termination
- Dynamic tone adaptation based on visual user analysis
- Parallel processing (user description + QA generation)
- Session management with conversation history
- Query rewriting for better retrieval
- Hybrid RAG search (ChromaDB + TF-IDF)

**Default Port**: 5002

**Main Endpoints**:
- `POST /api/rag-llm/query`: Main query endpoint with optional tone conversion
- `POST /api/rag-llm/query-with-tone`: Query with automatic dynamic tone conversion
- `POST /api/rag-llm/convert-tone`: Standalone tone conversion service
- `POST /api/rag-llm/init`: Initialize RAG system
- `POST /api/rag-llm/warmup`: Preload models
- `POST /api/rag-llm/close`: Graceful session cleanup
- `GET /api/rag-llm/sessions/{id}/history`: Get session history
- `DELETE /api/rag-llm/sessions/{id}/history`: Clear session history
- `GET /health`: Health check

#### 1.2 Tone System Prompts (`tone_system_prompts_no_tag.py`)

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

#### 1.3 Supporting Services

**Random User Description Server** (`random_user_description_server.py`):
- Simulates Vision Context API for testing
- Default Port: 5003
- Provides random visual descriptions for development

**Model Warmup Server** (`model_warmup_server.py`):
- Periodically warms up models to reduce latency
- Configurable interval (default: 60 minutes)
- Monitors API service health

**Client Utilities** (`client_utils.py`):
- Helper functions for building API clients
- Streaming query functions
- Health check utilities
- Tone conversion utilities

### 2. LLM_Chat Module (`LLM_Chat/`)

**Purpose**: Core RAG pipeline and database creation tools.

#### 2.1 ImprovedRAGPipeline (`RAG_LLM_realtime.py`)

**Purpose**: General document processing with semantic chunking.

**Key Features**:
- Hybrid search: ChromaDB dense (70%) + TF-IDF sparse (30%)
- Semantic chunking: 300 chars, 50 overlap, respects sentence boundaries
- Multi-format support: JSON (raw_data, qa_pairs, structured_data) and TXT files
- Multilingual: Native Traditional Chinese support with Jieba tokenization
- Gradio UI: Optional web interface with real-time TTS playback

**Use Case**: General documents where semantic chunking is beneficial (long documents, articles, unstructured text).

#### 2.2 Database Builder (`create_showroom_db.py`)

**Purpose**: Creates ChromaDB database from structured JSON data using "One Item = One Chunk" strategy.

**Key Features**:
- Structured data processing: Optimized for QA pairs, glossary, news
- One-to-one mapping: Each JSON item = one chunk (preserves structure)
- Smart formatting: Auto-formats content based on data type
- Batch processing: Processes embeddings in batches of 10

**Use Case**: Structured data where preserving item boundaries is important (QA pairs, glossary entries, news articles).

**Supported Data Formats**:
- **QA Pairs**: `{"question": "...", "answer": "..."}`
- **Glossary**: `{"term": "...", "full_name": "...", "content": "..."}`
- **News**: `{"date": "...", "title": "...", "content": "..."}`
- **General**: `{"title": "...", "content": "..."}`

**Comparison**:

| Feature | `create_showroom_db.py` | `RAG_LLM_realtime.py` |
|---------|------------------------|----------------------|
| **Chunking Strategy** | One Item = One Chunk | Semantic Chunking (300 chars, 50 overlap) |
| **Data Source** | `database_wiki_gemini整理_一定對的.../` | `itri_museum_docs/` |
| **Collection Name** | `chroma_db_golden` | `itri_museum_collection` |
| **Best For** | Structured data (QA, Glossary, News) | General documents (articles, long text) |
| **Preserves Structure** | ✅ Yes (item boundaries) | ⚠️ May split items |
| **Search Quality** | High for exact matches | High for semantic similarity |

---

## Technical Implementation

### LLM Module Pipeline

**Complete Processing Flow**:

1. **Input**: User query enters the system
2. **Query Rewriter**: Rewrites input using chat history context
   - Example: "他什麼時候上任的？" → "工研院院長張培仁博士的上任日期與就職時間"
3. **Embedding & Search**: Searches RAG DB for top k reference chunks
   - Hybrid search: 70% dense (ChromaDB) + 30% sparse (TF-IDF)
4. **Question Answering**: Generates factual response based on retrieved context
5. **Tone Selector & Converter**:
   - Selects tone based on Vision Server data
   - Converts factual response into stylized response
6. **Streaming**: Final output streamed to user with END_FLAG termination

### Parallel Processing Architecture

**Key Innovation**: Uses `ThreadPoolExecutor` to execute two tasks simultaneously:

**Task 1: Fetch User Description**
- Calls Vision Context API (`http://localhost:5004/visual-context/{session_id}`)
- Waits 2 seconds before fetching (allows VLM to process recent frames)
- Returns visual description: "a young boy wearing glasses, and is smiling"

**Task 2: Generate QA Response**
- Query rewriting using chat history context
- RAG retrieval (hybrid search: ChromaDB + TF-IDF)
- Context processing and ranking
- LLM generation with structured JSON prompt
- Response collection (max 150 chars for tone conversion)

**Benefits**:
- **Reduced Latency**: Total time ≈ max(T1, T2) instead of T1 + T2
- **Better Resource Utilization**: CPU and network I/O used simultaneously
- **Enhanced Context**: Vision description can inform QA generation if available early

### RAG Implementation Details

#### Database & Sources

- **Database**: ChromaDB (chunks in JSON format)
- **Data Sources**:
  - Official ITRI webpage
  - Wikipedia pages (Industrial Technology Research Institute)
  - Virtual Showroom

#### Embedding & Search Strategy

- **Model**: Ollama embedding model `bge-m3:latest` (chosen for better Mandarin support)
- **Search Method**: Hybrid search with ratio `dense:sparse = 7:3`
- **Optimization**: Query rewriter transforms follow-up queries into complete questions

#### Hybrid Search Algorithm

**1. Dense Search (ChromaDB)**:
```python
# Generate query embedding
query_embedding = requests.post("http://localhost:11435/api/embeddings", json={
    "model": "bge-m3:latest",
    "prompt": f"search_query: {query}"
}).json()['embedding']

# Search in ChromaDB
dense_results = chroma_collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k
)
```

**2. Sparse Search (TF-IDF)**:
```python
# Build TF-IDF index
vectorizer = TfidfVectorizer(
    max_features=1000,
    ngram_range=(1, 2),
    min_df=1,
    max_df=0.95
)
tfidf_matrix = vectorizer.fit_transform([chunk.content for chunk in chunks])

# Search with TF-IDF
query_vector = vectorizer.transform([query])
similarities = cosine_similarity(query_vector, tfidf_matrix)
```

**3. Result Fusion**:
```python
# Weighted combination: 70% dense + 30% sparse
combined_score = 0.7 * dense_score + 0.3 * sparse_score

# Rerank by combined score
sorted_results = sorted(results, key=lambda x: x['combined_score'], reverse=True)
```

### QA Response Generation

#### Model Specification

- **Model**: Ollama `linly-llama3.1:70b-instruct-q4_0`
- **Temperature**: Contextual (0.1 for analysis, 0.3 for tone conversion, 0.7 for QA)
- **Streaming**: Supported for real-time responses

#### Input/Output Format

**Input**:
- User input
- Rewritten input (for better retrieval)
- Chat history
- Database query results (RAG reference)
- User description (visual context)

**Output**: Factual response containing correct data

**Prompt Engineering**:
- Role-playing: "工業技術研究院 (ITRI, 工研院) 的權威知識系統"
- Target specification: Extract accurate information from `rag_reference`
- Limitations: 50-100 characters, single focus point
- Output format: only output response, no additional content
- Reasoning guidance: Use `rewritten_query` to understand user intent
- Few-shot examples: Concrete examples showing desired output format

**File Location**: `API/tone_system_prompts_no_tag.py`

### Tone Conversion System

#### Tone Selection

**Key Deciders**: User age and style (derived from User Description)

**Selection Rules**:
- **Age 0-17**: `child_friendly`
- **Age 55+**: `elder_friendly`
- **Business/formal context**: `professional_friendly`
- **General adults/unclear**: `casual_friendly` (default)

**Supported Tones**:
- **Elder**: Warm, storytelling-based, respectful
- **Kid**: Energetic, curious, vivid metaphors, interactive phrases
- **Adult-Professional**: Professional, authoritative, formal vocabulary
- **Adult-Casual**: Chill, conversational, like talking to a friend

#### Tone Converter

**Function**: Converts factual response into human-like, customized response with emotion control based on meta-prompt.

**Features**:
- **First Message Behavior**: Mandatory appearance reference for first messages
- **Subsequent Messages**: 20% probability to reference appearance (configurable via `PERCENTAGE`)
- **Context Integration**: Includes user appearance and original message
- **Language Detection**: Automatic Chinese/English detection
- **Streaming Support**: Real-time tone conversion streaming

**Audio Generation**:
- **FishAudio**: Used for responses requiring audio tags (TTS)
- **Voice Cloning**: Used for responses with no tags

#### Prompt Engineering Example

**Example: Ecological Tree (Specific Technology)**

- **User Input**: "Can you explain it more clearly?" (Referring to the Ecological Tree)
- **Fact (RAG)**: "The trunk uses 6 fans to circulate air 7.7 times per hour, lowering room temperature."
- **Cultural Output (Storytelling)**: "You are right, there is actually deep emotion and science behind this big tree. Speaking of how this tree works, imagine 6 very quiet fans hidden at the top... they circulate the indoor air nearly 8 times an hour... making the air as fresh as a forest."

---

## API Reference

### Core Endpoints

#### `POST /api/rag-llm/query`

Main query endpoint with optional tone conversion.

**Request Body**:
```json
{
  "text_user_msg": "Your question here",
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

#### `POST /api/rag-llm/query-with-tone`

Query with automatic dynamic tone conversion.

**Request Body**:
```json
{
  "text_user_msg": "Your question",
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

#### `POST /api/rag-llm/convert-tone`

Standalone tone conversion service.

**Request Body**:
```json
{
  "text": "Text to convert",
  "tone": "child_friendly",
  "stream": true,
  "user_description": "visual description",
  "user_msg": "original user message"
}
```

**Response** (streaming): Text chunks followed by `END_FLAG`

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

#### `POST /api/rag-llm/init`

Initialize the RAG system (loads ChromaDB, builds indices).

**Response**:
```json
{
  "success": true,
  "rag_initialized": true,
  "message": "RAG system initialized successfully"
}
```

#### `POST /api/rag-llm/warmup`

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

#### `POST /api/rag-llm/close`

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

#### `GET /api/rag-llm/sessions/{session_id}/history`

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

#### `DELETE /api/rag-llm/sessions/{session_id}/history`

Clear conversation history for a session.

#### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1234567890.123
}
```

---

## Configuration Guide

### Configuration File (`config.py`)

**Location**: `./config.py` (project root directory)

**Configuration Variables**:

```python
# LLM Model Configuration
# This model is used for:
# - QA generation (main responses)
# - Tone conversion (adapting response style)
# - Query rewriting (improving retrieval)
# - Tone selection (determining appropriate tone)
LLM_MODEL_NAME = "linly-llama3.1:70b-instruct-q4_0"

# ChromaDB Path Configuration
# Base directory where ChromaDB stores its persistent data
# The actual collection is created at: {CHROMA_DB_PATH}/chroma_db_golden
# This path is used by both create_showroom_db.py and RAG_LLM_realtime.py
CHROMA_DB_PATH = "/mnt/HDD4/thanglq/he110/Demo_GitSpace/chroma_db_golden"
```

**Import Usage**:
- `API/rag_llm_api.py`: `from config import LLM_MODEL_NAME, CHROMA_DB_PATH`
- `LLM_Chat/RAG_LLM_realtime.py`: `from config import LLM_MODEL_NAME, CHROMA_DB_PATH`
- `LLM_Chat/create_showroom_db.py`: Uses `CHROMA_DB_PATH` for database creation

**Configuration Guidelines**:
- Use absolute paths for production deployments
- Ensure `CHROMA_DB_PATH` matches where `create_showroom_db.py` created the database
- Changes to `config.py` require restarting the API server
- Model selection affects both performance and resource requirements

**Model Selection**:
- **Default**: `linly-llama3.1:70b-instruct-q4_0` (70B parameters)
  - Requires: 40GB+ GPU memory, high-end GPU
  - Provides: Best quality responses
- **Alternative**: `linly-llama3.1:8b-instruct-q4_0` (8B parameters)
  - Requires: 8GB+ GPU memory, mid-range GPU
  - Provides: Good quality with faster inference

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

**`model_warmup_server.py`**:
```bash
python model_warmup_server.py \
  --api-url http://localhost:5002 \
  --interval 60 \               # Warmup interval in minutes
  --test                         # Run single test and exit
```

---

## Deployment Guide

### Prerequisites

- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.8 or higher
- **CUDA**: Compatible GPU with CUDA support (optional but recommended for LLM)
- **Memory**: Minimum 16GB RAM (32GB+ recommended for 70B model)
- **Storage**: At least 50GB free space for models and data

### Step-by-Step Setup

#### Step 1: Clone Repository

```bash
git clone git@github.com:HelloHe110/Demo_llm_agent.git
cd Demo_llm_agent
```

Or using HTTPS:
```bash
git clone https://github.com/HelloHe110/Demo_llm_agent.git
cd Demo_llm_agent
```

#### Step 2: Set Up Python Environment

**Option A: Virtual Environment (venv) - Recommended**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install flask flask-cors requests chromadb numpy scikit-learn jieba gradio
```

**Option B: Conda**

```bash
# Create conda environment
conda create -n rag_llm python=3.8 -y

# Activate conda environment
conda activate rag_llm

# Install required packages
pip install flask flask-cors requests chromadb numpy scikit-learn jieba gradio
```

**Required Python Packages**:
- `flask`: Web framework for API server
- `flask-cors`: Cross-origin resource sharing support
- `requests`: HTTP library for API calls
- `chromadb`: Vector database for document storage
- `numpy`: Numerical computing
- `scikit-learn`: Machine learning utilities (TF-IDF)
- `jieba`: Chinese text segmentation
- `gradio`: Optional web UI for RAG pipeline

#### Step 3: Set Up Ollama Server

**3.1 Install Ollama**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**3.2 Start Ollama Server**

```bash
# With GPU support (recommended)
CUDA_VISIBLE_DEVICES=0,1,2,3 \
OLLAMA_HOST=127.0.0.1:11435 \
OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
OLLAMA_SCHED_SPREAD=1 \
OLLAMA_FLASH_ATTENTION=1 \
OLLAMA_KEEP_ALIVE=60m \
ollama serve
```

**3.3 Download Required Models**

Open a new terminal (keep Ollama running):

```bash
# Main language model for QA generation
ollama pull linly-llama3.1:70b-instruct-q4_0

# Embedding model for vector search
ollama pull bge-m3:latest
```

**Note**: The 70B model requires significant GPU memory. If you have limited resources, you can use a smaller model by updating `config.py`:
```python
LLM_MODEL_NAME = "linly-llama3.1:8b-instruct-q4_0"  # Smaller alternative
```

#### Step 4: Prepare Document Data

Organize your ITRI documents in JSON format. The script supports multiple data formats:

<details>
<summary><strong>QA Pairs Format</strong></summary>

```json
[
  {
    "question": "工研院是什麼？",
    "answer": "工研院是台灣最大的產業技術研發機構..."
  }
]
```

</details>

<details>
<summary><strong>Glossary Format</strong></summary>

```json
[
  {
    "term": "ITRI",
    "full_name": "Industrial Technology Research Institute",
    "content": "工研院成立於1973年..."
  }
]
```

</details>

<details>
<summary><strong>News Format</strong></summary>

```json
[
  {
    "date": "2025-01-01",
    "title": "工研院新技術突破",
    "content": "工研院今日宣布..."
  }
]
```

</details>

<details>
<summary><strong>General Format</strong></summary>

```json
[
  {
    "title": "工研院簡介",
    "content": "工研院成立於1973年..."
  }
]
```

</details>

Place your JSON files in:
```
LLM_Chat/
└── database_wiki_gemini整理_一定對的.../
    ├── qa_pairs.json
    ├── glossary.json
    ├── news.json
    └── ...
```

**Important**: Each JSON file should contain a **list of objects**. The script processes each item as a single chunk (One Item = One Chunk strategy).

#### Step 5: Build the Vector Database

**5.1 Create ChromaDB Database**

Use the dedicated script to build the vector database:

```bash
cd LLM_Chat
python create_showroom_db.py --golden --reload --embedding-model bge-m3:latest
```

**With Custom Options**:
```bash
python create_showroom_db.py \
  --data-folder "database_wiki_gemini整理_一定對的..." \
  --collection-name "chroma_db_golden" \
  --embedding-model "bge-m3:latest" \
  --golden \
  --reload
```

**What This Script Does**:
- Loads JSON files from `database_wiki_gemini整理_一定對的.../` folder
- Processes each JSON item as a single chunk (One Item = One Chunk strategy)
- Generates embeddings using `bge-m3:latest` via Ollama API
- Stores in ChromaDB collection named `chroma_db_golden`
- Creates ChromaDB at path: `{CHROMA_DB_PATH}/chroma_db_golden`

**5.2 Verify Database**

Check that ChromaDB was created:
```bash
# Check ChromaDB directory
ls -la chroma_db_golden/

# Or verify collection exists (using Python)
python -c "import chromadb; client = chromadb.PersistentClient(path='chroma_db_golden'); print(client.list_collections())"
```

#### Step 6: Configure the System

Update `config.py` to configure the system:

```python
# LLM Model Configuration
LLM_MODEL_NAME = "linly-llama3.1:70b-instruct-q4_0"

# ChromaDB Path Configuration
CHROMA_DB_PATH = "/mnt/HDD4/thanglq/he110/Demo_GitSpace/chroma_db_golden"
# Or use relative path:
# CHROMA_DB_PATH = "./chroma_db_golden"
```

**Important**: Make sure this path matches where `create_showroom_db.py` created the database.

#### Step 7: Start the RAG LLM API Server

**Important**: Make sure Ollama server is running (from Step 3) before starting the API server.

**7.1 Basic Startup**

```bash
cd API
python3 rag_llm_api.py --auto-init
```

**7.2 With Vision Integration**

**Development (Random Descriptions)**:
```bash
# First, start the random description server (in a separate terminal)
python3 random_user_description_server.py --port 5003

# Then start the API server with vision integration
python3 rag_llm_api.py --auto-init --user-description-server http://localhost:5003
```

**Production (Real VLM)**:
```bash
# Start Vision Context API first (in a separate terminal)
# python vision_api_multi_session.py  # Port 5004

# Then start the API server
python3 rag_llm_api.py --auto-init --user-description-server http://localhost:5004
```

**7.3 Custom Host/Port**

```bash
python3 rag_llm_api.py --host 0.0.0.0 --port 5002 --auto-init --debug
```

#### Step 8: Start Model Warmup Server (Optional but Recommended)

The model warmup server keeps models preloaded to reduce latency. Start it in a separate terminal:

```bash
cd API
python3 model_warmup_server.py --api-url http://localhost:5002 --interval 60
```

**What This Does**:
- Periodically warms up both embedding model and LLM every 60 minutes (configurable)
- Monitors API service health
- Tracks warmup statistics
- Reduces first-request latency significantly

#### Step 9: Verify Installation

**9.1 Health Check**

```bash
curl http://localhost:5002/health
```

Expected response:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1234567890.123
}
```

**9.2 Warm Up Models (If Not Using Warmup Server)**

```bash
curl -X POST http://localhost:5002/api/rag-llm/warmup
```

**9.3 Test Query**

**English Query**:
```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "What is ITRI?",
    "session_id": "test_session",
    "convert_tone": false
  }' \
  --no-buffer
```

**Traditional Chinese Query**:
```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "test_session",
    "convert_tone": false
  }' \
  --no-buffer
```

**With Tone Conversion**:
```bash
curl -X POST http://localhost:5002/api/rag-llm/query-with-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "test_session",
    "user_description": "a young boy wearing glasses",
    "convert_tone": true
  }' \
  --no-buffer
```

#### Step 10: Test with Client Script

The project includes a comprehensive test client script. Run it to verify the complete system:

```bash
cd API
python3 test_rag_llm_api.py --usr_msg "工研院是什麼？" --session_id "test_session"
```

**Test Client Options**:
```bash
python3 test_rag_llm_api.py \
  --usr_msg "Your question here" \
  --session_id "your_session_id" \
  --user_description "a young boy wearing glasses" \
  --convert_tone \
  --base_url http://localhost:5002
```

**Other Example Clients**:

Basic API client example:
```bash
python3 api_client_example.py
```

Tone conversion example:
```bash
python3 api_client_tone_example.py
```

### Recommended Startup Sequence

1. **Clone Repository**
2. **Set Up Python Environment** (venv or conda)
3. **Configure System** (`config.py`)
4. **Start Ollama Server**
5. **Download Models**
6. **Build ChromaDB** (if not already built)
7. **Start Vision Context API** (optional, if using VLM)
8. **Start RAG LLM API Server**
9. **Start Model Warmup Server** (optional but recommended)
10. **Test the System**

---

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

---

## Troubleshooting

### Issue: Ollama Server Not Responding

**Symptoms**: Connection errors when calling LLM API

**Solutions**:
```bash
# Check if Ollama is running
curl http://localhost:11435/api/tags

# Restart Ollama
pkill ollama
ollama serve

# Verify models are downloaded
ollama list
```

### Issue: ChromaDB Not Found

**Symptoms**: "No ChromaDB found" or collection errors

**Solutions**:
```bash
# Check ChromaDB path in config.py
cat config.py | grep CHROMA_DB_PATH

# Verify directory exists
ls -la $(python -c "from config import CHROMA_DB_PATH; print(CHROMA_DB_PATH)")

# Rebuild database using create_showroom_db.py
cd LLM_Chat
python create_showroom_db.py --reload

# Verify collection exists
python -c "import chromadb; client = chromadb.PersistentClient(path='chroma_db_golden'); print([c.name for c in client.list_collections()])"
```

### Issue: Embedding Dimension Mismatch

**Symptoms**: "expecting embedding with dimension X" errors

**Solutions**:
- Rebuild ChromaDB with current embedding model
- Ensure using same embedding model (`bge-m3:latest`) for both building and querying

### Issue: Chinese Text Processing Errors

**Symptoms**: Jieba tokenization failures

**Solutions**:
```bash
# Reinstall Jieba
pip uninstall jieba
pip install jieba

# Clear cache
rm -rf ~/.jieba_cache/
```

### Issue: Vision API Connection Failed

**Symptoms**: "Could not connect to Vision Context API"

**Solutions**:
- Check if Vision API server is running: `curl http://localhost:5004/sessions`
- Use random description server for testing: `--user-description-server http://localhost:5003`
- System will fallback to `casual_friendly` tone if Vision API unavailable

### Issue: Slow First Request

**Solutions**:
```bash
# Warm up models before first real request
curl -X POST http://localhost:5002/api/rag-llm/warmup

# Or use model warmup server
python model_warmup_server.py --api-url http://localhost:5002
```

### Issue: Port Already in Use

**Solutions**:
```bash
# Find process using port
lsof -i :5002

# Kill process or use different port
python3 rag_llm_api.py --port 5003
```

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

---

## Performance Optimization

### Parallel Processing

**Impact**: Reduces total response time by executing independent operations simultaneously

**Implementation**: `ThreadPoolExecutor` for user description fetching and QA generation

**Before (Sequential)**:
```
Total Time = T_fetch_description + T_qa_generation + T_tone_conversion
           ≈ 2s + 5s + 3s = 10s
```

**After (Parallel)**:
```
Total Time = max(T_fetch_description, T_qa_generation) + T_tone_conversion
           ≈ max(2s, 5s) + 3s = 8s
```

**Savings**: ~20% reduction in total latency

### Streaming Responses

**Benefits**: 
- Immediate user feedback (perceived latency reduction)
- Better user experience for long responses
- Progressive rendering in client applications

**Implementation**: 
- Yields chunks as they arrive from LLM
- Sends `END_FLAG` when complete
- Client can process chunks incrementally

### Model Warmup

**Purpose**: Preload models into memory to eliminate cold start delays

**Components**: 
- Embedding model warmup: Test ChromaDB query
- LLM warmup: Minimal test request

**Impact**: 
- First request latency: ~10-15s → ~2-3s
- Subsequent requests: No change

### Session Caching

**Implementation**: In-memory chat history storage with configurable retention

**Benefits**: 
- Context-aware responses without database overhead
- Fast history retrieval
- Automatic cleanup on session close

**Limitations**: 
- Not persistent across server restarts
- Memory usage scales with active sessions

### Query Rewriting

**Purpose**: Improve document retrieval accuracy, especially for follow-up questions

**Impact**: 
- Better context retrieval for ambiguous queries
- Improved handling of pronouns and references
- Enhanced follow-up question understanding

### Batch Processing

**create_showroom_db.py** processes embeddings in batches of 10:
```python
batch_size = 10
for i in range(0, total_docs, batch_size):
    batch = documents[i : i + batch_size]
    # Process batch...
```

**RAG_LLM_realtime.py** uses batch size of 5000 for ChromaDB storage:
```python
BATCH_SIZE = 5000
for i in range(0, len(documents), BATCH_SIZE):
    chroma_collection.add(...)
```

---

## Future Enhancements

### Current Issues & Future Work

#### LLM Reasoning Dilemma

**Ollama Server**: 
- Capable of running better reasoning modules (no additional output problems)
- Suffers from **slow start**

**vLLM**: 
- Offers faster response times for real-time features
- Requires smaller models due to hardware constraints

#### Auto-Prompt Methodology

**Current State**: 
- Uses "quick select" function (hardcoded if/else logic based on user description)
- Example: `If (elder) return elder_tone...`

**Future Goal**: 
- Switch to dynamic auto-prompt method to support wider variety of users
- **Challenge**: May introduce latency during construction of tone-converting meta-prompt

### Scalability Improvements

- **Persistent Session Storage**: Database-backed session management (Redis/PostgreSQL)
- **Load Balancing**: Multi-instance deployment support
- **Caching Layer**: Redis integration for performance optimization
- **Async Processing**: AsyncIO for better concurrency

### Feature Extensions

- **Multi-modal Input**: Image and voice input processing
- **Advanced Analytics**: User interaction tracking and analytics
- **A/B Testing**: Dynamic tone selection algorithm improvement
- **Custom Tone Profiles**: User-defined tone preferences
- **Response Caching**: Cache common queries for faster responses

### Security Enhancements

- **Authentication**: JWT-based user authentication
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Enhanced security for user inputs
- **HTTPS Support**: Encrypted communication
- **API Key Management**: Secure API access control

---

## Conclusion

The ITRI Museum RAG + LLM System represents a sophisticated integration of multiple AI technologies, providing a comprehensive solution for intelligent, context-aware, and tone-adaptive question-answering. Its parallel processing architecture, dynamic tone selection capabilities, and robust error handling make it suitable for production deployment in various interactive AI applications.

### Key Strengths

- Parallel processing reduces latency
- Dynamic tone adaptation based on user demographics
- Robust error handling and graceful degradation
- Streaming responses for better UX
- Comprehensive session management
- Multi-language support (English/繁體中文)

### Architecture Highlights

- Modular design allows for easy extension and customization
- Comprehensive API surface provides flexibility for different client implementations
- Combination of RAG for accuracy, LLM for generation quality, and VLM for personalization creates a powerful AI service platform

The system's design philosophy emphasizes **performance**, **reliability**, and **user experience**, making it an ideal foundation for building production-grade AI applications.

---

## Additional Resources

- [Main README](README.md) - Complete system documentation
- [RAG Pipeline Documentation](LLM_Chat/README.md) - Core RAG pipeline details
- [API Server Methodology](RAG_LLM_Server_Methodology.md) - Technical deep dive
- [API Module Documentation](API/README.md) - API server details
- [Project Summary Report](proj_summary_report.pdf) - Project progress and status

---

## License

This project is developed for educational and research purposes at the Industrial Technology Research Institute (ITRI).

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-06  
**Maintained By**: ITRI Development Team

