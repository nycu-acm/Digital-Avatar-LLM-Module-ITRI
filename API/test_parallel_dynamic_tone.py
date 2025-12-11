#!/usr/bin/env python3
"""
Test script for Parallel Dynamic Tone Selection API

This script demonstrates the new parallel architecture where:
1. Visual context is fetched from the Vision Context API (VLM server)
2. QA response generation happens in parallel with visual context fetching
3. Both results are combined for dynamic tone selection

Usage:
1. Start both servers:
   - python vision_api_multi_session.py  (Vision Context API)
   - python rag_llm_api.py --auto-init --user-description-server http://localhost:5004
2. Run this test: python test_parallel_dynamic_tone.py
"""

import requests
import json
import time

# API Configuration
RAG_API_URL = "http://localhost:5002"
VISION_API_URL = "http://localhost:5004"
RAG_ENDPOINT = "/api/rag-llm/query"

def test_parallel_dynamic_tone():
    """Test the parallel dynamic tone selection functionality"""
    
    print("🧪 Testing Parallel Dynamic Tone Selection API")
    print("=" * 60)
    
    # Test cases - note that user_description is NOT provided by client
    # The server will fetch it automatically from the description server
    test_cases = [
        {
            "name": "Test 1 - ITRI Question (English)",
            "text_user_msg": "What is ITRI?",
        },
        {
            "name": "Test 2 - ITRI Question (Chinese)",
            "text_user_msg": "工研院是什麼？",
        },
        {
            "name": "Test 3 - Research Question",
            "text_user_msg": "What kind of research does ITRI do?",
        },
        {
            "name": "Test 4 - Technology Question",
            "text_user_msg": "工研院的技術發展如何？",
        },
        {
            "name": "Test 5 - History Question",
            "text_user_msg": "Tell me about ITRI's history",
        },
    ]
    
    session_id = f"test_session_{int(time.time())}"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 {test_case['name']}")
        print(f"❓ Question: '{test_case['text_user_msg']}'")
        print(f"📸 Visual context will be fetched from Vision API automatically")
        
        # Prepare request payload (NO user_description provided)
        payload = {
            "text_user_msg": test_case["text_user_msg"],
            "session_id": f"{session_id}_{i}",
            "convert_tone": True,
            "include_history": True
        }
        
        try:
            # Make API request
            print(f"🔄 Sending request (parallel processing will occur)...")
            start_time = time.time()
            
            response = requests.post(
                f"{RAG_API_URL}{RAG_ENDPOINT}", 
                json=payload, 
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                print("✅ Request successful, collecting streaming response...")
                
                # Collect streaming response
                full_response = ""
                chunk_count = 0
                first_chunk_time = None
                
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            ttfb = (first_chunk_time - start_time) * 1000
                            print(f"⚡ Time to first byte: {ttfb:.0f}ms")
                        
                        if line == "END_FLAG":
                            end_time = time.time()
                            total_time = (end_time - start_time) * 1000
                            print(f"🏁 Stream completed in {total_time:.0f}ms")
                            break
                        elif line.startswith("ERROR:"):
                            print(f"❌ Error in response: {line}")
                            break
                        else:
                            full_response += line
                            chunk_count += 1
                
                print(f"📊 Response collected: {len(full_response)} chars in {chunk_count} chunks")
                print(f"💬 Response:")
                print(f"   {full_response}")
                
                # Check if response contains tone-specific expressions
                has_tone_markers = "(" in full_response or "呢" in full_response or "啊" in full_response or "喔" in full_response
                print(f"🎨 Tone markers detected: {'✅ Yes' if has_tone_markers else '❌ No'}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("-" * 60)
        
        # Wait between tests
        if i < len(test_cases):
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"🎉 Parallel Dynamic Tone Selection Testing Complete!")
    print("\n💡 Architecture Overview:")
    print("1. Client sends request WITHOUT user_description")
    print("2. Server does TWO things in PARALLEL:")
    print("   a) Fetches visual context from Vision Context API")
    print("   b) Generates QA response from RAG+LLM")
    print("3. After both complete, server determines tone and converts")
    print("4. Client receives streaming tone-converted response")
    print("\n🔧 Server Architecture:")
    print("- Vision Context API Server: Port 5004")
    print("- RAG LLM API Server: Port 5002")

def test_vision_api_server():
    """Test if the Vision Context API server is running"""
    try:
        response = requests.get(f"{VISION_API_URL}/sessions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vision Context API Server: Active")
            print(f"👥 Active Sessions: {data.get('total_sessions', 0)}")
            return True
        else:
            print(f"❌ Vision API server check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Vision Context API server: {e}")
        print("🔧 Make sure the Vision API server is running:")
        print("   python vision_api_multi_session.py")
        return False

def test_rag_api_server():
    """Test if the RAG API server is running"""
    try:
        response = requests.get(f"{RAG_API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG API Server: {data['status']}")
            print(f"🤖 RAG Initialized: {data['rag_initialized']}")
            return True
        else:
            print(f"❌ RAG API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to RAG API: {e}")
        print("🔧 Make sure the API service is running:")
        print("   python rag_llm_api.py --auto-init")
        return False

def main():
    """Main test execution"""
    print("🚀 Parallel Dynamic Tone Selection API Test")
    print("=" * 60)
    
    # Check if both servers are running
    print("\n🔍 Checking server status...")
    vision_api_ok = test_vision_api_server()
    rag_api_ok = test_rag_api_server()
    
    if not vision_api_ok or not rag_api_ok:
        print("\n❌ One or more servers are not running!")
        print("\n💡 Required servers:")
        print("   1. Vision Context API Server: python vision_api_multi_session.py (port 5004)")
        print("      OR Vision API Simulator: python random_user_description_server.py --port 5003")
        print("   2. RAG LLM API Server: python rag_llm_api.py --auto-init --user-description-server http://localhost:5004")
        print("      (Use --user-description-server http://localhost:5003 for simulator)")
        return 1
    
    # Wait a moment
    print("\n⏳ Starting tests in 3 seconds...")
    time.sleep(3)
    
    # Run the tests
    test_parallel_dynamic_tone()
    
    return 0

if __name__ == "__main__":
    exit(main())



