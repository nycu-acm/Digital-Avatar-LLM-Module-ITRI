# LLM_Chat Module Documentation

## 📋 Overview

The `LLM_Chat` folder contains the **core RAG (Retrieval-Augmented Generation) pipeline** and **database creation tools** for the ITRI Museum system. This module provides two distinct approaches for building and querying knowledge bases:

1. **General RAG Pipeline** (`RAG_LLM_realtime.py`): Semantic chunking with hybrid search for general documents
2. **Structured Database Builder** (`create_showroom_db.py`): One-item-per-chunk strategy for structured JSON data (QA pairs, glossary, news)

Both approaches integrate with the main API server (`API/rag_llm_api.py`) to provide intelligent question-answering capabilities.

---

## 🏗️ Folder Structure

```
LLM_Chat/
├── RAG_LLM_realtime.py              # Core RAG pipeline (semantic chunking)
├── create_showroom_db.py             # Structured database builder (One Item = One Chunk)
├── RAG_LLM_realtime_all_age.py      # Variant with age-specific handling
├── RAG_LLM_realtime_try.py          # Experimental/test version
├── database_wiki_gemini整理_一定對的.../  # Structured JSON data source
│   ├── 工研院Gold_QA.json
│   ├── 工研院glossary.json
│   ├── 最新新聞資訊.json
│   └── ...
├── crawl_ref_and_past_data/          # Historical crawlers and past data
└── database_prompt/                  # Database-related prompts
```

---

## 🔑 Key Components

### 1. ImprovedRAGPipeline (`RAG_LLM_realtime.py`)

**Purpose**: Core RAG pipeline for general document processing with semantic chunking.

**Key Features**:
- **Hybrid Search**: Combines ChromaDB dense embeddings (70%) with TF-IDF sparse retrieval (30%)
- **Semantic Chunking**: Intelligent text splitting (300 chars, 50 overlap) respecting sentence boundaries
- **Multi-format Support**: Handles JSON (raw_data, qa_pairs, structured_data) and TXT files
- **Multilingual**: Native support for Traditional Chinese with Jieba tokenization
- **Gradio UI**: Optional web interface with real-time TTS playback

**Use Case**: General document processing where semantic chunking is beneficial (long documents, articles, unstructured text).

### 2. create_showroom_db.py

**Purpose**: Creates ChromaDB database from structured JSON data using "One Item = One Chunk" strategy.

**Key Features**:
- **Structured Data Processing**: Optimized for QA pairs, glossary, news, and general items
- **One-to-One Mapping**: Each JSON item becomes a single chunk (preserves document structure)
- **Smart Formatting**: Automatically formats content based on data type (QA, Glossary, News, General)
- **Batch Processing**: Processes embeddings in batches of 10 for efficiency

**Use Case**: Structured data where preserving item boundaries is important (QA pairs, glossary entries, news articles).

**Supported Data Formats**:
- **QA Pairs**: `{"question": "...", "answer": "..."}`
- **Glossary**: `{"term": "...", "full_name": "...", "content": "..."}`
- **News**: `{"date": "...", "title": "...", "content": "..."}`
- **General**: `{"title": "...", "content": "..."}`

---

## 🚀 Quick Start

### Option 1: Using Structured Database Builder (Recommended for QA/Glossary/News)

**Step 1: Prepare Your Data**

Place structured JSON files in `database_wiki_gemini整理_一定對的.../`:

```json
// Example: 工研院Gold_QA.json
[
  {
    "question": "工研院是什麼？",
    "answer": "工研院是台灣最大的產業技術研發機構..."
  }
]
```

**Step 2: Create ChromaDB Database**

```bash
cd LLM_Chat
python create_showroom_db.py --golden --reload --embedding-model bge-m3:latest
```

**Expected Output**:
```
================================================================================
Creating ChromaDB database: chroma_db_golden
================================================================================
📁 ChromaDB path: /path/to/chroma_db_golden
📂 Data folder: database_wiki_gemini整理_一定對的...
📂 Found 12 JSON files in database_wiki_gemini整理_一定對的...
   - Processing 工研院Gold_QA.json (100 items)...
   - Processing 工研院glossary.json (50 items)...
🔄 Reloading vector store...
   - Deleted existing collection.
   - Created new collection.
🧮 Generating embeddings using [bge-m3:latest]...
   Processing batch 1/15 (10 items)
   ...
🎉 Database creation completed! Stored 150 items.
```

**Step 3: Use in API Server**

The API server (`API/rag_llm_api.py`) will automatically load this database when initialized.

### Option 2: Using General RAG Pipeline

**Step 1: Prepare Your Documents**

Place documents in `itri_museum_docs/`:

```
itri_museum_docs/
├── raw_data.json
├── qa_pairs.json
├── structured_data.json
└── text_files/
    └── *.txt
```

**Step 2: Build Vector Store**

```bash
cd LLM_Chat
python RAG_LLM_realtime.py --RAG_RELOAD
```

**Step 3: Test with Gradio UI**

```bash
python RAG_LLM_realtime.py --gradio
```

Access at: `http://localhost:7860`

---

## 📊 Comparison: Two Approaches

| Feature | `create_showroom_db.py` | `RAG_LLM_realtime.py` |
|---------|------------------------|----------------------|
| **Chunking Strategy** | One Item = One Chunk | Semantic Chunking (300 chars, 50 overlap) |
| **Data Source** | `database_wiki_gemini整理_一定對的.../` | `itri_museum_docs/` |
| **Collection Name** | `chroma_db_golden` | `itri_museum_collection` |
| **Best For** | Structured data (QA, Glossary, News) | General documents (articles, long text) |
| **Preserves Structure** | ✅ Yes (item boundaries) | ⚠️ May split items |
| **Search Quality** | High for exact matches | High for semantic similarity |

---

## 🔧 Detailed Usage

### create_showroom_db.py

**Command Line Options**:

```bash
python create_showroom_db.py \
  --data-folder "database_wiki_gemini整理_一定對的..." \
  --collection-name "chroma_db_golden" \
  --embedding-model "bge-m3:latest" \
  --golden \
  --reload
```

**Parameters**:
- `--data-folder`: Source folder containing JSON files (default: `database_wiki_gemini整理_一定對的...`)
- `--collection-name`: ChromaDB collection name (default: `chroma_db_golden`)
- `--embedding-model`: Embedding model to use (default: `bge-m3:latest`)
- `--golden`: Use golden dataset path
- `--reload`: Delete existing collection and rebuild

**Data Processing Flow**:

```python
# 1. Load JSON files
documents = load_itri_json_docs("database_wiki_gemini整理_一定對的...")

# 2. Format each item based on type
for item in data:
    if 'question' in item and 'answer' in item:
        content = f"問題：{item['question']}\n答案：{item['answer']}"
    elif 'term' in item and 'content' in item:
        content = f"術語：{item['term']} ({item['full_name']})\n解釋：{item['content']}"
    # ... more formats

# 3. Generate embeddings
embedding = requests.post("http://localhost:11435/api/embeddings", json={
    "model": "bge-m3:latest",
    "prompt": f"search_document: {content}"
}).json()['embedding']

# 4. Store in ChromaDB
collection.add(
    ids=[f"{file_name}_{index}"],
    documents=[content],
    metadatas=[metadata],
    embeddings=[embedding]
)
```

### RAG_LLM_realtime.py

**Command Line Usage**:

```bash
# Run with existing vector store
python RAG_LLM_realtime.py

# Force rebuild vector store
python RAG_LLM_realtime.py --RAG_RELOAD

# Launch with Gradio web UI
python RAG_LLM_realtime.py --gradio

# Launch with Gradio and force rebuild
python RAG_LLM_realtime.py --RAG_RELOAD --gradio
```

**Python API Usage**:

```python
from RAG_LLM_realtime import ImprovedRAGPipeline

# Initialize pipeline
rag_pipeline = ImprovedRAGPipeline(museum_name='itri_museum')

# Load and process documents
chunks = rag_pipeline.load_and_chunk_docs('itri_museum_docs')

# Build vector store
chroma_collection, embedding_model = rag_pipeline.build_hybrid_vector_store(
    chunks, 
    collection_name="itri_museum_collection",
    reload=False  # Set to True to rebuild from scratch
)

# Perform hybrid search
results = rag_pipeline.hybrid_search(
    "工研院是什麼？", 
    chroma_collection, 
    top_k=10
)

for result in results:
    print(f"Score: {result['combined_score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
```

---

## 🔍 Hybrid Search Algorithm

Both approaches use **hybrid search** combining dense and sparse retrieval:

### 1. Dense Search (ChromaDB)

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

### 2. Sparse Search (TF-IDF)

```python
# Build TF-IDF index (only in RAG_LLM_realtime.py)
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

### 3. Result Fusion

```python
# Weighted combination: 70% dense + 30% sparse
combined_score = 0.7 * dense_score + 0.3 * sparse_score

# Rerank by combined score
sorted_results = sorted(results, key=lambda x: x['combined_score'], reverse=True)
```

---

## 📁 Data Structure

### Structured Data Format (`database_wiki_gemini整理_一定對的.../`)

**QA Pairs** (`工研院Gold_QA.json`):
```json
[
  {
    "question": "工研院是什麼？",
    "answer": "工研院是台灣最大的產業技術研發機構..."
  }
]
```

**Glossary** (`工研院glossary.json`):
```json
[
  {
    "term": "ITRI",
    "full_name": "Industrial Technology Research Institute",
    "content": "工研院成立於1973年..."
  }
]
```

**News** (`最新新聞資訊.json`):
```json
[
  {
    "date": "2025-01-01",
    "title": "工研院新技術突破",
    "content": "工研院今日宣布..."
  }
]
```

### General Document Format (`itri_museum_docs/`)

**Golden JSON Format** (for RAG_LLM_realtime.py):
```json
[
  {
    "content": "工研院成立於1973年，是台灣最大的產業技術研發機構...",
    "title": "工研院簡介",
    "source": "itri_website",
    "hierarchy": "首頁 > 關於工研院"
  }
]
```

---

## ⚙️ Configuration

### Environment Setup

**Required Python Packages**:
```bash
pip install chromadb numpy scikit-learn jieba requests flask gradio
```

**Optional Dependencies** (for TTS):
```bash
pip install edge-tts mutagen
```

**System Dependencies** (for audio playback):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg mpv mpg123

# macOS
brew install ffplay mpv mpg123
```

### Configuration Files

**config.py** (in parent directory):
```python
# LLM Model Configuration
LLM_MODEL_NAME = "linly-llama3.1:70b-instruct-q4_0"

# ChromaDB Path Configuration
CHROMA_DB_PATH = "/path/to/chroma_db_golden"
```

### ChromaDB Paths

- **create_showroom_db.py**: Creates database at `{CHROMA_DB_PATH}/chroma_db_golden`
- **RAG_LLM_realtime.py**: Uses `{CHROMA_DB_PATH}` directly

---

## 🔗 Integration with API Server

The `LLM_Chat` module integrates with the main API server (`API/rag_llm_api.py`):

### Initialization Flow

```python
# In API/rag_llm_api.py
from LLM_Chat.RAG_LLM_realtime import ImprovedRAGPipeline

class RAGLLMAPIService:
    def _initialize_rag_system(self):
        # Initialize RAG pipeline
        self.rag_pipeline = ImprovedRAGPipeline()
        
        # Load ChromaDB collection
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.chroma_collection = chroma_client.get_collection("chroma_db_golden")
        
        # Build TF-IDF index (for hybrid search)
        self.rag_pipeline._build_tfidf_index(chunks)
```

### Query Processing

```python
# In API server
def _generate_streaming_response(self, text_user_msg, session_id, chat_history):
    # 1. Rewrite query (optional)
    rewritten_query = self._rewrite_query(text_user_msg, chat_history)
    
    # 2. Hybrid search using RAG pipeline
    search_results = self.rag_pipeline.hybrid_search(
        rewritten_query, 
        self.chroma_collection, 
        top_k=6
    )
    
    # 3. Process context
    context = self.rag_pipeline._process_context(museum_context, text_user_msg)
    
    # 4. Generate LLM response with context
    # ...
```

---

## 🧪 Testing

### Test create_showroom_db.py

```bash
# Test database creation
python create_showroom_db.py --golden --reload

# Verify collection exists
python -c "import chromadb; client = chromadb.PersistentClient(path='chroma_db_golden'); print([c.name for c in client.list_collections()])"
```

### Test RAG_LLM_realtime.py

```bash
# Run test queries
python RAG_LLM_realtime.py

# Test with Gradio UI
python RAG_LLM_realtime.py --gradio
```

**Predefined Test Queries**:
```python
test_queries = [
    "工研院有哪些重要成就？",
    "工研院的組織架構如何？",
    "工研院的院長是誰？",
    "工研院如何推動產業升級？"
]
```

---

## 🐛 Troubleshooting

### Issue: ChromaDB Collection Not Found

**Symptoms**: `CollectionNotFoundError` when querying

**Solutions**:
```bash
# Rebuild database
python create_showroom_db.py --golden --reload

# Or rebuild RAG pipeline database
python RAG_LLM_realtime.py --RAG_RELOAD
```

### Issue: Embedding Dimension Mismatch

**Symptoms**: `expecting embedding with dimension X` errors

**Solutions**:
- Ensure using same embedding model (`bge-m3:latest`) for both building and querying
- Rebuild database with current embedding model

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

---

## 📈 Performance Optimization

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

### Model Warmup

Preload models to reduce first-request latency:
```python
# Preload Jieba
rag_pipeline._initialize_jieba()

# Warmup LLM
warmup_messages = [{"role": "user", "content": "Test"}]
# Send to Ollama API...
```

---

## 📚 Additional Resources

- [Main README](../README.md) - Complete system documentation
- [API Server Documentation](../API/README_rag_llm_api.md) - API server details
- [RAG Server Methodology](../RAG_LLM_Server_Methodology.md) - Technical deep dive

---

## 🔄 Version Variants

### RAG_LLM_realtime_all_age.py

Variant with age-specific handling for different user demographics. May include specialized prompts or processing for children, elderly, etc.

### RAG_LLM_realtime_try.py

Experimental/test version for trying new features or debugging. Not recommended for production use.

---

## 📝 Notes

- **Two Approaches**: Choose `create_showroom_db.py` for structured data (QA/Glossary/News) or `RAG_LLM_realtime.py` for general documents
- **Collection Names**: `chroma_db_golden` (structured) vs `itri_museum_collection` (general)
- **Chunking Strategy**: One-item-per-chunk (structured) vs semantic chunking (general)
- **Integration**: Both integrate seamlessly with the main API server

---

## 📄 License

This module is part of the ITRI Museum RAG system, developed for educational and research purposes at the Industrial Technology Research Institute (ITRI).
