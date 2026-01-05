# RAG + LLM Server Methodology

## 1. Overview and Purpose

### 1.1 What the Server Does

The RAG + LLM API Server is a comprehensive Flask-based web service that provides intelligent question-answering capabilities by combining **Retrieval Augmented Generation (RAG)** with **Large Language Models (LLM)**. The server serves as a bridge between client applications and advanced AI capabilities, offering context-aware, tone-adapted responses with real-time streaming.

**Core Functionalities:**
- **Intelligent Q&A**: Processes user queries using RAG to retrieve relevant context from a knowledge base, then generates responses using LLM
- **Dynamic Tone Adaptation**: Automatically adjusts response tone based on visual user analysis (child-friendly, elder-friendly, professional, casual)
- **Real-time Streaming**: Provides streaming text responses for immediate user feedback
- **Session Management**: Maintains conversation history across multiple interactions
- **Multi-modal Integration**: Integrates with Vision Language Models for user appearance analysis
- **Multi-language Support**: Handles English and Traditional Chinese (繁體中文) responses
- **Parallel Processing**: Executes user description fetching and QA generation simultaneously to minimize latency

### 1.2 Target Use Cases

- **Museum Interactive Systems**: Providing personalized explanations about exhibits based on visitor demographics
- **Educational Platforms**: Adapting content delivery based on user demographics (children, elderly, professionals)
- **Customer Service Chatbots**: Context-aware responses with appropriate tone
- **Knowledge Management Systems**: Intelligent document retrieval and explanation
- **Multilingual Information Systems**: Cross-language knowledge retrieval with automatic language detection

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Client   │────│   Flask API      │────│  RAG Pipeline   │
│   (Web/Mobile)  │    │   Service        │    │  (ChromaDB)     │
│                 │    │   (Port 5002)    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Session        │    │   Streaming      │    │   Ollama LLM    │
│  Management     │    │   Response       │    │   Service       │
│  (In-Memory)    │    │   Handler        │    │   (Port 11435)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌──────────────────┐
                    │   Vision Context │
                    │   API (VLM)      │
                    │   (Port 5004)    │
                    └──────────────────┘
```

### 2.2 Core Components

#### 2.2.1 RAGLLMAPIService Class

**Location**: `API/rag_llm_api.py`

**Purpose**: Main orchestrator that manages API endpoints, session handling, and service coordination.

**Key Attributes:**
- `rag_pipeline`: `ImprovedRAGPipeline` instance for document retrieval
- `chroma_collection`: ChromaDB collection for vector storage
- `chat_sessions`: In-memory session storage (`dict[session_id: str, chat_history: List[Dict]]`)
- `user_description_server_url`: Vision Context API endpoint URL
- `rag_initialized`: Boolean flag indicating RAG system readiness

**Key Methods:**
- `_initialize_rag_system()`: Loads ChromaDB collection and initializes RAG pipeline
- `_generate_streaming_response()`: Generates QA response using RAG + LLM
- `_generate_streaming_response_with_tone()`: Orchestrates parallel processing and tone conversion
- `_determine_tone_from_user_description()`: Analyzes user description to select appropriate tone
- `_convert_tone()` / `_stream_convert_tone()`: Converts response tone using specialized LLM agent
- `_rewrite_query()`: Rewrites user query for better document retrieval
- `_fetch_user_description_from_server()`: Fetches visual context from Vision API

#### 2.2.2 RAG Pipeline Integration

**Location**: `LLM_Chat/RAG_LLM_realtime.py`

**Purpose**: Retrieves relevant context from the knowledge base using hybrid search.

**Components:**
- **ChromaDB**: Persistent vector database for document embeddings
- **Embedding Model**: `bge-m3:latest` via Ollama API (`/api/embeddings`)
- **Hybrid Search**: Combines semantic (dense) and keyword (sparse TF-IDF) search for optimal retrieval
- **Document Processing**: Multi-format support (JSON, TXT) with semantic chunking

**Key Methods:**
- `load_json_data()`: Loads and processes JSON documents (raw_data, qa_pairs, structured_data, golden entries)
- `semantic_chunking()`: Intelligent text splitting respecting sentence boundaries (300 chars, 50 overlap)
- `build_hybrid_vector_store()`: Creates ChromaDB collection with embeddings
- `hybrid_search()`: Performs combined dense + sparse retrieval with reranking
- `_process_context()`: Filters and ranks retrieved documents (max 2500 chars)
- `_build_messages()`: Constructs structured JSON prompt for LLM

#### 2.2.3 Tone Conversion System

**Location**: `API/tone_system_prompts_no_tag.py`

**Purpose**: Adapts response tone based on user characteristics and context.

**Available Tones:**
- `child_friendly`: For children and teenagers (0-17 years)
  - Role: "科學探險隊隊長" (Science Adventure Team Leader)
  - Style: Energetic, curious, vivid metaphors, interactive phrases
- `elder_friendly`: For elderly users (65+ years)
  - Role: "資深導覽員" (Senior Guide)
  - Style: Warm, storytelling-based, respectful, gentle expressions
- `professional_friendly`: For business/professional contexts
  - Role: "官方專家導覽員" (Official Expert Guide)
  - Style: Professional, authoritative, formal vocabulary
- `casual_friendly`: For general adult users (default)
  - Role: "科技嚮導" (Tech Guide)
  - Style: Chill, conversational, like talking to a friend

**Key Functions:**
- `get_tone_system_prompt(tone, target_lang)`: Retrieves specialized prompt for tone
- `build_tone_selector_system_prompt(target_lang)`: Creates prompt for tone selection agent
- `build_fixed_system_prompt(response_restriction)`: Creates QA agent system prompt
- `build_query_rewriter_prompt(target_lang)`: Creates query rewriting agent prompt

#### 2.2.4 Vision Context Integration

**Purpose**: Fetches visual user descriptions from VLM service for dynamic tone selection.

**Integration Point**: HTTP API call to Vision Context server (default: `http://localhost:5004`)

**Endpoint**: `GET /visual-context/{session_id}`

**Response Format**:
```json
{
  "available": true,
  "visual_context": "a young boy wearing glasses, and is smiling"
}
```

**Fallback Behavior**: If Vision API unavailable, defaults to `casual_friendly` tone

---

## 3. Technical Implementation

### 3.1 Complete Request Processing Workflow

#### Phase 1: Request Reception

```python
# Client sends POST request to /api/rag-llm/query
{
  "text_user_msg": "工研院是什麼？",
  "session_id": "user_123",
  "include_history": true,
  "user_description": "a young boy wearing glasses",  # Optional
  "convert_tone": true
}
```

**Processing Steps**:
1. Parse JSON request body
2. Validate required fields (`text_user_msg`)
3. Retrieve session history (if `include_history=true`)
4. Detect input language (Chinese/English)

#### Phase 2: Parallel Processing (Key Innovation)

The system uses `ThreadPoolExecutor` to execute two independent tasks simultaneously:

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    # Task 1: Fetch user description (with 2-second delay)
    def _delayed_fetch_user_description():
        time.sleep(2)  # Allow VLM to process recent frames
        return self._fetch_user_description_from_server(session_id)
    
    future_description = executor.submit(_delayed_fetch_user_description)
    
    # Task 2: Generate QA response
    def collect_qa_response():
        # Try to get vision description first (wait up to 3 seconds)
        vision_desc = future_description.result(timeout=3) if available else ""
        
        # Generate QA response with vision context
        response_generator = self._generate_streaming_response(
            text_user_msg, session_id, chat_history, 
            user_description=vision_desc
        )
        
        # Collect full response (max 150 chars for tone conversion)
        content = ""
        for chunk in response_generator:
            if chunk == "END_FLAG":
                break
            content += chunk
            if len(content) > MAX_LENGTH:
                content = content[:MAX_LENGTH]
                break
        
        return content, None, vision_desc
    
    future_qa = executor.submit(collect_qa_response)
    
    # Wait for both tasks
    result = future_qa.result(timeout=120)
    response_content, error, fetched_user_description = result
```

**Benefits**:
- **Reduced Latency**: Total time ≈ max(T1, T2) instead of T1 + T2
- **Better Resource Utilization**: CPU and network I/O used simultaneously
- **Enhanced Context**: Vision description can inform QA generation if available early

#### Phase 3: RAG Processing (Within QA Generation)

**Step 1: Query Rewriting**

```python
def _rewrite_query(self, user_question: str, chat_history: List[Dict]) -> str:
    # Build system prompt for query rewriter
    system_prompt = build_query_rewriter_prompt(target_lang)
    
    # Format chat history for context
    history_context = format_chat_history(chat_history[-4:])
    
    # Send to LLM for rewriting
    rewritten_query = llm_call(system_prompt, user_question, history_context)
    
    return rewritten_query or user_question  # Fallback to original
```

**Example Transformations**:
- "他什麼時候上任的？" → "工研院院長張培仁博士的上任日期與就職時間"
- "還有嗎？" → "工研院其他辦事處或園區的地址與聯絡資訊"
- "你好" → "你好，並簡單介紹工研院"

**Step 2: Hybrid Search**

```python
def hybrid_search(self, query: str, chroma_collection, top_k: int = 6):
    # Dense search (ChromaDB)
    query_embedding = generate_embedding(f"search_query: {query}")
    dense_results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Sparse search (TF-IDF)
    query_vector = self.vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, self.tfidf_matrix)
    sparse_results = get_top_k_indices(similarities, top_k)
    
    # Combine and rerank (70% dense + 30% sparse)
    combined_results = combine_and_rerank(
        dense_results, sparse_results, top_k
    )
    
    return combined_results
```

**Step 3: Context Processing**

```python
def _process_context(self, context_chunks: List[str], query: str) -> str:
    processed_chunks = []
    current_length = 0
    MAX_LENGTH = 2500
    
    # Use sorted chunks from hybrid search (most relevant first)
    for chunk in context_chunks:
        if current_length + len(chunk) > MAX_LENGTH:
            if not processed_chunks:
                processed_chunks.append(chunk[:MAX_LENGTH])
            break
        processed_chunks.append(chunk)
        current_length += len(chunk)
    
    return "\n\n".join(processed_chunks)
```

**Step 4: LLM Prompt Construction**

```python
def _build_messages(self, system_prompt, user_question, history, 
                   rag_reference, user_description=None, rewritten_query=None):
    # Structure chat history
    structured_history = []
    for msg in history:
        if msg["role"] == "user":
            structured_history.append({
                "id": f"Q{question_count}",
                "role": "user",
                "content": msg["content"]
            })
        elif msg["role"] == "assistant":
            structured_history.append({
                "id": f"A{question_count}",
                "role": "assistant",
                "content": msg["content"]
            })
    
    # Build JSON payload
    user_payload = {
        "user_question": user_question,
        "chat_history": structured_history,
        "rag_reference": rag_reference or "",
        "language_requirement": f"Respond in {detected_language}"
    }
    
    # Add optional fields
    if user_description:
        user_payload["user_description"] = user_description
    if rewritten_query and rewritten_query != user_question:
        user_payload["rewritten_query"] = rewritten_query
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    ]
    
    return messages
```

**Step 5: LLM Response Generation**

```python
# Stream response from Ollama
request_payload = {
    "model": LLM_MODEL_NAME,
    "messages": messages,
    "stream": True,
    "options": {"temperature": 0.7}
}

response = requests.post("http://localhost:11435/api/chat", 
                        json=request_payload, stream=True)

for line in response.iter_lines(decode_unicode=True):
    chunk = json.loads(line)
    delta = chunk.get("message", {}).get("content")
    if delta:
        yield delta  # Stream to client
    
    if chunk.get("done"):
        yield "END_FLAG"
        break
```

#### Phase 4: Tone Determination

After QA response is collected:

```python
def _determine_tone_from_user_description(self, user_description: str) -> str:
    # Build tone selector system prompt
    system_prompt = build_tone_selector_system_prompt(target_lang)
    
    # Analyze user description
    user_instruction = f"Analyze this user description: {user_description}"
    
    # Call LLM for tone selection
    tone_result = llm_call(system_prompt, user_instruction, temperature=0.1)
    
    # Validate and return
    valid_tones = ["child_friendly", "elder_friendly", 
                   "professional_friendly", "casual_friendly"]
    return tone_result if tone_result in valid_tones else "casual_friendly"
```

**Tone Selection Rules**:
- Age 0-17: `child_friendly`
- Age 55+: `elder_friendly`
- Business/formal context: `professional_friendly`
- General adults/unclear: `casual_friendly` (default)

#### Phase 5: Tone Conversion

```python
def _stream_convert_tone(self, text, tone, user_description="", 
                        user_msg="", is_first_message=False):
    # Get tone-specific system prompt
    system_prompt = get_tone_system_prompt(tone, target_lang)
    
    # Build context information
    context_info = ""
    if user_description:
        context_info += f"\n[使用者外貌描述]: {user_description}"
    if user_msg:
        context_info += f"\n[使用者的原始問題]: {user_msg}"
    
    # First message guidance
    if is_first_message and user_description:
        first_msg_guide = "\n這是我與客人的初次見面，請務必在開場時親切地提到對方的外貌特徵..."
    elif user_description:
        first_msg_guide = f"\n這不是初次見面，請自然地對話。有 {PERCENTAGE}% 的機率可以再次提到對方的外貌..."
    
    # Build user instruction
    user_instruction = f"""
    ### 導覽任務資訊 ###
    目標語言：{target_lang}
    導覽對象：{target_audience}
    {context_info}
    {first_msg_guide}
    
    ### 待轉換的事實內容（Part 1 產出） ###
    ---
    {text}
    ---
    
    ### 輸出規範 ###
    1. 請依照「資深導覽員」的身份，將上述【事實內容】編織成一段溫暖的故事。
    2. 嚴禁使用任何表情符號 (Emoji)。
    3. 僅輸出轉換後的對話文字，不可包含任何備註、解釋、標籤。
    """
    
    # Stream tone conversion
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction}
        ],
        "stream": True,
        "options": {"temperature": 0.5}
    }
    
    response = requests.post("http://localhost:11435/api/chat", 
                            json=payload, stream=True)
    
    for line in response.iter_lines(decode_unicode=True):
        chunk = json.loads(line)
        delta = chunk.get("message", {}).get("content")
        if delta:
            yield delta
        
        if chunk.get("done"):
            yield "END_FLAG"
            break
```

#### Phase 6: Response Delivery & Session Update

```python
# Stream converted response to client
for tone_chunk in self._stream_convert_tone(...):
    if tone_chunk == "END_FLAG":
        # Update session history with ORIGINAL (pre-tone) response
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        
        self.chat_sessions[session_id].append({
            "role": "user", 
            "content": text_user_msg
        })
        self.chat_sessions[session_id].append({
            "role": "assistant", 
            "content": response_content  # Original, not converted
        })
        
        yield "END_FLAG"
        break
    else:
        yield tone_chunk
```

**Important**: Session history stores the **original** (pre-tone-conversion) response to maintain factual context for future queries.

### 3.2 Document Processing Pipeline

#### Database Creation (Separate Script)

**Important**: ChromaDB database is created using a dedicated script `create_showroom_db.py`, not through the RAG pipeline.

**Location**: `LLM_Chat/create_showroom_db.py`

**Purpose**: Creates ChromaDB database from structured JSON files using "One Item = One Chunk" strategy.

**Process**:
```python
def create_showroom_database(
    data_folder: str = "database_wiki_gemini整理_一定對的...",
    collection_name: str = "chroma_db_golden",
    chroma_db_path: str = None,
    embedding_model: str = "bge-m3:latest",
    reload: bool = True
):
    # 1. Load JSON files from data_folder
    documents = load_itri_json_docs(full_data_path)
    
    # 2. Process each JSON item as a single chunk
    for item in data:
        # Smart formatting based on item type:
        # - QA Pair: "問題：{question}\n答案：{answer}"
        # - Glossary: "術語：{term} ({full_name})\n解釋：{content}"
        # - News: "日期：{date}\n標題：{title}\n內容：{content}"
        # - General: "{title}\n{body}"
        content_for_embedding = format_item(item)
        
        # 3. Generate embedding
        embedding = requests.post(
            "http://localhost:11435/api/embeddings",
            json={"model": embedding_model, "prompt": f"search_document: {content_for_embedding}"}
        ).json()['embedding']
        
        # 4. Store in ChromaDB
        collection.add(
            ids=[f"{file_name}_{index}"],
            documents=[content_for_embedding],
            metadatas=[metadata],
            embeddings=[embedding]
        )
```

**Key Differences from RAG Pipeline**:
- **Chunking Strategy**: One JSON item = One chunk (preserves document structure)
- **Data Source**: `database_wiki_gemini整理_一定對的.../` folder (not `itri_museum_docs/`)
- **Collection Name**: `chroma_db_golden` (not `itri_museum_collection`)
- **Purpose**: Optimized for structured QA/Glossary/News data

#### Document Loading (RAG Pipeline)

The RAG pipeline (`RAG_LLM_realtime.py`) loads documents differently for general document processing:

```python
def load_json_data(self, data_dir: str = "itri_museum_docs"):
    all_chunks = []
    
    # Recursively find all JSON files
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                json_file = os.path.join(root, file)
                data = json.load(open(json_file, 'r', encoding='utf-8'))
                
                # Route to appropriate processor
                if isinstance(data, list) and data[0].get("content"):
                    chunks = self._process_itri_golden_entries(data, file_name)
                elif 'raw_data' in file_name:
                    chunks = self._process_raw_data(data, file_name)
                elif 'qa_pairs' in file_name:
                    chunks = self._process_qa_pairs(data, file_name)
                # ... more processors
                
                all_chunks.extend(chunks)
    
    return all_chunks
```

**Note**: The RAG pipeline uses semantic chunking (300 chars, 50 overlap) for general documents, while `create_showroom_db.py` uses one-item-per-chunk for structured data.

#### Semantic Chunking

```python
def semantic_chunking(self, text: str, source_file: str):
    chunks = []
    sentences = re.split(r'[。！？.!?]', text)  # Split by sentence boundaries
    sentences = [s.strip() for s in sentences if s.strip()]
    
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > self.chunk_size:
            if current_chunk:
                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{source_file}_{self.chunk_counter}",
                    # ... metadata
                ))
                
                # Overlap handling
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += " " + sentence
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(DocumentChunk(...))
    
    return chunks
```

#### Vector Store Building

```python
def build_hybrid_vector_store(self, chunks, collection_name, reload=False):
    chroma_client = chromadb.PersistentClient(path=chroma_db_path)
    
    if reload:
        # Create new collection
        chroma_collection = chroma_client.create_collection(collection_name)
        
        # Build TF-IDF index
        self._build_tfidf_index(chunks)
        
        # Generate embeddings
        embeddings = []
        for chunk in chunks:
            embedding = requests.post(
                "http://localhost:11435/api/embeddings",
                json={"model": "bge-m3:latest", "prompt": chunk.content}
            ).json()['embedding']
            embeddings.append(embedding)
        
        # Store in ChromaDB
        chroma_collection.add(
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=[chunk.metadata for chunk in chunks],
            ids=[chunk.chunk_id for chunk in chunks]
        )
    else:
        # Load existing collection
        chroma_collection = chroma_client.get_collection(collection_name)
        self._build_tfidf_index(chunks)
    
    return chroma_collection, "bge-m3:latest"
```

### 3.3 System Prompt Engineering

#### QA Agent System Prompt

```python
def build_fixed_system_prompt(response_restriction: str):
    return f"""
    ## 角色設定
    你現在是「工業技術研究院 (ITRI, 工研院) 的權威知識系統」。
    你的唯一目標是從提供的 `rag_reference` 中提取並提供準確的資訊。
    
    ## 任務目標
    請完全根據 `rag_reference` 產出事實、客觀且準確的回答。 {response_restriction}
    
    ## 限制
    - **長度濃縮**：回答必須在 100 個字以內
    - **精準扼要**：僅回答使用者問題的核心資訊
    - **單一重點**：回覆內容長度應控制在 **50 個字以內**
    
    ## 核心約束
    1. **來源根據**：僅使用 `rag_reference`。如果資料中缺乏相關資訊，請回答「我不知道」。
    2. **重寫查詢理解**：優先使用 `rewritten_query` 來理解使用者的真實意圖。
    3. **身份執行**：絕對禁止稱呼自己為「AI」或「機器人」。請自稱為「我們」或「工研院」。
    4. **寒暄與問候處理規範**：若包含打招呼意圖，請回答問候語；若包含具體查詢，直接輸出事實回答。
    5. **語言一致性**：若使用者的問題是中文，請使用繁體中文回答；否則使用英文。
    """
```

#### Tone System Prompts

Each tone has a specialized system prompt with:
- **Role Definition**: Specific persona (e.g., "科學探險隊隊長" for child_friendly)
- **Style Guidelines**: Vocabulary, expressions, and communication patterns
- **Few-Shot Examples**: Concrete examples showing desired output format
- **Appearance Integration Rules**: First message vs. subsequent message behavior
- **Output Format Requirements**: Strict rules about no prefixes, no explanations

**Example (Child Friendly)**:
```python
def build_child_friendly_system_prompt(target_lang: str):
    return f"""
    ## ROLE
    你是一位在工研院博物館工作的「科學探險隊隊長」。
    你充滿活力、熱愛冒險，擅長把複雜的科技變成超酷的神奇魔法。
    
    ## TARGET LANGUAGE
    {target_lang}
    
    ## IMAGERY & INTERACTIVE PHRASES GUIDANCE
    - **驚奇開場**：「嘿！你有發現嗎...」、「哇！這絕對會讓你大吃一驚...」
    - **擬人化比喻**：「這就像是裝滿能量的小怪獸...」、「電力正在電線裡賽跑呢...」
    - **邀請觀察**：「快看這裡！...」、「你猜猜看會發生什麼事？...」
    - **嚴禁使用表情符號 (No Emojis)**
    
    ## FEW-SHOT EXAMPLES
    [Concrete examples showing desired output format]
    """
```

---

## 4. API Endpoints and Functionality

### 4.1 Core Endpoints

#### `/api/rag-llm/query` (POST)

**Purpose**: Main query endpoint with optional tone conversion

**Request Parameters**:
```json
{
  "text_user_msg": "User question",
  "session_id": "optional_session_id",
  "include_history": true,
  "user_description": "visual description (optional)",
  "convert_tone": false
}
```

**Response**: Streaming text chunks followed by `END_FLAG`

**Processing Flow**:
1. Parse request and validate
2. Retrieve session history
3. If `convert_tone=true`: Call `_generate_streaming_response_with_tone()`
4. Else: Call `_generate_streaming_response()` directly
5. Stream response to client

#### `/api/rag-llm/query-with-tone` (POST)

**Purpose**: Query with automatic dynamic tone conversion

**Request Parameters**: Same as `/api/rag-llm/query`, but `convert_tone` defaults to `true`

**Workflow**:
1. Parallel processing: Fetch user description + Generate QA response
2. Determine appropriate tone based on visual analysis
3. Convert response tone using specialized LLM agent
4. Stream adapted response to client

#### `/api/rag-llm/convert-tone` (POST)

**Purpose**: Standalone tone conversion service

**Request Parameters**:
```json
{
  "text": "Text to convert",
  "tone": "child_friendly",
  "stream": true,
  "user_description": "visual description",
  "user_msg": "original user message"
}
```

**Features**:
- Supports streaming and non-streaming modes
- Context-aware conversion using user appearance and original message
- Multiple tone options with specialized prompts

#### `/api/rag-llm/warmup` (POST)

**Purpose**: Model preloading for reduced latency

**Process**:
1. **Embedding Model Warmup**: Test embedding generation with ChromaDB query
2. **LLM Warmup**: Send minimal test request to Ollama service
3. **Performance Metrics**: Returns warmup time and success status

**Response**:
```json
{
  "embedding_model": {
    "status": "success",
    "time_ms": 123.45,
    "message": "Embedding model warmed up successfully"
  },
  "llm_model": {
    "status": "success",
    "time_ms": 567.89,
    "message": "LLM model warmed up successfully"
  },
  "overall_success": true
}
```

### 4.2 Session Management

#### `/api/rag-llm/sessions/{session_id}/history` (GET/DELETE)

**Purpose**: Chat history management per session

**GET Response**:
```json
{
  "session_id": "user_123",
  "history": [
    {"role": "user", "content": "工研院是什麼？"},
    {"role": "assistant", "content": "工研院是台灣最大的..."}
  ],
  "message_count": 2
}
```

**Features**:
- Retrieve complete conversation history
- Clear session data for privacy
- Message count tracking

#### `/api/rag-llm/close` (POST)

**Purpose**: Graceful connection termination

**Request**:
```json
{
  "session_id": "user_123"
}
```

**Process**:
1. Session existence validation
2. Message count calculation
3. Session cleanup and logging
4. Confirmation response with metrics

**Response**:
```json
{
  "success": true,
  "session_id": "user_123",
  "message": "Connection closed successfully",
  "session_existed": true,
  "messages_cleared": 10,
  "timestamp": 1234567890.123
}
```

---

## 5. Integration Points

### 5.1 External Service Dependencies

#### 5.1.1 Ollama LLM Service (localhost:11435)

**APIs Used**:
- `/api/chat`: Main chat completion endpoint
  - Used for: QA generation, tone conversion, query rewriting, tone selection
  - Model: `linly-llama3.1:70b-instruct-q4_0`
  - Temperature: Contextual (0.1 for analysis, 0.3 for tone conversion, 0.7 for QA)
  - Streaming: Supported for real-time responses
- `/api/embeddings`: Text embedding generation
  - Used for: Document embeddings, query embeddings
  - Model: `bge-m3:latest`
  - Prefixes: `search_document:` for documents, `search_query:` for queries

**Configuration**:
- Model: Configurable via `LLM_MODEL_NAME` in `config.py`
- Host: `http://localhost:11435` (default)
- Timeout: 120 seconds for LLM, 10 seconds for embeddings

#### 5.1.2 ChromaDB Vector Database

**Purpose**: Document storage and retrieval using vector embeddings

**Configuration**:
- Path: Configurable via `CHROMA_DB_PATH` in `config.py`
- Collection Strategy: Auto-detection with fallback creation
- Embedding Function: Uses Ollama embedding API (not built-in)
- Collection Name: `{museum_name}_collection` (e.g., `itri_museum_collection`)

**Operations**:
- `query()`: Vector similarity search with `query_embeddings`
- `add()`: Store documents with embeddings and metadata
- `get_collection()`: Load existing collection
- `create_collection()`: Create new collection

#### 5.1.3 Vision Context API (localhost:5004)

**Endpoint**: `GET /visual-context/{session_id}`

**Purpose**: Retrieve user appearance descriptions from VLM analysis

**Request**:
```http
GET /visual-context/abc123def456
```

**Response Format**:
```json
{
  "available": true,
  "visual_context": "a young boy wearing glasses, and is smiling"
}
```

**Error Handling**:
- Connection error: Returns empty string, defaults to `casual_friendly`
- Timeout: Returns empty string after 5 seconds
- Unavailable: `available: false`, returns empty string

### 5.2 Data Flow Integration

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

## 6. Performance Optimizations

### 6.1 Parallel Processing

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

### 6.2 Streaming Responses

**Benefits**: 
- Immediate user feedback (perceived latency reduction)
- Better user experience for long responses
- Progressive rendering in client applications

**Implementation**: 
- Yields chunks as they arrive from LLM
- Sends `END_FLAG` when complete
- Client can process chunks incrementally

### 6.3 Model Warmup

**Purpose**: Preload models into memory to eliminate cold start delays

**Components**: 
- Embedding model warmup: Test ChromaDB query
- LLM warmup: Minimal test request

**Impact**: 
- First request latency: ~10-15s → ~2-3s
- Subsequent requests: No change

### 6.4 Session Caching

**Implementation**: In-memory chat history storage with configurable retention

**Benefits**: 
- Context-aware responses without database overhead
- Fast history retrieval
- Automatic cleanup on session close

**Limitations**: 
- Not persistent across server restarts
- Memory usage scales with active sessions

### 6.5 Query Rewriting

**Purpose**: Improve document retrieval accuracy, especially for follow-up questions

**Impact**: 
- Better context retrieval for ambiguous queries
- Improved handling of pronouns and references
- Enhanced follow-up question understanding

---

## 7. Error Handling and Reliability

### 7.1 Graceful Degradation

**RAG Failure**: 
- Falls back to LLM-only mode
- Logs error but continues processing
- Returns response without RAG context

**Vision API Unavailable**: 
- Uses default `casual_friendly` tone
- Logs warning but continues processing
- No impact on core functionality

**ChromaDB Issues**: 
- Creates fallback collections or continues without RAG
- Attempts multiple collection name variations
- Falls back to LLM-only mode if all attempts fail

### 7.2 Connection Management

**Timeout Handling**: 
- Configurable timeouts for external service calls
- Vision API: 5 seconds
- LLM API: 120 seconds for QA, 30 seconds for tone conversion
- Embedding API: 10 seconds

**Retry Logic**: 
- Implicit retry through service redundancy
- No explicit retry loops (relies on service availability)

**Graceful Shutdown**: 
- Proper session cleanup on service termination
- `/api/rag-llm/close` endpoint for explicit cleanup

### 7.3 Monitoring and Diagnostics

**Health Endpoints**: 
- `/health`: System status and component health checks
- Returns RAG initialization status

**Comprehensive Logging**: 
- Structured logging for debugging and monitoring
- Color-coded console output (GREEN=success, YELLOW=warning, RED=error)
- Detailed timing information

**Performance Metrics**: 
- Warmup timing and response performance tracking
- Chunk count and response length logging
- Parallel task completion tracking

---

## 8. Configuration and Deployment

### 8.1 Configuration Management

**Key Configuration Points**:

#### Configuration File (`config.py`)

The `config.py` file is located in the project root directory and serves as the central configuration for the entire system.

**Location**: `./config.py` (root directory)

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

#### Runtime Configuration (CLI Arguments)

- Host/Port: Service binding configuration (`--host`, `--port`)
- Vision API URL: External VLM service integration (`--user-description-server`)
- Auto-initialization: RAG system setup on startup (`--auto-init`)
- Debug mode: Detailed logging (`--debug`)

### 8.2 Deployment Options

**Standalone Deployment**:
```bash
python rag_llm_api.py --host 0.0.0.0 --port 5002 --auto-init
```

**Production Considerations**:
- CORS configuration for cross-origin requests (enabled by default)
- Threaded Flask application for concurrent requests
- Auto-initialization option for seamless startup
- Environment variable configuration for security
- Model warmup on startup (recommended)

**Recommended Startup Sequence**:

1. **Clone Repository**:
   ```bash
   git clone git@github.com:HelloHe110/Demo_llm_agent.git
   cd Demo_llm_agent
   ```

2. **Set Up Python Environment**:
   ```bash
   # Option A: Virtual Environment
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install flask flask-cors requests chromadb numpy scikit-learn jieba gradio
   
   # Option B: Conda
   conda create -n rag_llm python=3.8 -y
   conda activate rag_llm
   pip install flask flask-cors requests chromadb numpy scikit-learn jieba gradio
   ```

3. **Configure System** (`config.py`):
   ```python
   LLM_MODEL_NAME = "linly-llama3.1:70b-instruct-q4_0"
   CHROMA_DB_PATH = "/path/to/chroma_db_golden"
   ```

4. **Start Ollama Server**:
   ```bash
   CUDA_VISIBLE_DEVICES=0,1,2,3 \
   OLLAMA_HOST=127.0.0.1:11435 \
   ollama serve
   ```

5. **Download Models** (in new terminal):
   ```bash
   ollama pull linly-llama3.1:70b-instruct-q4_0
   ollama pull bge-m3:latest
   ```

6. **Build ChromaDB** (if not already built):
   ```bash
   cd LLM_Chat
   python create_showroom_db.py --golden --reload --embedding-model bge-m3:latest
   ```

7. **Start Vision Context API** (optional, if using VLM):
   ```bash
   # Development: Random descriptions
   cd API
   python random_user_description_server.py --port 5003
   
   # Production: Real VLM
   # python vision_api_multi_session.py  # Port 5004
   ```

8. **Start RAG LLM API Server**:
   ```bash
   cd API
   python rag_llm_api.py --auto-init --user-description-server http://localhost:5003
   ```

9. **Start Model Warmup Server** (optional but recommended):
   ```bash
   cd API
   python model_warmup_server.py --api-url http://localhost:5002 --interval 60
   ```

10. **Test the System**:
    ```bash
    cd API
    python test_rag_llm_api.py --usr_msg "工研院是什麼？" --session_id "test"
    ```

---

## 9. Future Enhancement Opportunities

### 9.1 Scalability Improvements

- **Persistent Session Storage**: Database-backed session management (Redis/PostgreSQL)
- **Load Balancing**: Multi-instance deployment support
- **Caching Layer**: Redis integration for performance optimization
- **Async Processing**: AsyncIO for better concurrency

### 9.2 Feature Extensions

- **Multi-modal Input**: Image and voice input processing
- **Advanced Analytics**: User interaction tracking and analytics
- **A/B Testing**: Dynamic tone selection algorithm improvement
- **Custom Tone Profiles**: User-defined tone preferences
- **Response Caching**: Cache common queries for faster responses

### 9.3 Security Enhancements

- **Authentication**: JWT-based user authentication
- **Rate Limiting**: API abuse prevention
- **Input Validation**: Enhanced security for user inputs
- **HTTPS Support**: Encrypted communication
- **API Key Management**: Secure API access control

---

## 10. Conclusion

The RAG + LLM API Server represents a sophisticated integration of multiple AI technologies, providing a comprehensive solution for intelligent, context-aware, and tone-adaptive question-answering. Its parallel processing architecture, dynamic tone selection capabilities, and robust error handling make it suitable for production deployment in various interactive AI applications.

**Key Strengths**:
- Parallel processing reduces latency
- Dynamic tone adaptation based on user demographics
- Robust error handling and graceful degradation
- Streaming responses for better UX
- Comprehensive session management
- Multi-language support (English/繁體中文)

**Architecture Highlights**:
- Modular design allows for easy extension and customization
- Comprehensive API surface provides flexibility for different client implementations
- Combination of RAG for accuracy, LLM for generation quality, and VLM for personalization creates a powerful AI service platform

The server's design philosophy emphasizes **performance**, **reliability**, and **user experience**, making it an ideal foundation for building production-grade AI applications.
