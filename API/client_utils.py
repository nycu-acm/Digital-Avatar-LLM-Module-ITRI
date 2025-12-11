import requests
import json
import time
import os
import sys
# Add parent directories to path to import RAG components
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import LLM_MODEL_NAME, CHROMA_DB_PATH

# Import tone system prompts
from tone_system_prompts import get_tone_system_prompt

def convert_tone(text: str, tone: str = "child_friendly", model_url: str = "http://localhost:11435/api/chat", model_name: str = LLM_MODEL_NAME):
    """
    Convert the tone/style of a given text using a secondary agent (LLM rewriter).

    Args:
        text: The original text to be rewritten.
        tone: Target tone/style (e.g., "child_friendly", "elder_friendly").
        model_url: The chat API endpoint of the local LLM service.
        model_name: The model identifier to use for rewriting.

    Returns:
        str | None: The rewritten text if successful, otherwise None.
    """
    try:
        if not text:
            return text

        # Detect input language
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        target_lang = "Traditional Chinese (繁體中文)" if has_chinese else "English"
        
        # Get appropriate system prompt based on tone
        system_prompt = get_tone_system_prompt(tone, target_lang)
        
        # Create tone-specific user instruction
        tone_descriptions = {
            "child_friendly": "children",
            "elder_friendly": "elderly people"
        }
        target_audience = tone_descriptions.get(tone, tone.replace("_", " "))

        user_instruction = (
            f"Rewrite this text to speak to {target_audience} in {target_lang}:\n"
            f"---\n{text}\n---"
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instruction},
            ],
            "stream": False,
            "options": {"temperature": 0.3}
        }

        resp = requests.post(model_url, json=payload, timeout=None)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content", "").strip()
        # Fallback common formats
        if isinstance(data, dict) and "response" in data:
            return str(data.get("response", "")).strip()
        return None
    except Exception as e:
        print(f"❌ Tone conversion failed: {e}")
        return None

def stream_convert_tone(text: str, tone: str = "child_friendly", model_url: str = "http://localhost:11435/api/chat", model_name: str = LLM_MODEL_NAME):
    """
    Stream the tone conversion so users can see the rewritten text as it is generated.

    Args:
        text: The text to convert
        tone: Target tone/style (e.g., "child_friendly", "elder_friendly")
        model_url: The chat API endpoint of the local LLM service
        model_name: The model identifier to use for rewriting

    Prints chunks as they arrive and returns the final converted string.
    """
    try:
        if not text:
            return text

        # Detect input language
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        target_lang = "Traditional Chinese (繁體中文)" if has_chinese else "English"

        # Get appropriate system prompt based on tone
        system_prompt = get_tone_system_prompt(tone, target_lang)
        
        # Create tone-specific user instruction
        tone_descriptions = {
            "child_friendly": "children",
            "elder_friendly": "elderly people"
        }
        target_audience = tone_descriptions.get(tone, tone.replace("_", " "))

        user_instruction = (
            f"Rewrite this text to speak to {target_audience} in {target_lang}:\n"
            f"---\n{text}\n---"
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instruction},
            ],
            "stream": True,
            "options": {"temperature": 0.3}
        }

        print(f"🎨 Streaming Tone-Converted ({tone}):")
        print("-" * 50)

        with requests.post(model_url, json=payload, stream=True) as response:
            response.raise_for_status()
            converted = ""
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except Exception:
                    continue
                message = chunk.get("message", {})
                delta = message.get("content")
                if delta:
                    converted += delta
                    print(delta, end="", flush=True)
                if chunk.get("done"):
                    break
        print()  # newline after stream
        return converted.strip()
    except Exception as e:
        print(f"❌ Streaming tone conversion failed: {e}")
        return None

def stream_rag_llm_query(api_url: str, text_user_msg: str, session_id: str):
    """
    Stream a query to the RAG + LLM API service
    
    Args:
        api_url: Base URL of the API service (e.g., "http://localhost:5002")
        text_user_msg: The user's text message/question
        session_id: Optional session ID for maintaining chat history
    
    Returns:
        Generator yielding streaming text chunks
    """
    
    endpoint = f"{api_url}/api/rag-llm/query"
    payload = {
        "text_user_msg": text_user_msg,
        "session_id": session_id,
        "include_history": True
    }
    
    print(f"🤖 Sending query: {text_user_msg}")
    print("📡 Streaming response:")
    print("-" * 50)
    
    try:
        with requests.post(endpoint, json=payload, stream=True) as response:
            response.raise_for_status()
            
            accumulated_response = ""
            
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    # Check for END_FLAG
                    if chunk == "E" and accumulated_response.endswith("END_FLA"):
                        # Complete END_FLAG received
                        print("\n" + "=" * 50)
                        print("✅ Response complete (END_FLAG received)")
                        break
                    elif "END_FLAG" in chunk:
                        # Handle case where END_FLAG comes in one chunk
                        text_part = chunk.replace("END_FLAG", "")
                        if text_part:
                            accumulated_response += text_part
                            print(text_part, end="", flush=True)
                        print("\n" + "=" * 50)
                        print("✅ Response complete (END_FLAG received)")
                        break
                    else:
                        accumulated_response += chunk
                        print(chunk, end="", flush=True)
            
            return accumulated_response
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def check_service_health(api_url: str):
    """Check if the API service is healthy"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        print(f"🔍 Service Health Check:")
        print(f"  Status: {health_data.get('status')}")
        print(f"  RAG Initialized: {health_data.get('rag_initialized')}")
        print(f"  Timestamp: {health_data.get('timestamp')}")
        
        return health_data.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def initialize_rag_system(api_url: str):
    """Initialize the RAG system via API"""
    try:
        response = requests.post(f"{api_url}/api/rag-llm/init", timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"🔄 RAG Initialization:")
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        return False

def warmup_models(api_url: str):
    """
    Warmup the embedding model and LLM to reduce first-request latency
    
    Args:
        api_url: Base URL of the API service (e.g., "http://localhost:5002")
    
    Returns:
        dict: Warmup results with detailed timing information
    """
    try:
        endpoint = f"{api_url}/api/rag-llm/warmup"
        
        print(f"🔥 Warming up models...")
        start_time = time.time()
        
        response = requests.post(endpoint, timeout=None)  # Generous timeout for warmup
        response.raise_for_status()
        result = response.json()
        
        total_time = time.time() - start_time
        
        print(f"🔥 Model Warmup Results:")
        print(f"  Overall Success: {result.get('overall_success')}")
        print(f"  Total Time: {total_time:.2f}s")
        
        # Embedding model results
        embedding_result = result.get('embedding_model', {})
        print(f"  📚 Embedding Model:")
        print(f"    Status: {embedding_result.get('status')}")
        print(f"    Message: {embedding_result.get('message')}")
        print(f"    Time: {embedding_result.get('time_ms', 0):.0f}ms")
        if 'results_found' in embedding_result:
            print(f"    Results Found: {embedding_result.get('results_found')}")
        
        # LLM results
        llm_result = result.get('llm_model', {})
        print(f"  🤖 LLM Model:")
        print(f"    Status: {llm_result.get('status')}")
        print(f"    Message: {llm_result.get('message')}")
        print(f"    Time: {llm_result.get('time_ms', 0):.0f}ms")
        if 'test_response' in llm_result:
            print(f"    Test Response: '{llm_result.get('test_response')}'")
        
        return result
        
    except requests.exceptions.Timeout:
        print(f"❌ Model warmup timed out (60s)")
        return None
    except Exception as e:
        print(f"❌ Model warmup failed: {e}")
        return None

def close_connection(api_url: str, session_id: str):
    """
    Elegant connection close function
    
    Client calls this function before program termination.
    Server will clear the history of the client based on the chat_session_id.
    
    Args:
        api_url: Base URL of the API service (e.g., "http://localhost:5002")
        session_id: Session ID to close and clean up
    
    Returns:
        bool: True if connection was closed successfully, False otherwise
    """
    try:
        endpoint = f"{api_url}/api/rag-llm/close"
        payload = {
            "session_id": session_id
        }
        
        print(f"👋 Closing connection for session: {session_id}")
        
        response = requests.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Connection Close:")
        print(f"  Session ID: {result.get('session_id')}")
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        print(f"  Session Existed: {result.get('session_existed')}")
        print(f"  Messages Cleared: {result.get('messages_cleared')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Connection close failed: {e}")
        return False
