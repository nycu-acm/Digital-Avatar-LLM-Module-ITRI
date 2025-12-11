# RAG_LLM_realtime.py Module Documentation

## Overview

The `RAG_LLM_realtime.py` module provides the core Retrieval-Augmented Generation (RAG) pipeline for the ITRI Museum system. It implements an advanced hybrid search system combining dense vector embeddings with sparse TF-IDF retrieval, optimized for both English and Traditional Chinese content.

## Core Components

### ImprovedRAGPipeline Class

The main class that orchestrates the entire RAG workflow, from document processing to response generation.

#### Key Features

- **Multilingual Support**: Native support for Traditional Chinese (繁體中文) with Jieba tokenization
- **Hybrid Retrieval**: Combines ChromaDB dense embeddings with TF-IDF sparse retrieval
- **Semantic Chunking**: Intelligent document chunking that respects sentence boundaries
- **JSON Data Processing**: Specialized handlers for different JSON data formats
- **Real-time TTS**: Integrated Text-to-Speech with streaming audio playback
- **Gradio UI**: Optional web interface with live TTS playback

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Document       │────│  Chunk           │────│  Vector Store   │
│  Loading        │    │  Processing      │    │  (ChromaDB)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  JSON Parsing   │    │  TF-IDF Index    │    │  Hybrid Search  │
│  (Multiple      │    │  (Sparse)        │    │  Reranking      │
│   Formats)      │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation & Dependencies

### Required Python Packages

```bash
pip install chromadb numpy scikit-learn jieba requests flask gradio
```

### Optional Dependencies

For TTS functionality:
```bash
pip install edge-tts mutagen
```

For audio playback (system-level):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg mpv mpg123

# macOS
brew install ffplay mpv mpg123
```

## Usage

### Basic Usage

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
results = rag_pipeline.hybrid_search("工研院是什麼？", chroma_collection, top_k=10)
print(f"Found {len(results)} relevant chunks")
```

### Command Line Usage

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

## Data Processing

### Supported Document Formats

#### JSON Data Files
The pipeline supports multiple JSON formats with specialized processors:

- **raw_data.json**: Basic organizational information and sections
- **qa_pairs.json**: Question-answer pairs for training data
- **structured_data.json**: Hierarchically organized information
- **Generic JSON**: Automatic text extraction from any JSON structure

#### Text Files
- **UTF-8 encoded .txt files**: Processed with semantic chunking

### Data Directory Structure

```
itri_museum_docs/
├── raw_data.json
├── qa_pairs.json  
├── structured_data.json
├── subdirectory/
│   ├── more_data.json
│   └── document.txt
└── text_files/
    ├── intro.txt
    └── history.txt
```

## Chunking Strategy

### Semantic Chunking Parameters

- **Chunk Size**: 300 characters (configurable)
- **Chunk Overlap**: 50 characters (configurable)  
- **Sentence Boundary Respect**: Splits on `。！？.!?` for both languages
- **Language Detection**: Automatic Chinese/English detection per chunk

### Example Chunking

```python
# Configure chunking parameters
rag_pipeline.chunk_size = 500
rag_pipeline.chunk_overlap = 100

# Process with custom chunking
chunks = rag_pipeline.semantic_chunking(
    text="長文本內容...", 
    source_file="document.txt"
)
```

## Vector Store Configuration

### ChromaDB Setup

```python
# Persistent storage location
chroma_db_path = "/mnt/HDD4/thanglq/he110/LLM_Chat/itri_museum_docs/chroma_db"

# Build with custom embedding model
chroma_collection, embedding_model = rag_pipeline.build_hybrid_vector_store(
    chunks,
    collection_name="custom_collection", 
    embedding_model="nomic-embed-text",
    reload=True  # Force rebuild
)
```

### TF-IDF Configuration

```python
# Customize TF-IDF parameters
rag_pipeline._build_tfidf_index(chunks)
# Uses: max_features=1000, ngram_range=(1,2), min_df=1, max_df=0.95
```

## Search & Retrieval

### Hybrid Search Algorithm

1. **Dense Search**: ChromaDB similarity search with embeddings
2. **Sparse Search**: TF-IDF cosine similarity  
3. **Result Combination**: Weighted fusion (70% dense, 30% sparse)
4. **Reranking**: Combined score sorting

### Search Example

```python
query = "工研院的研究領域有哪些？"
results = rag_pipeline.hybrid_search(query, chroma_collection, top_k=10)

for result in results:
    print(f"Score: {result['combined_score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Metadata: {result['metadata']}")
    print("-" * 50)
```

## LLM Integration

### Message Building

The pipeline uses a structured JSON message format:

```python
system_prompt = rag_pipeline._build_fixed_system_prompt(
    response_restriction="You must answer in 1 sentence only."
)

messages = rag_pipeline._build_messages(
    system_prompt=system_prompt,
    user_question="工研院是什麼？",
    history=chat_history,
    rag_reference=context
)
```

### JSON User Payload Format

```json
{
    "user_question": "工研院是什麼？",
    "chat_history": [
        {"id": "Q1", "role": "user", "content": "Previous question"},
        {"id": "A1", "role": "assistant", "content": "Previous answer"}
    ],
    "rag_reference": "Retrieved context from documents..."
}
```

## Text-to-Speech (TTS) Integration (disable right now)

### EdgeTTS Integration

```python
# Initialize TTS (requires edge_tts_helper module)
from edge_tts_helper import EdgeTTSClient

tts_client = EdgeTTSClient(voice="en-US-BrianMultilingualNeural")

# Synthesize text to audio file
audio_path = tts_client.synth_to_file(
    text="工研院是台灣最重要的研究機構", 
    rate=0, 
    volume=85, 
    pitch_hz=0, 
    file_basename="response_001"
)
```

### Streaming TTS

The module supports sentence-by-sentence TTS synthesis during LLM response streaming:

- **Sentence Detection**: Real-time splitting on punctuation
- **Queue Management**: Audio files queued for sequential playback
- **Auto-playback**: Automatic audio player invocation (ffplay/mpv/mpg123)

## Gradio Web Interface

### Features

- **Real-time Streaming**: Live text and audio streaming
- **Session Management**: Conversation history maintenance
- **Auto-play Audio**: Sentence-by-sentence TTS playback
- **Multi-language**: Support for Chinese and English queries

### Launch Gradio UI

```bash
python RAG_LLM_realtime.py --gradio
```

Access at: `http://localhost:7860`

## Performance Optimization

### Model Warm-up

```python
# Pre-load models to reduce first-query latency
rag_pipeline._initialize_jieba()  # Pre-load Chinese tokenizer

# Warm-up LLM with test query
warmup_messages = [{"role": "user", "content": "Test"}]
# Send to Ollama API...
```

### Batch Processing

```python
# Process documents in batches for large datasets
BATCH_SIZE = 5000
for i in range(0, len(documents), BATCH_SIZE):
    batch_docs = documents[i:i + BATCH_SIZE]
    chroma_collection.add(
        documents=batch_docs,
        embeddings=embeddings[i:i + BATCH_SIZE],
        metadatas=metadatas[i:i + BATCH_SIZE],
        ids=ids[i:i + BATCH_SIZE]
    )
```

## Configuration

### Environment Variables

- `CUDA_VISIBLE_DEVICES`: GPU devices for Ollama
- `OLLAMA_HOST`: Ollama server endpoint (default: `127.0.0.1:11435`)

### Pipeline Configuration

```python
# Customize pipeline parameters
rag_pipeline = ImprovedRAGPipeline(museum_name='custom_museum')
rag_pipeline.chunk_size = 400
rag_pipeline.chunk_overlap = 80
```

## API Requirements

### Ollama Service

The module requires a running Ollama instance with these endpoints:

- **Embeddings**: `POST http://localhost:11435/api/embeddings`
- **Chat**: `POST http://localhost:11435/api/chat`  
- **Generate**: `POST http://localhost:11435/api/generate`

### Required Models

```bash
# Install required models
ollama pull nomic-embed-text          # For embeddings
ollama pull linly-llama3.1:70b-instruct-q4_0  # For generation
```

## Error Handling

### Common Issues

**ChromaDB Connection Errors**:
```python
# Check database path permissions
os.makedirs(chroma_db_path, exist_ok=True)
os.chmod(chroma_db_path, 0o755)
```

**Embedding Dimension Mismatches**:
```python
# Clear and rebuild vector store
rag_pipeline.build_hybrid_vector_store(chunks, reload=True)
```

**Chinese Text Processing**:
```python
# Ensure Jieba is properly initialized
rag_pipeline._initialize_jieba()
```

## Testing

### Test Queries

The module includes predefined test queries:

```python
test_queries = [
    "工研院有哪些重要成就？",
    "工研院的組織架構如何？", 
    "工研院的院長是誰？",
    "工研院如何推動產業升級？"
]
```

### Performance Metrics

The system logs timing metrics:
- First LLM token latency
- First TTS audio latency  
- End-to-end response time

## Advanced Usage

### Custom Document Processors

```python
def custom_json_processor(data: Dict, file_name: str) -> List[DocumentChunk]:
    """Custom processor for specialized JSON formats"""
    chunks = []
    # Process custom format...
    return chunks

# Register custom processor
rag_pipeline._process_custom_json = custom_json_processor
```

### Custom Reranking

```python
def custom_rerank(dense_results, sparse_results, top_k):
    """Custom result fusion algorithm"""
    # Implement custom scoring...
    return sorted_results

# Override reranking method
rag_pipeline._combine_and_rerank = custom_rerank
```

## Troubleshooting

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Fixes

1. **Vector Store Corruption**: Delete `chroma_db` directory and rebuild
2. **Model Loading Issues**: Verify Ollama service is running
3. **Memory Issues**: Reduce batch size and chunk count
4. **Audio Playback**: Install system audio players (ffplay/mpv/mpg123)

## License

This module is part of the ITRI Museum RAG system, developed for educational and research purposes.
