# Parallel Dynamic Tone Selection Architecture

## Overview

This document describes the parallel architecture for dynamic tone selection, where user description fetching and QA response generation happen simultaneously to minimize latency.

## Architecture Components

### 1. Random User Description Server (`random_user_description_server.py`)
- **Port**: 5003 (default)
- **Purpose**: Simulates a Vision Language Model (VLM) that analyzes camera input and generates user descriptions
- **Endpoint**: `GET /api/get-user-description`
- **Returns**: Random user description from a predefined pool

In production, this would be replaced by an actual VLM service that processes camera frames.

### 2. RAG LLM API Server (`rag_llm_api.py`)
- **Port**: 5002 (default)
- **Purpose**: Main API server that handles queries with dynamic tone selection
- **Key Feature**: Parallel processing for efficiency

## Parallel Processing Flow

```
Client Request
     │
     ├─────────────────────────────────────────┐
     │                                          │
     ▼                                          ▼
┌─────────────────────┐              ┌──────────────────────┐
│ Fetch User Desc     │              │ Generate QA Response │
│ from Desc Server    │   PARALLEL   │ using RAG + LLM      │
│ (Task 1)            │   EXECUTION  │ (Task 2)             │
└─────────────────────┘              └──────────────────────┘
     │                                          │
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
            │ (with user context)  │
            └──────────────────────┘
                       │
                       ▼
            Stream Response to Client
```

## Key Benefits

1. **Reduced Latency**: User description fetching and QA generation happen simultaneously
2. **Better Resource Utilization**: Both CPU and network I/O are used efficiently
3. **Enhanced Context**: User description and original message are passed to tone converter
4. **Scalability**: Easy to add more parallel tasks if needed

## Quick Start

### Option 1: Using the Start Script (Recommended)

```bash
cd API
bash start_servers.sh
```

This will:
- Start the random user description server on port 5003
- Start the RAG LLM API server on port 5002
- Configure automatic connection between them

### Option 2: Manual Start

**Terminal 1 - Start User Description Server:**
```bash
cd API
python3 random_user_description_server.py --port 5003
```

**Terminal 2 - Start RAG LLM API Server:**
```bash
cd API
python3 rag_llm_api.py --auto-init --user-description-server http://localhost:5003
```

## Testing

Run the parallel dynamic tone selection test:

```bash
cd API
python3 test_parallel_dynamic_tone.py
```

This test demonstrates:
- Automatic user description fetching
- Parallel processing of description and QA
- Dynamic tone selection based on fetched description
- Streaming response with tone conversion

## API Usage

### Client Request

```python
import requests

payload = {
    "text_user_msg": "What is ITRI?",
    "session_id": "user_123",
    "convert_tone": True,
    "include_history": False
    # NOTE: No user_description needed - server fetches it automatically!
}

response = requests.post(
    "http://localhost:5002/api/rag-llm/query",
    json=payload,
    stream=True
)

# Collect streaming response
for line in response.iter_lines(decode_unicode=True):
    if line == "END_FLAG":
        break
    elif not line.startswith("ERROR:"):
        print(line, end='', flush=True)
```

### Server Processing (Automatic)

1. **Parallel Execution** (happens automatically):
   - Thread 1: `GET http://localhost:5003/api/get-user-description`
   - Thread 2: Generate RAG+LLM response

2. **Synchronization**: Wait for both threads to complete

3. **Tone Determination**: Analyze fetched user description

4. **Tone Conversion**: Convert QA response with user context
   - Original text
   - Selected tone
   - User description (for context)
   - User message (for context)

5. **Stream Response**: Send tone-converted response to client

## Configuration

### RAG LLM API Server Options

```bash
python3 rag_llm_api.py \
    --host 0.0.0.0 \
    --port 5002 \
    --auto-init \
    --user-description-server http://localhost:5003 \
    --debug
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5002)
- `--auto-init`: Auto-initialize RAG system on startup
- `--user-description-server`: URL of user description server (default: http://localhost:5003)
- `--debug`: Enable debug mode

### Random User Description Server Options

```bash
python3 random_user_description_server.py \
    --host 0.0.0.0 \
    --port 5003 \
    --debug
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5003)
- `--debug`: Enable debug mode

## Customizing the Description Pool

Edit `random_user_description_server.py` and modify the `USER_DESCRIPTION_POOL` list:

```python
USER_DESCRIPTION_POOL = [
    "a young boy wearing glasses, and is smiling",
    "an elderly woman with white hair",
    # Add your own descriptions here
]
```

## Enhanced Tone Conversion

The tone conversion agent now receives additional context:

```python
def _stream_convert_tone(
    text: str,                      # The QA response to convert
    tone: str,                      # Selected tone
    user_description: str = "",     # Visual description from VLM
    user_msg: str = ""             # Original user question
):
    # Context is passed to the tone converter for better results
    context_info = ""
    if user_description:
        context_info += f"\nUser Appearance: {user_description}"
    if user_msg:
        context_info += f"\nUser Question: {user_msg}"
    
    # Tone converter can now use this context
```

This allows the tone converter to:
- Understand the user's profile better
- Adapt language based on the original question
- Provide more personalized responses

## Performance Monitoring

The console output shows timing information:

```
🚀 Starting parallel processing for user description and QA response...
⏳ Waiting for parallel tasks to complete...
✅ Parallel tasks completed!
📸 User description: 'a young boy wearing glasses, and is smiling'
💬 QA response length: 156 chars
🎯 Tone selected: child_friendly (based on VLM description: '...')
🎨 Converting tone to child_friendly (determined from VLM description)...
```

## Production Deployment

### Replacing Random Description Server with Real VLM

1. **Implement VLM Service**: Create a service that processes camera frames
2. **Match API Contract**: Ensure it returns JSON with `user_description` field
3. **Update Configuration**: Point RAG API to your VLM service URL

Example VLM service response:
```json
{
    "success": true,
    "user_description": "a middle-aged person in casual clothing",
    "confidence": 0.95,
    "timestamp": 1634567890.123
}
```

### Scaling Considerations

1. **Load Balancing**: Deploy multiple instances of each service
2. **Caching**: Cache user descriptions for a session to reduce VLM calls
3. **Async Processing**: Consider using async frameworks for higher concurrency
4. **Monitoring**: Add metrics for parallel task execution times

## Troubleshooting

### User Description Server Not Available

If the description server is unavailable, the system gracefully falls back:
- Uses empty user_description
- Defaults to `casual_friendly` tone
- Logs warning but continues processing

### Parallel Tasks Taking Too Long

Check:
1. VLM/Description server response time
2. RAG database query performance
3. LLM response generation time
4. Network latency between services

Use the console logs to identify which task is the bottleneck.

## Future Enhancements

1. **Adaptive Timeout**: Adjust timeouts based on historical performance
2. **Intelligent Fallback**: Use previous user description if current fetch fails
3. **Batch Processing**: Process multiple requests in a batch for efficiency
4. **Caching Layer**: Cache tone conversions for similar inputs
5. **Real-time Monitoring**: Dashboard for parallel processing metrics

## Examples

See `test_parallel_dynamic_tone.py` for complete working examples of:
- Basic parallel processing
- Multiple test cases with different languages
- Performance measurement
- Error handling

## Summary

The parallel architecture significantly improves response times by:
- Fetching user descriptions while generating QA responses
- Passing rich context to the tone converter
- Maintaining backward compatibility with existing clients
- Providing graceful fallbacks when services are unavailable

This design is production-ready and scalable for real-world deployments.



