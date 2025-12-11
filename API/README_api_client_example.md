# 📱 RAG + LLM API Client Guide with Server-Side Tone Conversion

A comprehensive guide for developers to access the RAG + LLM API service with integrated server-side tone conversion using the provided client utilities.

## 🎯 Overview

This guide shows you how to use the pre-built client utilities in `client_utils.py` to interact with the RAG + LLM API service with integrated server-side tone conversion. All the complex connection handling, streaming, session management, and tone conversion processing is already implemented for you!

### 🆕 New Features

- **Server-Side Tone Conversion**: Tone conversion now happens on the server, providing better performance and simplified client code
- **Streaming Tone-Converted Responses**: Get real-time streaming of tone-converted text directly from the API
- **Integrated Processing**: No need for separate client-side tone conversion calls
- **Backward Compatibility**: Legacy client-side tone conversion functions are still available

## 🚀 Quick Start

### 1. Import the Client Utilities

```python
from client_utils import (
    stream_rag_llm_query,      # Enhanced with tone conversion support
    stream_rag_llm_with_tone,  # Convenience function for tone conversion
    check_service_health,
    initialize_rag_system,
    warmup_tone_conversion,    # New: Warmup tone conversion models
    close_connection
)
import time
```

### 2. Basic Usage Pattern

```python
# Configuration
API_URL = "http://localhost:5002"
SESSION_ID = f"my_app_{int(time.time())}"  # Unique session ID

# 1. Check if service is running
if not check_service_health(API_URL):
    print("❌ API service is not available!")
    exit(1)

# 2. Initialize RAG system (optional, but recommended)
initialize_rag_system(API_URL)

# 3. Optional: Warmup tone conversion models for better performance
warmup_tone_conversion(API_URL)

# 4. Send queries with server-side tone conversion (NEW!)
response = stream_rag_llm_with_tone(
    api_url=API_URL,
    text_user_msg="What is ITRI?",
    session_id=SESSION_ID,
    tone_style="child_friendly"
)

# OR use the enhanced function with manual control:
response = stream_rag_llm_query(
    api_url=API_URL,
    text_user_msg="What is ITRI?",
    session_id=SESSION_ID,
    enable_tone_conversion=True,
    tone_style="child_friendly"
)

# 5. IMPORTANT: Always close connection before termination
close_connection(API_URL, SESSION_ID)
```

## 📚 Client Functions Reference

### 🏥 `check_service_health(api_url)`

**Purpose**: Verify that the API service is running and healthy.

```python
# Check if service is available
if check_service_health("http://localhost:5002"):
    print("✅ Service is ready!")
else:
    print("❌ Service is not available")
```

**Output**: Console status information and boolean return value.

---

### 🔄 `initialize_rag_system(api_url)`

**Purpose**: Initialize the RAG system on the server (one-time setup).

```python
# Initialize RAG capabilities
success = initialize_rag_system("http://localhost:5002")
if success:
    print("✅ RAG system ready for queries!")
```

**Output**: Initialization status and boolean return value.

---

### 🤖 `stream_rag_llm_query(api_url, text_user_msg, session_id, **tone_options)`

**Purpose**: Send a query and receive streaming response from the RAG + LLM system with optional server-side tone conversion.

```python
# Basic query without tone conversion
response = stream_rag_llm_query(
    api_url="http://localhost:5002",
    text_user_msg="Tell me about ITRI's research areas",
    session_id="my_session_123"
)

# Query with server-side tone conversion (NEW!)
response = stream_rag_llm_query(
    api_url="http://localhost:5002",
    text_user_msg="Tell me about ITRI's research areas",
    session_id="my_session_123",
    enable_tone_conversion=True,
    tone_style="child_friendly"
)

print(f"Final response: {response}")
```

**Enhanced Features**:
- Real-time streaming output to console
- **NEW**: Server-side tone conversion support
- Automatic END_FLAG detection
- Session history maintained
- Returns accumulated response text (tone converted if enabled)

**New Parameters**:
- `enable_tone_conversion`: Enable server-side tone conversion (default: False)
- `tone_style`: Target tone style (default: "child_friendly")
- `tone_model_url`: Custom tone conversion model URL (optional)
- `tone_model_name`: Custom tone conversion model name (optional)

---

### 🎨 `stream_rag_llm_with_tone(api_url, text_user_msg, session_id, tone_style)`

**Purpose**: Convenience function for RAG + LLM queries with server-side tone conversion enabled.

```python
# Simplified tone conversion usage
response = stream_rag_llm_with_tone(
    api_url="http://localhost:5002",
    text_user_msg="Tell me about ITRI's research areas",
    session_id="my_session_123",
    tone_style="child_friendly"
)

print(f"Tone-converted response: {response}")
```

**Features**:
- Automatically enables tone conversion
- Simplified parameter set
- Same streaming and session features as main function

---

### 🔥 `warmup_tone_conversion(api_url)`

**Purpose**: Warmup the tone conversion models on the server to reduce first-request latency.

```python
# Warmup tone conversion models
success = warmup_tone_conversion("http://localhost:5002")
if success:
    print("✅ Tone conversion ready!")
```

**Benefits**:
- Reduces latency on first tone conversion request
- Preloads models into memory
- Should be called after `initialize_rag_system()`

---

### 👋 `close_connection(api_url, session_id)`

**Purpose**: Elegantly close connection and clear session history before program termination.

```python
# Always call before your program exits
success = close_connection("http://localhost:5002", "my_session_123")
if success:
    print("✅ Connection closed gracefully")
```

**Important**: This cleans up server-side session data and should always be called before program termination.

## 💡 Complete Example Implementation

Here's a complete example showing proper client implementation:

```python
#!/usr/bin/env python3
"""
My RAG + LLM Client Application
"""

from client_utils import (
    stream_rag_llm_query,
    check_service_health,
    initialize_rag_system,
    close_connection
)
import time
import sys

def main():
    """Main application logic"""
    
    # Configuration
    API_URL = "http://localhost:5002"
    SESSION_ID = f"my_app_{int(time.time())}"
    
    try:
        print("🚀 Starting My RAG + LLM Client")
        print("=" * 50)
        
        # Step 1: Health Check
        print("🏥 Checking service health...")
        if not check_service_health(API_URL):
            print("❌ API service is not available!")
            return 1
        
        # Step 2: Initialize RAG (optional but recommended)
        print("\n🔄 Initializing RAG system...")
        initialize_rag_system(API_URL)
        
        # Step 3: Your application logic - send queries
        print("\n🤖 Starting queries...")
        
        user_questions = [
            "What is ITRI?",
            "Tell me about ITRI's research focus",
            "工研院的主要技術領域是什麼？"  # Traditional Chinese example
        ]
        
        for question in user_questions:
            print(f"\n📝 Question: {question}")
            response = stream_rag_llm_query(API_URL, question, SESSION_ID)
            
            if response:
                print(f"\n✅ Query completed successfully")
            else:
                print(f"\n❌ Query failed")
            
            time.sleep(1)  # Brief pause between queries
        
        print("\n✅ All queries completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
    finally:
        # Step 4: ALWAYS close connection before exit
        print(f"\n👋 Closing connection...")
        if close_connection(API_URL, SESSION_ID):
            print("✅ Connection closed successfully")
        else:
            print("⚠️ Connection close may have failed")
    
    return 0

if __name__ == "__main__":
    exit(main())
```

## 🔧 Session Management Best Practices

### 1. **Unique Session IDs**
```python
# Generate unique session ID for your application
SESSION_ID = f"my_app_{int(time.time())}"
# or
SESSION_ID = f"user_{user_id}_{int(time.time())}"
```

### 2. **Session History**
```python
# Chat history is automatically maintained per session
# Each query in the same session will have context from previous queries

# First query
stream_rag_llm_query(API_URL, "What is ITRI?", "session_123")

# Second query (will have context from first query)  
stream_rag_llm_query(API_URL, "Tell me more about its research", "session_123")
```

### 3. **Proper Cleanup**
```python
import atexit

# Register cleanup function to run on exit
def cleanup():
    close_connection(API_URL, SESSION_ID)

atexit.register(cleanup)

# Or use try/finally
try:
    # Your application logic
    pass
finally:
    close_connection(API_URL, SESSION_ID)
```

## 🎨 Server-Side Tone Conversion Features

### How It Works

The new server-side tone conversion integrates directly into the RAG + LLM pipeline:

1. **RAG Query Processing**: Your question is processed through the RAG system to find relevant context
2. **LLM Response Generation**: The LLM generates the initial response based on RAG context
3. **Automatic Tone Conversion**: If enabled, the server automatically converts the response tone using a secondary LLM
4. **Streaming Output**: The tone-converted response is streamed directly to your client

### Benefits of Server-Side Processing

- **Better Performance**: No need for separate client-side API calls
- **Simplified Code**: Single function call for RAG + LLM + tone conversion
- **Consistent Processing**: Server-side ensures consistent tone conversion across all clients
- **Reduced Network Traffic**: Only final tone-converted response is sent to client
- **Integrated Streaming**: Real-time streaming of tone-converted text

### Tone Conversion Options

```python
# Available tone styles (can be customized)
TONE_STYLES = [
    "child_friendly",    # Default: Encouraging, simple language for children
    "professional",      # Formal business communication style
    "casual",           # Relaxed, conversational tone
    "academic",         # Scholarly, research-oriented language
    "enthusiastic"      # Energetic, excited presentation
]

# Usage examples
response = stream_rag_llm_with_tone(API_URL, "What is ITRI?", SESSION_ID, "child_friendly")
response = stream_rag_llm_with_tone(API_URL, "Explain ITRI's research", SESSION_ID, "academic")
```

### Legacy Client-Side Functions

The original client-side tone conversion functions (`convert_tone` and `stream_convert_tone`) are still available for backward compatibility, but server-side conversion is recommended for new implementations.

## 🌐 Multi-language Support

The API service supports multiple languages. Response language depends on user input:

```python
# English query with tone conversion
response = stream_rag_llm_with_tone(API_URL, "What is ITRI?", SESSION_ID, "child_friendly")

# Traditional Chinese query with tone conversion  
response = stream_rag_llm_with_tone(API_URL, "工研院是什麼？", SESSION_ID, "child_friendly")

# Mixed language query with tone conversion
response = stream_rag_llm_with_tone(API_URL, "Please explain ITRI in Chinese", SESSION_ID, "child_friendly")

# Without tone conversion (original behavior)
response = stream_rag_llm_query(API_URL, "What is ITRI?", SESSION_ID)
```

## ⚡ Performance Tips

### 1. **Reuse Sessions**
```python
# Good: Reuse session for related queries
SESSION_ID = "conversation_001"
stream_rag_llm_query(API_URL, "What is ITRI?", SESSION_ID)
stream_rag_llm_query(API_URL, "What are its research areas?", SESSION_ID)
close_connection(API_URL, SESSION_ID)
```

### 2. **Initialize and Warmup Once**
```python
# Initialize RAG system once at application start
initialize_rag_system(API_URL)

# Warmup models for better performance (NEW!)
warmup_models(API_URL)
warmup_tone_conversion(API_URL)  # For tone conversion

# Then send multiple queries...
```

### 3. **Choose Tone Conversion Wisely**
```python
# Use tone conversion for user-facing responses
user_response = stream_rag_llm_with_tone(API_URL, question, SESSION_ID, "child_friendly")

# Skip tone conversion for internal processing or when speed is critical
internal_response = stream_rag_llm_query(API_URL, question, SESSION_ID, enable_tone_conversion=False)

# Use different tones for different contexts
academic_response = stream_rag_llm_with_tone(API_URL, question, SESSION_ID, "academic")
casual_response = stream_rag_llm_with_tone(API_URL, question, SESSION_ID, "casual")
```

### 4. **Handle Errors Gracefully**
```python
def safe_query_with_tone(question, session_id, tone_style="child_friendly"):
    try:
        return stream_rag_llm_with_tone(API_URL, question, session_id, tone_style)
    except Exception as e:
        print(f"Query failed: {e}")
        return None

# Always attempt to close connection even if queries fail
try:
    response = safe_query_with_tone("My question", SESSION_ID)
finally:
    close_connection(API_URL, SESSION_ID)
```

## 🛠️ Integration Examples

### Command Line Tool
```python
#!/usr/bin/env python3
import sys
from client_utils import *

def cli_chat():
    API_URL = "http://localhost:5002" 
    SESSION_ID = f"cli_{int(time.time())}"
    
    if not check_service_health(API_URL):
        print("Service not available!")
        return
    
    initialize_rag_system(API_URL)
    
    try:
        while True:
            question = input("\n🤖 Ask a question (or 'quit' to exit): ")
            if question.lower() == 'quit':
                break
            
            stream_rag_llm_query(API_URL, question, SESSION_ID)
    finally:
        close_connection(API_URL, SESSION_ID)

if __name__ == "__main__":
    cli_chat()
```

### Web Application Backend
```python
from flask import Flask, request, jsonify
from client_utils import *

app = Flask(__name__)
API_URL = "http://localhost:5002"

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    session_id = data.get('session_id', 'web_default')
    
    response = stream_rag_llm_query(API_URL, question, session_id)
    return jsonify({'response': response})

@app.route('/close/<session_id>', methods=['POST'])  
def close_session(session_id):
    success = close_connection(API_URL, session_id)
    return jsonify({'success': success})
```

## ❗ Important Notes

### 🔥 Always Close Connections
```python
# CRITICAL: Always call close_connection() before your program terminates
# This prevents memory leaks on the server and ensures proper cleanup

# Method 1: try/finally
try:
    # Your application logic
    pass
finally:
    close_connection(API_URL, SESSION_ID)

# Method 2: atexit handler
import atexit
atexit.register(lambda: close_connection(API_URL, SESSION_ID))
```

### 🌍 Language Handling
- **Input Language**: Use the language you want the response in
- **Default**: Service matches user input language
- **Traditional Chinese**: Use `"請用繁體中文回答"` in your query
- **One Sentence Limit**: Server is configured to respond in single sentences

### 🔗 Service Dependencies
Make sure the API service is running before using client utilities:

```bash
# Start the API service in another terminal
cd /workspace/API
python rag_llm_api.py --auto-init

# Then run your client application
python your_client_app.py
```

## 🐛 Troubleshooting

### Common Client Issues

1. **Connection Refused**:
   ```python
   # Always check health first
   if not check_service_health(API_URL):
       print("Start the API service first!")
   ```

2. **Empty Responses**:
   ```python
   # Initialize RAG system
   initialize_rag_system(API_URL)
   ```

3. **Session Cleanup**:
   ```python
   # Always close connections
   close_connection(API_URL, SESSION_ID)
   ```

### Debug Mode
```python
# Add debug information to your client
import logging
logging.basicConfig(level=logging.DEBUG)

# The client utilities will show more detailed error information
```

## 📋 Complete Workflow Checklist

✅ **Before Starting**:
- [ ] API service is running (`python rag_llm_api.py --auto-init`)
- [ ] Import client utilities (including new tone conversion functions)
- [ ] Generate unique session ID
- [ ] Decide on tone conversion strategy

✅ **During Operation**:
- [ ] Check service health
- [ ] Initialize RAG system (once)
- [ ] **NEW**: Warmup tone conversion models (optional, for performance)
- [ ] Send queries with same session ID
- [ ] **NEW**: Use `stream_rag_llm_with_tone()` for tone-converted responses
- [ ] Handle errors gracefully

✅ **Before Termination**:
- [ ] Call `close_connection()` 
- [ ] Verify cleanup success
- [ ] Exit cleanly

✅ **NEW: Tone Conversion Checklist**:
- [ ] Choose appropriate tone style for your use case
- [ ] Consider performance impact (tone conversion adds processing time)
- [ ] Test with your target language (English/Traditional Chinese)
- [ ] Use warmup for production applications

---

## 🎉 You're Ready!

With the enhanced `client_utils.py`, you now have everything needed to build powerful applications on top of the RAG + LLM API service with integrated server-side tone conversion. The utilities handle all the complex streaming, session management, tone conversion processing, and cleanup for you - just focus on your application logic!

### 🆕 What's New:
- **Server-side tone conversion** for better performance and simplified code
- **Streaming tone-converted responses** for real-time user experience
- **Multiple tone styles** for different contexts and audiences
- **Integrated warmup functions** for optimal performance
- **Backward compatibility** with existing client code

### 🚀 Next Steps:
1. Try the enhanced `api_client_example.py` to see server-side tone conversion in action
2. Integrate `stream_rag_llm_with_tone()` into your applications
3. Experiment with different tone styles for your use cases
4. Use warmup functions in production for best performance

<<<<<<< Current (Your changes)
**Happy coding! 🚀**
=======
**Happy coding with enhanced tone conversion! 🎨🚀**
>>>>>>> Incoming (Background Agent changes)
