#!/usr/bin/env python3
"""
Example client demonstrating the new tone conversion features of the RAG + LLM API Service

This example shows how to use the three different endpoints:
1. /api/rag-llm/convert-tone - Standalone tone conversion
2. /api/rag-llm/query-with-tone - Combined RAG+LLM query with automatic tone conversion
3. /api/rag-llm/query - Original query endpoint with optional tone conversion
"""

import requests
import json
import time
import uuid

# API Configuration
API_BASE_URL = "http://localhost:5002"
SESSION_ID = f"tone_demo_{uuid.uuid4().hex[:8]}"

# Colors for console output
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

def check_service_health():
    """Check if the API service is healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        print(f"{GREEN}✅ Service Health Check:{RESET}")
        print(f"  Status: {health_data.get('status')}")
        print(f"  RAG Initialized: {health_data.get('rag_initialized')}")
        print()
        
        return health_data.get('status') == 'healthy'
        
    except Exception as e:
        print(f"{RED}❌ Health check failed: {e}{RESET}")
        return False

def stream_response(response):
    """Helper function to stream and display response content"""
    accumulated_response = ""
    
    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            # Check for END_FLAG
            if chunk == "E" and accumulated_response.endswith("END_FLA"):
                # Complete END_FLAG received
                print(f"\n{GREEN}✅ Response complete{RESET}")
                break
            elif "END_FLAG" in chunk:
                # Handle case where END_FLAG comes in one chunk
                text_part = chunk.replace("END_FLAG", "")
                if text_part:
                    accumulated_response += text_part
                    print(text_part, end="", flush=True)
                print(f"\n{GREEN}✅ Response complete{RESET}")
                break
            else:
                accumulated_response += chunk
                print(chunk, end="", flush=True)
    
    return accumulated_response

def demo_standalone_tone_conversion():
    """Demonstrate standalone tone conversion endpoint"""
    print(f"{BLUE}🎨 Demo 1: Standalone Tone Conversion{RESET}")
    print("=" * 50)
    
    # Example texts to convert
    test_texts = [
        "ITRI was founded in 1973 and focuses on applied research in various technological fields.",
        "工研院成立於1973年，專注於各種技術領域的應用研究。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{YELLOW}Test {i}: Converting text to child-friendly tone{RESET}")
        print(f"Original: {text}")
        print(f"Converted: ", end="")
        
        payload = {
            "text": text,
            "tone": "child_friendly",
            "stream": True
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/rag-llm/convert-tone", 
                                   json=payload, stream=True)
            response.raise_for_status()
            
            converted_text = stream_response(response)
            print()
            
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
    
    print()

def demo_query_with_automatic_tone_conversion():
    """Demonstrate combined query + tone conversion endpoint"""
    print(f"{BLUE}🤖🎨 Demo 2: Query with Automatic Tone Conversion{RESET}")
    print("=" * 50)
    
    questions = [
        "What is ITRI?",
        "工研院是什麼？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{YELLOW}Question {i}: {question}{RESET}")
        print(f"Answer (child-friendly): ", end="")
        
        payload = {
            "text_user_msg": question,
            "session_id": SESSION_ID,
            "include_history": True,
            "tone": "child_friendly",
            "convert_tone": True
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/rag-llm/query-with-tone", 
                                   json=payload, stream=True)
            response.raise_for_status()
            
            answer = stream_response(response)
            print()
            
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
    
    print()

def demo_original_query_with_optional_tone():
    """Demonstrate original query endpoint with optional tone conversion"""
    print(f"{BLUE}🤖 Demo 3: Original Query Endpoint with Optional Tone{RESET}")
    print("=" * 50)
    
    question = "Tell me about ITRI's research areas."
    
    # First, without tone conversion
    print(f"\n{YELLOW}Question: {question}{RESET}")
    print(f"Answer (normal): ", end="")
    
    payload = {
        "text_user_msg": question,
        "session_id": SESSION_ID,
        "include_history": True,
        "convert_tone": False
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/rag-llm/query", 
                               json=payload, stream=True)
        response.raise_for_status()
        
        normal_answer = stream_response(response)
        print()
        
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    # Then, with tone conversion
    print(f"\n{YELLOW}Same question with tone conversion enabled:{RESET}")
    print(f"Answer (child-friendly): ", end="")
    
    payload["convert_tone"] = True
    payload["tone"] = "child_friendly"
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/rag-llm/query", 
                               json=payload, stream=True)
        response.raise_for_status()
        
        tone_answer = stream_response(response)
        print()
        
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    print()

def demo_non_streaming_tone_conversion():
    """Demonstrate non-streaming tone conversion"""
    print(f"{BLUE}🎨 Demo 4: Non-Streaming Tone Conversion{RESET}")
    print("=" * 50)
    
    text = "ITRI develops advanced technologies for industry transformation."
    
    print(f"\n{YELLOW}Converting (non-streaming): {text}{RESET}")
    
    payload = {
        "text": text,
        "tone": "child_friendly",
        "stream": False  # Non-streaming
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/rag-llm/convert-tone", 
                               json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            print(f"Original: {result.get('original_text')}")
            print(f"Converted: {result.get('converted_text')}")
            print(f"Tone: {result.get('tone')}")
        else:
            print(f"{RED}❌ Conversion failed{RESET}")
            
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    print()

def close_session():
    """Close the demo session"""
    print(f"{BLUE}👋 Closing demo session{RESET}")
    
    payload = {
        "session_id": SESSION_ID
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/rag-llm/close", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Session closed: {result.get('message')}")
        print(f"Messages cleared: {result.get('messages_cleared')}")
        
    except Exception as e:
        print(f"{RED}❌ Error closing session: {e}{RESET}")

def main():
    """Main demo function"""
    print(f"{GREEN}🚀 RAG + LLM API Tone Conversion Demo{RESET}")
    print("=" * 70)
    print(f"Session ID: {SESSION_ID}")
    print(f"API URL: {API_BASE_URL}")
    print()
    
    # Check service health
    if not check_service_health():
        print(f"{RED}❌ Service is not healthy. Please start the API service first.{RESET}")
        return 1
    
    try:
        # Run all demos
        demo_standalone_tone_conversion()
        demo_query_with_automatic_tone_conversion()
        demo_original_query_with_optional_tone()
        demo_non_streaming_tone_conversion()
        
        print(f"{GREEN}🎉 All demos completed successfully!{RESET}")
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}🛑 Demo interrupted by user{RESET}")
    
    finally:
        # Clean up session
        close_session()
    
    return 0

if __name__ == "__main__":
    exit(main())
