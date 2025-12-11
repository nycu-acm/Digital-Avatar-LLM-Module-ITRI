# client_utils.py Module Documentation

## Overview

The `client_utils.py` module provides a comprehensive set of utility functions for interacting with the RAG + LLM API service. It includes functions for streaming queries, health checks, system initialization, model warmup, and tone conversion capabilities.

## Core Functions

### Main Query Functions

#### `stream_rag_llm_query(api_url, text_user_msg, session_id)`

Stream a query to the RAG + LLM API service with real-time response processing.

**Parameters:**
- `api_url` (str): Base URL of the API service (e.g., `"http://localhost:5002"`)
- `text_user_msg` (str): The user's question or message
- `session_id` (str): Session identifier for conversation history

**Returns:**
- `str`: Complete accumulated response text

**Example:**
```python
from client_utils import stream_rag_llm_query

response = stream_rag_llm_query(
    "http://localhost:5002",
    "工研院是什麼？",
    "my_session_123"
)
print(f"Complete response: {response}")
```

#### `check_service_health(api_url)`

Verify that the API service is running and accessible.

**Parameters:**
- `api_url` (str): Base URL of the API service

**Returns:**
- `bool`: `True` if service is healthy, `False` otherwise

**Example:**
```python
from client_utils import check_service_health

if check_service_health("http://localhost:5002"):
    print("✅ Service is ready!")
else:
    print("❌ Service is not available")
```

## System Management Functions

#### `initialize_rag_system(api_url)`

Initialize the RAG system on the server.

**Parameters:**
- `api_url` (str): Base URL of the API service

**Returns:**
- `bool`: `True` if initialization succeeded, `False` otherwise

**Example:**
```python
from client_utils import initialize_rag_system

success = initialize_rag_system("http://localhost:5002")
if success:
    print("✅ RAG system initialized successfully")
else:
    print("❌ RAG initialization failed")
```

#### `warmup_models(api_url)`

Warm up the embedding model and LLM to reduce first-request latency.

**Parameters:**
- `api_url` (str): Base URL of the API service

**Returns:**
- `dict`: Detailed warmup results with timing information

**Example:**
```python
from client_utils import warmup_models

result = warmup_models("http://localhost:5002")
if result and result.get('overall_success'):
    print("✅ Models warmed up successfully!")
    print(f"Total time: {result['embedding_model']['time_ms'] + result['llm_model']['time_ms']:.0f}ms")
else:
    print("⚠️ Warmup had issues")
```

#### `close_connection(api_url, session_id)`

Gracefully close a session and clean up server-side resources.

**Parameters:**
- `api_url` (str): Base URL of the API service
- `session_id` (str): Session identifier to close

**Returns:**
- `bool`: `True` if connection was closed successfully

**Example:**
```python
from client_utils import close_connection

success = close_connection("http://localhost:5002", "my_session_123")
if success:
    print("✅ Connection closed successfully")
```

## Tone Conversion Functions

#### `convert_tone(text, tone, model_url, model_name)`

Convert text to a child-friendly speaking style using LLM rewriting with expressive audio tags.

**Parameters:**
- `text` (str): Original text to rewrite
- `tone` (str): Target tone (default: `"child_friendly"`)
- `model_url` (str): LLM API endpoint (default: `"http://localhost:11435/api/chat"`)
- `model_name` (str): Model identifier (default: `f"{LLM_MODEL_NAME}"`)

**Returns:**
- `str | None`: Rewritten text with audio tags if successful, `None` otherwise

**Example:**
```python
from client_utils import convert_tone

original = "ITRI was founded in 1973."
child_friendly = convert_tone(original)
print(child_friendly)
# Output: "[gasps] Wow, ITRI was founded way back in 1973! [excited] That's such an AMAZING organization!"
```

#### `stream_convert_tone(text, tone, model_url, model_name)`

Stream the tone conversion process so users can see rewritten text with audio tags as it's generated.

**Parameters:**
- Same as `convert_tone()`

**Returns:**
- `str | None`: Complete rewritten text with audio tags

**Example:**
```python
from client_utils import stream_convert_tone

original = "工研院成立於1973年"
converted = stream_convert_tone(original)
print(f"\nFinal result: {converted}")
# Output: "[curious] 工研院是在1973年成立的喔！[excited] 這是一個很厲害的機構呢！"
```

### Audio Tags for Enhanced Expression

Both tone conversion functions now include **expressive audio tags** to make the child-friendly speech more natural and engaging:

#### Supported Audio Tags
- **Emotional Expression**: `[curious]`, `[excited]`, `[giggles]`, `[whispers]`, `[sighs]`
- **Enthusiasm**: `[gasps]`, `[woo]`, `[laughs softly]`, `[exhales]`
- **Enhanced Punctuation**: Ellipses (`...`) for pauses, `CAPITALIZATION` for emphasis

#### Audio Tag Usage
- 1-2 tags per sentence for natural flow
- Child-appropriate and gentle expressions only
- Tags match content emotion (curious for questions, excited for achievements)
- Placed at natural speech breaks

#### Audio Tag Examples
```python
# English examples
"The museum has artifacts" → "[whispers] You know what? The museum has really COOL artifacts... [giggles] it's like magic!"
"ITRI researches AI" → "[curious] ITRI researches amazing AI technology! [excited] Isn't that incredible?"

# Chinese examples  
"這個技術很先進" → "[curious] 這個技術很先進呢！[excited] 是不是很厲害？"
"博物館有很多展品" → "[whispers] 博物館有很多很棒的展品喔... [giggles] 就像寶藏一樣！"
```

## Installation & Dependencies

### Required Python Packages

```bash
pip install requests
```

### System Requirements

- **Network Access**: API service must be reachable
- **JSON Support**: Built-in Python JSON handling

## Usage Examples

### Complete Workflow Example

```python
from client_utils import (
    check_service_health, 
    initialize_rag_system, 
    warmup_models, 
    stream_rag_llm_query, 
    close_connection
)
import time

def complete_rag_workflow():
    """Demonstrate complete RAG interaction workflow"""
    
    API_URL = "http://localhost:5002"
    SESSION_ID = f"demo_{int(time.time())}"
    
    print("🤖 RAG System Demo")
    print("=" * 50)
    
    # Step 1: Health check
    print("🔍 Checking service health...")
    if not check_service_health(API_URL):
        print("❌ Service not available")
        return False
    
    # Step 2: Initialize RAG system
    print("🔄 Initializing RAG system...")
    if not initialize_rag_system(API_URL):
        print("⚠️ RAG initialization failed, continuing anyway...")
    
    # Step 3: Warm up models
    print("🔥 Warming up models...")
    warmup_result = warmup_models(API_URL)
    if warmup_result and warmup_result.get('overall_success'):
        print("✅ Models ready!")
    
    # Step 4: Query the system
    questions = [
        "What is ITRI?",
        "工研院有什麼重要成就？",
        "Tell me about ITRI's research areas"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        response = stream_rag_llm_query(API_URL, question, SESSION_ID)
        if response:
            print(f"✅ Response received: {len(response)} chars")
        time.sleep(1)  # Brief pause between queries
    
    # Step 5: Clean shutdown
    print("\n👋 Closing connection...")
    if close_connection(API_URL, SESSION_ID):
        print("✅ Clean shutdown complete")
    
    return True

if __name__ == "__main__":
    complete_rag_workflow()
```

### Tone Conversion Example

```python
from client_utils import convert_tone, stream_convert_tone

def demonstrate_tone_conversion():
    """Show tone conversion capabilities with audio tags"""
    
    examples = [
        "ITRI is Taiwan's largest research institute.",
        "工研院成立於1973年，是台灣最重要的產業技術研發機構。",
        "The organization focuses on applied research and development."
    ]
    
    print("🎨 Tone Conversion Demo with Audio Tags")
    print("=" * 50)
    
    for i, text in enumerate(examples, 1):
        print(f"\n📝 Example {i}:")
        print(f"Original: {text}")
        
        # Non-streaming conversion with audio tags
        converted = convert_tone(text)
        if converted:
            print(f"Child-friendly with audio tags: {converted}")
            # Example outputs:
            # "[gasps] Wow, ITRI is Taiwan's BIGGEST research institute! [excited] That's incredible!"
            # "[curious] 工研院是在1973年成立的喔！[excited] 是台灣最重要的產業技術研發機構呢！"
            # "[whispers] You know what? The organization focuses on really COOL research... [giggles] it's like making the future!"
        
        # Alternative: streaming conversion
        print("\n🔄 Streaming conversion with audio tags:")
        stream_converted = stream_convert_tone(text)
        print(f"Final result: {stream_converted}")

if __name__ == "__main__":
    demonstrate_tone_conversion()
```

## Advanced Usage

### Custom Session Management

```python
import uuid
from client_utils import stream_rag_llm_query, close_connection

class RAGSession:
    """Wrapper class for managing RAG sessions"""
    
    def __init__(self, api_url):
        self.api_url = api_url
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.message_count = 0
    
    def ask(self, question):
        """Ask a question and return response"""
        response = stream_rag_llm_query(
            self.api_url, 
            question, 
            self.session_id
        )
        self.message_count += 1
        return response
    
    def close(self):
        """Clean up session"""
        return close_connection(self.api_url, self.session_id)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Usage with context manager
with RAGSession("http://localhost:5002") as session:
    answer1 = session.ask("What is ITRI?")
    answer2 = session.ask("What are its main research areas?")
    # Session automatically closed on exit
```

### Async Client Implementation

```python
import asyncio
import aiohttp
from client_utils import check_service_health

async def async_rag_query(session, api_url, question, session_id):
    """Async version of RAG query"""
    url = f"{api_url}/api/rag-llm/query"
    payload = {
        "text_user_msg": question,
        "session_id": session_id
    }
    
    async with session.post(url, json=payload) as response:
        content = ""
        async for chunk in response.content.iter_any():
            chunk_text = chunk.decode('utf-8')
            if "END_FLAG" in chunk_text:
                content += chunk_text.replace("END_FLAG", "")
                break
            content += chunk_text
        return content

async def batch_queries():
    """Process multiple queries concurrently"""
    questions = [
        "What is ITRI?",
        "工研院的歷史如何？", 
        "What research areas does ITRI focus on?"
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            async_rag_query(session, "http://localhost:5002", q, f"batch_{i}")
            for i, q in enumerate(questions)
        ]
        responses = await asyncio.gather(*tasks)
        return responses

# Usage
# responses = asyncio.run(batch_queries())
```

## Error Handling

### Network Error Handling

```python
import requests
from client_utils import stream_rag_llm_query

def robust_query(api_url, question, session_id, max_retries=3):
    """Query with retry logic"""
    
    for attempt in range(max_retries):
        try:
            return stream_rag_llm_query(api_url, question, session_id)
        except requests.exceptions.ConnectionError:
            print(f"Connection failed, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.Timeout:
            print(f"Request timed out, attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return None
```

### Response Validation

```python
def validate_response(response):
    """Validate RAG response quality"""
    if not response:
        return False, "Empty response"
    
    if len(response.strip()) < 10:
        return False, "Response too short"
    
    if "ERROR:" in response:
        return False, f"API error: {response}"
    
    # Check for reasonable content
    if response.count(' ') < 2:  # At least a few words
        return False, "Response seems incomplete"
    
    return True, "Valid response"

# Usage
response = stream_rag_llm_query(api_url, question, session_id)
is_valid, message = validate_response(response)
if not is_valid:
    print(f"⚠️ Response validation failed: {message}")
```

## Configuration

### Default Settings

```python
DEFAULT_CONFIG = {
    'api_url': 'http://localhost:5002',
    'ollama_url': 'http://localhost:11435/api/chat',
    'model_name': f"{LLM_MODEL_NAME}",
    'timeout': None,
    'max_retries': 3
}
```

### Environment Variables

```python
import os

API_URL = os.getenv('RAG_API_URL', 'http://localhost:5002')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11435/api/chat')
MODEL_NAME = os.getenv('LLM_MODEL', f"{LLM_MODEL_NAME}")
```

## Monitoring & Logging

### Response Time Monitoring

```python
import time
from client_utils import stream_rag_llm_query

def timed_query(api_url, question, session_id):
    """Query with timing measurement"""
    start_time = time.time()
    
    response = stream_rag_llm_query(api_url, question, session_id)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  Query completed in {duration:.2f} seconds")
    print(f"📊 Response length: {len(response) if response else 0} chars")
    
    return response, duration
```

### Health Monitoring

```python
import time
from client_utils import check_service_health, warmup_models

def monitor_service_health(api_url, interval=30):
    """Continuously monitor service health"""
    while True:
        try:
            if check_service_health(api_url):
                print(f"✅ {time.strftime('%H:%M:%S')} - Service healthy")
            else:
                print(f"❌ {time.strftime('%H:%M:%S')} - Service unhealthy")
                
                # Attempt to warm up models
                print("🔄 Attempting model warmup...")
                warmup_models(api_url)
                
        except KeyboardInterrupt:
            print("🛑 Monitoring stopped")
            break
        except Exception as e:
            print(f"⚠️ Monitoring error: {e}")
        
        time.sleep(interval)
```

## Testing

### Unit Tests

```python
import unittest
from unittest.mock import patch, Mock
from client_utils import check_service_health, stream_rag_llm_query

class TestClientUtils(unittest.TestCase):
    
    @patch('client_utils.requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'healthy'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = check_service_health("http://test:5002")
        self.assertTrue(result)
    
    @patch('client_utils.requests.post')
    def test_streaming_query(self, mock_post):
        """Test streaming query functionality"""
        mock_response = Mock()
        mock_response.iter_content.return_value = [
            'Hello', ' world', 'END_FLAG'
        ]
        mock_response.raise_for_status.return_value = None
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_post.return_value = mock_response
        
        result = stream_rag_llm_query(
            "http://test:5002", 
            "test question", 
            "test_session"
        )
        self.assertEqual(result, "Hello world")

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
def integration_test_suite():
    """Comprehensive integration test"""
    api_url = "http://localhost:5002"
    session_id = f"test_{int(time.time())}"
    
    tests = []
    
    # Test 1: Health check
    health_ok = check_service_health(api_url)
    tests.append(("Health Check", health_ok))
    
    # Test 2: RAG initialization  
    init_ok = initialize_rag_system(api_url)
    tests.append(("RAG Init", init_ok))
    
    # Test 3: Model warmup
    warmup_result = warmup_models(api_url)
    warmup_ok = warmup_result and warmup_result.get('overall_success')
    tests.append(("Model Warmup", warmup_ok))
    
    # Test 4: Simple query
    response = stream_rag_llm_query(api_url, "Test query", session_id)
    query_ok = response and len(response.strip()) > 0
    tests.append(("Simple Query", query_ok))
    
    # Test 5: Tone conversion with audio tags
    converted = convert_tone("Test text")
    tone_ok = converted and converted != "Test text" and ("[" in converted)
    tests.append(("Tone Conversion with Audio Tags", tone_ok))
    
    # Test 6: Connection close
    close_ok = close_connection(api_url, session_id)
    tests.append(("Connection Close", close_ok))
    
    # Report results
    print("\n📊 Integration Test Results")
    print("=" * 40)
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    overall = all(passed for _, passed in tests)
    print(f"\nOverall: {'✅ ALL PASS' if overall else '❌ SOME FAILED'}")
    return overall
```

## Troubleshooting

### Common Issues

**Connection Refused:**
```python
# Check if API service is running
curl http://localhost:5002/health

# Verify port and host settings
netstat -ln | grep 5002
```

**Streaming Response Issues:**
```python
# Check END_FLAG handling in response processing
# Verify chunk decoding (UTF-8)
```

**Tone Conversion Failures:**
```python
# Verify Ollama service availability
curl http://localhost:11435/api/tags

# Check model availability
ollama list | grep linly-llama3.1
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed request logging
import requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

## Performance Optimization

### Connection Reuse

```python
import requests

# Use session for connection pooling
session = requests.Session()

def optimized_query(question, session_id):
    """Use session for better performance"""
    url = "http://localhost:5002/api/rag-llm/query"
    payload = {"text_user_msg": question, "session_id": session_id}
    
    with session.post(url, json=payload, stream=True) as response:
        # Process streaming response...
        pass
```

### Concurrent Processing

```python
from concurrent.futures import ThreadPoolExecutor
from client_utils import stream_rag_llm_query

def batch_process_queries(questions, api_url, max_workers=3):
    """Process multiple queries concurrently"""
    
    def process_single(args):
        question, session_id = args
        return stream_rag_llm_query(api_url, question, session_id)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        args_list = [(q, f"batch_{i}") for i, q in enumerate(questions)]
        results = list(executor.map(process_single, args_list))
    
    return results
```

## License

This module is part of the ITRI Museum RAG system, developed for educational and research purposes.
