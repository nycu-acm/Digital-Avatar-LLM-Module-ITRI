# RAG + LLM API with Tone Conversion

The RAG + LLM API service now includes integrated tone conversion capabilities, allowing you to automatically convert responses to child-friendly speaking styles with emotional expression tags.

## New Features

### 🎨 Tone Conversion Integration
- **Standalone tone conversion** for any text
- **Automatic tone conversion** for RAG+LLM responses  
- **Optional tone conversion** in existing query endpoint
- **Streaming and non-streaming** support
- **Language detection** (Traditional Chinese / English)
- **Rich emotional expression tags** (69 different expressions)

## API Endpoints

### 1. `/api/rag-llm/convert-tone` - Standalone Tone Conversion

Convert any text to child-friendly speaking style with emotional expression tags.

**Request:**
```json
{
    "text": "Text to convert",
    "tone": "child_friendly",
    "stream": true
}
```

**Parameters:**
- `text` (required): Text to convert
- `tone` (optional): Target tone/style (default: "child_friendly")
- `stream` (optional): Enable streaming response (default: true)

**Streaming Response:** Text chunks followed by `END_FLAG`
**Non-streaming Response:**
```json
{
    "success": true,
    "original_text": "Original text",
    "converted_text": "Converted text with (expression) tags",
    "tone": "child_friendly"
}
```

### 2. `/api/rag-llm/query-with-tone` - Combined Query + Tone Conversion

Get RAG+LLM response with automatic tone conversion applied.

**Request:**
```json
{
    "text_user_msg": "Your question here",
    "session_id": "optional_session_id",
    "include_history": true,
    "tone": "child_friendly",
    "convert_tone": true
}
```

**Parameters:**
- `text_user_msg` (required): User's question
- `session_id` (optional): Session identifier
- `include_history` (optional): Include chat history (default: true)
- `tone` (optional): Target tone for conversion (default: "child_friendly")
- `convert_tone` (optional): Enable tone conversion (default: true)

**Response:** Streaming tone-converted text followed by `END_FLAG`

### 3. `/api/rag-llm/query` - Enhanced Original Query Endpoint

The original query endpoint now supports optional tone conversion.

**Request:**
```json
{
    "text_user_msg": "Your question here",
    "session_id": "optional_session_id", 
    "include_history": true,
    "tone": "child_friendly",
    "convert_tone": false
}
```

**New Parameters:**
- `tone` (optional): Target tone for conversion (default: "child_friendly")
- `convert_tone` (optional): Enable tone conversion (default: false for backward compatibility)

## Expression Tags

The tone conversion system uses 69 different emotional expression tags:

### Basic Emotions (24)
`(angry)` `(sad)` `(excited)` `(surprised)` `(satisfied)` `(delighted)` `(scared)` `(worried)` `(upset)` `(nervous)` `(frustrated)` `(depressed)` `(empathetic)` `(embarrassed)` `(disgusted)` `(moved)` `(proud)` `(relaxed)` `(happy)` `(calm)` `(confident)` `(grateful)` `(curious)` `(sarcastic)`

### Advanced Emotions (25)
`(disdainful)` `(unhappy)` `(anxious)` `(hysterical)` `(indifferent)` `(uncertain)` `(doubtful)` `(confused)` `(disappointed)` `(regretful)` `(guilty)` `(ashamed)` `(jealous)` `(envious)` `(hopeful)` `(optimistic)` `(pessimistic)` `(nostalgic)` `(lonely)` `(bored)` `(contemptuous)` `(sympathetic)` `(compassionate)` `(determined)` `(resigned)`

### Tone Markers (5)
`(in a hurry tone)` `(shouting)` `(screaming)` `(whispering)` `(soft tone)`

### Audio Effects (10)
`(laughing)` `(chuckling)` `(sobbing)` `(crying loudly)` `(sighing)` `(groaning)` `(panting)` `(gasping)` `(yawning)` `(snoring)`

### Special Effects (5)
`(audience laughing)` `(background laughter)` `(crowd laughing)` `(break)` `(long-break)`

## Examples

### English Example
**Original:** "ITRI was founded in 1973"  
**Converted:** "(surprised) Oh wow! ITRI was founded all the way back in 1973! (amazed) That's such a long history!"

### Traditional Chinese Example
**Original:** "工研院成立於1973年"  
**Converted:** "(surprised) 哇！工研院在1973年就成立了呀！(amazed) 這麼久的歷史真讓人驚訝呢！"

## Usage Examples

### Python Client Examples

```python
import requests

# 1. Standalone tone conversion
response = requests.post("http://localhost:5002/api/rag-llm/convert-tone", 
    json={"text": "ITRI develops advanced technologies", "stream": True}, 
    stream=True)

# 2. Query with automatic tone conversion
response = requests.post("http://localhost:5002/api/rag-llm/query-with-tone",
    json={"text_user_msg": "What is ITRI?", "session_id": "demo"}, 
    stream=True)

# 3. Original query with optional tone conversion
response = requests.post("http://localhost:5002/api/rag-llm/query",
    json={"text_user_msg": "Tell me about ITRI", "convert_tone": True}, 
    stream=True)
```

### Demo Script

Run the included demo script to see all features:

```bash
cd /workspace/API
python api_client_tone_example.py
```

## Language Support

- **Automatic language detection** based on input text
- **Traditional Chinese (繁體中文)** for Chinese input
- **English** for non-Chinese input
- Maintains language consistency in converted output

## Integration Notes

- All tone conversion is handled server-side
- No client-side dependencies required
- Backward compatible with existing clients
- Stream processing for real-time user experience
- Graceful error handling with fallback to original text

## Requirements

- RAG + LLM API service running on port 5002
- Ollama service with `f"{LLM_MODEL_NAME}" = linly-llama3.1:70b-instruct-q4_0` model
- ChromaDB for RAG functionality (optional for tone-only conversion)

## Error Handling

The system gracefully handles errors and will:
- Return original text if tone conversion fails
- Provide detailed error messages in API responses
- Continue RAG+LLM functionality even if tone conversion is unavailable
