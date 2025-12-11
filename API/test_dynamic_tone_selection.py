#!/usr/bin/env python3
"""
Test script for VLM-based Dynamic Tone Selection API

This script demonstrates the new dynamic tone selection feature where the API
automatically determines the appropriate tone based on visual descriptions from a VLM.

The user_description parameter now expects visual descriptions like:
- "a young boy wearing glasses, and is smiling"
- "an elderly woman with gray hair sitting in a chair"

Usage:
1. Start the RAG LLM API service: python rag_llm_api.py --auto-init
2. Run this test: python test_dynamic_tone_selection.py
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:5002"
API_ENDPOINT = "/api/rag-llm/query"

def test_dynamic_tone_selection():
    """Test the dynamic tone selection functionality"""
    
    print("🧪 Testing Dynamic Tone Selection API")
    print("=" * 50)
    
    # Test cases with VLM visual descriptions for all 4 tones
    test_cases = [
        {
            "name": "Young Boy Test",
            "user_description": "a young boy wearing glasses, and is smiling",
            "text_user_msg": "What is ITRI?",
            "expected_tone": "child_friendly"
        },
        {
            "name": "Young Boy Test",
            "user_description": "a young boy wearing glasses, and is smiling",
            "text_user_msg": "哇！這裡看起來好酷喔！",
            "expected_tone": "child_friendly"
        },
        {
            "name": "Little Girl Test", 
            "user_description": "a little girl with pigtails holding a backpack",
            "text_user_msg": "工研院是什麼？",
            "expected_tone": "child_friendly"
        },
        {
            "name": "Teenager Test",
            "user_description": "a teenager in school uniform looking curious",
            "text_user_msg": "What kind of research does ITRI do?",
            "expected_tone": "child_friendly"
        },
        {
            "name": "Elderly Man Test",
            "user_description": "an elderly man with gray hair and wrinkles, wearing a cardigan",
            "text_user_msg": "工研院做什麼研究？",
            "expected_tone": "elder_friendly"
        },
        {
            "name": "Senior Woman Test",
            "user_description": "an old woman with white hair using a walking stick",
            "text_user_msg": "Tell me about ITRI's history",
            "expected_tone": "elder_friendly"
        },
        {
            "name": "Chinese Elder Test",
            "user_description": "一位白髮蒼蒼坐在輪椅上的老奶奶",
            "text_user_msg": "工研院的歷史如何？",
            "expected_tone": "elder_friendly"
        },
        {
            "name": "Business Professional Test",
            "user_description": "a middle-aged person in business suit standing confidently in an office",
            "text_user_msg": "What are ITRI's main achievements?",
            "expected_tone": "professional_friendly"
        },
        {
            "name": "Formal Executive Test",
            "user_description": "a man in formal attire holding documents in a conference room",
            "text_user_msg": "Tell me about ITRI's research capabilities",
            "expected_tone": "professional_friendly"
        },
        {
            "name": "Chinese Business Person Test",
            "user_description": "穿西裝的商務人士站在辦公室裡",
            "text_user_msg": "工研院的技術發展如何？",
            "expected_tone": "professional_friendly"
        },
        {
            "name": "Casual Adult Test",
            "user_description": "a person wearing jeans and t-shirt sitting relaxed",
            "text_user_msg": "Tell me about ITRI's technology",
            "expected_tone": "casual_friendly"
        },
        {
            "name": "Home Setting Test",
            "user_description": "a woman wearing casual clothes at home on a couch",
            "text_user_msg": "What does ITRI do?",
            "expected_tone": "casual_friendly"
        },
        {
            "name": "Chinese Casual Test",
            "user_description": "穿便服的中年人在家裡",
            "text_user_msg": "工研院有什麼特色？",
            "expected_tone": "casual_friendly"
        },
        {
            "name": "Unclear Description Test",
            "user_description": "a person standing",
            "text_user_msg": "Tell me about ITRI's innovations",
            "expected_tone": "casual_friendly"  # Default when unclear
        },
        {
            "name": "Empty Description Test",
            "user_description": "",  # Empty VLM description
            "text_user_msg": "Tell me about ITRI's achievements",
            "expected_tone": "casual_friendly"  # Default fallback
        }
    ]
    
    session_id = f"test_session_{int(time.time())}"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"👁️ VLM Description: '{test_case['user_description']}'")
        print(f"❓ Question: '{test_case['text_user_msg']}'")
        print(f"🎯 Expected Tone: {test_case['expected_tone']}")
        
        # Prepare request payload
        payload = {
            "text_user_msg": test_case["text_user_msg"],
            "session_id": f"{session_id}_{i}",
            "user_description": test_case["user_description"],
            "convert_tone": True,
            "include_history": False
        }
        
        try:
            # Make API request
            print("🔄 Sending request...")
            response = requests.post(
                f"{API_BASE_URL}{API_ENDPOINT}", 
                json=payload, 
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                print("✅ Request successful, collecting streaming response...")
                
                # Collect streaming response
                full_response = ""
                chunk_count = 0
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line == "END_FLAG":
                            print("🏁 Stream completed")
                            break
                        elif line.startswith("ERROR:"):
                            print(f"❌ Error in response: {line}")
                            break
                        else:
                            full_response += line
                            chunk_count += 1
                
                print(f"📊 Response collected: {len(full_response)} chars in {chunk_count} chunks")
                print(f"💬 Response preview: {full_response[:200]}...")
                
                # Check if response contains tone-specific expressions
                has_tone_markers = "()" in full_response or "呢" in full_response or "啊" in full_response
                print(f"🎨 Tone markers detected: {'✅' if has_tone_markers else '❌'}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("-" * 30)
        
        # Wait between tests to avoid overwhelming the API
        if i < len(test_cases):
            time.sleep(2)
    
    print(f"\n🎉 VLM-based Dynamic Tone Selection Testing Complete!")
    print("Check the console output from the API service to see tone selection logs.")
    print("\n💡 Integration Notes:")
    print("- Connect your VLM to generate user_description from camera input")
    print("- Pass VLM descriptions like 'a young boy wearing glasses' to the API")
    print("- The system will automatically select from 4 tones based on visual cues:")
    print("  • child_friendly: For children and teenagers")
    print("  • elder_friendly: For elderly users (65+)")
    print("  • professional_friendly: For business/formal contexts")
    print("  • casual_friendly: For general adults (DEFAULT)")

def test_health_check():
    """Test if the API service is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health Check: {data['status']}")
            print(f"🤖 RAG Initialized: {data['rag_initialized']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("🔧 Make sure the API service is running:")
        print("   python rag_llm_api.py --auto-init")
        return False

def main():
    """Main test execution"""
    print("🚀 VLM-based Dynamic Tone Selection API Test")
    print("=" * 50)
    
    # Check if API is running
    if not test_health_check():
        return 1
    
    # Wait a moment
    print("\n⏳ Starting tests in 3 seconds...")
    time.sleep(3)
    
    # Run the tests
    test_dynamic_tone_selection()
    
    return 0

if __name__ == "__main__":
    exit(main())
