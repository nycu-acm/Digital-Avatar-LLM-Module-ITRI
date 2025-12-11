#!/usr/bin/env python3
"""
Example client for RAG + LLM API Service

This demonstrates how to use the API service to get streaming responses
from the RAG + LLM system.
"""

import requests
import json
import time
from client_utils import stream_rag_llm_query, check_service_health, initialize_rag_system, warmup_models, close_connection, convert_tone, stream_convert_tone

def main():
    """Example usage of the RAG + LLM API client"""
    
    # Configuration
    API_URL = "http://localhost:5002"
    SESSION_ID = f"time_stamp_{int(time.time())}"
    # Available tone options: "child_friendly", "elder_friendly", "professional_friendly", "casual_friendly"
    # TONE_STYLE1 = "professional_friendly"  # Convert to professional-friendly speaking style with formal words
    # TONE_STYLE2 = "casual_friendly"  # Convert to casual-friendly speaking style with relaxed words
    TONE_STYLE1 = "child_friendly"  # Convert to child-friendly speaking style with encouraging words
    TONE_STYLE2 = "elder_friendly"  # Convert to elder-friendly speaking style with respectful words

    print("🤖 RAG + LLM API Client Example")
    print("=" * 50)
    
    # Check service health
    if not check_service_health(API_URL):
        print("❌ Service is not healthy. Make sure the API service is running.")
        return 1
    
    print()
    
    # Initialize RAG system if needed
    print("🔄 Checking RAG system...")
    if not initialize_rag_system(API_URL):
        print("⚠️ RAG initialization may have failed. Continuing anyway...")
    
    print()
    
    # Warm up models for better performance
    print("🔥 Warming up models...")
    warmup_result = warmup_models(API_URL)
    if warmup_result and warmup_result.get('overall_success'):
        print("✅ Models warmed up successfully!")
    else:
        print("⚠️ Model warmup may have failed. Continuing anyway...")
    
    print()
    
    # Example queries
    example_queries = [
        # "What is ITRI?",
        # "Tell me about ITRI's research areas",
        # "What services does ITRI provide?",
        # "工研院是什麼？",  # Chinese example
        # "who is the director of ITRI?",
        # "who is the president of ITRI?",
        # "What is ITRI?",
        # "工研院是什麼？",
        # "What research areas does ITRI focus on?",
        # "工研院有什麼研究領域？",
        # "When was ITRI established?",
        "工研院成立於什麼時候？",
        # "What are ITRI's main technological achievements?",
        "工研院有哪些重要的技術發展？",
        # "How does ITRI contribute to Taiwan's industrial development?",
        # "工研院如何貢獻台灣的產業發展？",
        # "What is ITRI's organizational structure?",
        # "工研院的組織架構如何？",
        # "Who is the current president of ITRI?",
        "工研院院長是誰？",
        # "How does ITRI support talent development?",
        "工研院如何推動產業升級？",
        # "What are ITRI's key innovation programs?",
        "工研院有哪些重要成就？",
        # "How does ITRI collaborate with industry partners?",
        "工研院與產業界如何合作？",
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n📝 Example {i}:")
        response = stream_rag_llm_query(API_URL, query, SESSION_ID)
        
        if response:
            # print(f"\n📋 Final Response: {response}")
            # Streaming tone conversion via secondary agent
            print()
            converted = stream_convert_tone(response, tone=TONE_STYLE1)
            # converted = convert_tone(response, tone=TONE_STYLE)
            if converted:
                print(f"\n✅ Tone-Converted ({TONE_STYLE1}) complete.")
            else:
                print("⚠️ Tone conversion skipped/failed.")
            # print()
            converted = stream_convert_tone(response, tone=TONE_STYLE2)
            if converted:
                print(f"\n✅ Tone-Converted ({TONE_STYLE2}) complete.")
            else:
                print("⚠️ Tone conversion skipped/failed.")
        else:
            print("❌ Query failed")
        
        print("\n" + "=" * 50)
        
        # Wait a bit between queries
        if i < len(example_queries):
            time.sleep(2)
    
    print("\n✅ Demo complete!")
    
    # Elegant connection close before program termination
    print("\n👋 Closing connection...")
    if close_connection(API_URL, SESSION_ID):
        print("✅ Connection closed successfully")
    else:
        print("⚠️ Connection close may have failed")

if __name__ == "__main__":
    exit(main())