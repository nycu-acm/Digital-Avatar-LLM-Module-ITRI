#!/usr/bin/env python3
"""
Test script for Model Warmup Server

This script tests the warmup server functionality without running the full service.
"""

import time
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from client_utils import check_service_health, warmup_models

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def test_warmup_server():
    """Test the warmup server components"""
    
    API_URL = "http://localhost:5002"
    
    print(f"{BLUE}🧪 Testing Model Warmup Server Components{RESET}")
    print("=" * 50)
    
    # Test 1: Service Health Check
    print(f"\n{BLUE}Test 1: API Service Health Check{RESET}")
    try:
        if check_service_health(API_URL):
            print(f"{GREEN}✅ API service is healthy{RESET}")
            health_ok = True
        else:
            print(f"{RED}❌ API service is not healthy{RESET}")
            health_ok = False
    except Exception as e:
        print(f"{RED}❌ Health check error: {e}{RESET}")
        health_ok = False
    
    # Test 2: Model Warmup
    if health_ok:
        print(f"\n{BLUE}Test 2: Model Warmup{RESET}")
        try:
            print(f"{YELLOW}🔥 Running warmup...{RESET}")
            result = warmup_models(API_URL)
            
            if result and result.get('overall_success'):
                print(f"{GREEN}✅ Model warmup completed successfully{RESET}")
                
                # Print detailed results
                embedding_result = result.get('embedding_model', {})
                llm_result = result.get('llm_model', {})
                
                print(f"\n{BLUE}📊 Detailed Results:{RESET}")
                print(f"  Embedding Model:")
                print(f"    Status: {embedding_result.get('status')}")
                print(f"    Time: {embedding_result.get('time_ms', 0):.0f}ms")
                print(f"  LLM Model:")
                print(f"    Status: {llm_result.get('status')}")
                print(f"    Time: {llm_result.get('time_ms', 0):.0f}ms")
                
                warmup_ok = True
            else:
                print(f"{RED}❌ Model warmup failed or partially failed{RESET}")
                warmup_ok = False
                
        except Exception as e:
            print(f"{RED}❌ Warmup error: {e}{RESET}")
            warmup_ok = False
    else:
        print(f"\n{YELLOW}⏭️ Skipping warmup test (service not healthy){RESET}")
        warmup_ok = False
    
    # Test 3: Import Test
    print(f"\n{BLUE}Test 3: Module Import Test{RESET}")
    try:
        from model_warmup_server import ModelWarmupServer
        print(f"{GREEN}✅ ModelWarmupServer imported successfully{RESET}")
        import_ok = True
    except Exception as e:
        print(f"{RED}❌ Import error: {e}{RESET}")
        import_ok = False
    
    # Summary
    print(f"\n{BLUE}📋 Test Summary{RESET}")
    print("=" * 50)
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Model Warmup: {'✅ PASS' if warmup_ok else '❌ FAIL'}")
    print(f"Module Import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    
    all_tests_passed = health_ok and warmup_ok and import_ok
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_tests_passed:
        print(f"\n{YELLOW}💡 Troubleshooting Tips:{RESET}")
        if not health_ok:
            print("  - Make sure RAG + LLM API service is running on http://localhost:5002")
            print("  - Check if the service is accessible: curl http://localhost:5002/health")
        if not import_ok:
            print("  - Ensure all required Python modules are installed")
            print("  - Check if client_utils.py is in the same directory")
    
    return all_tests_passed

def demo_warmup_server():
    """Demonstrate warmup server usage"""
    
    print(f"\n{BLUE}🎯 Warmup Server Usage Demo{RESET}")
    print("=" * 50)
    
    try:
        from model_warmup_server import ModelWarmupServer
        
        print(f"{BLUE}Creating warmup server instance...{RESET}")
        server = ModelWarmupServer(api_url="http://localhost:5002", interval_minutes=1)
        
        print(f"{GREEN}✅ Server created successfully{RESET}")
        print(f"  API URL: {server.api_url}")
        print(f"  Interval: {server.interval_seconds//60} minutes")
        
        print(f"\n{YELLOW}💡 To start the server manually:{RESET}")
        print(f"  python3 model_warmup_server.py")
        print(f"  python3 model_warmup_server.py --interval 5")
        print(f"  python3 model_warmup_server.py --test")
        
        print(f"\n{YELLOW}💡 To start with bash script:{RESET}")
        print(f"  ./start_warmup_server.sh")
        print(f"  ./start_warmup_server.sh --interval 5")
        print(f"  ./start_warmup_server.sh --test")
        
        return True
        
    except Exception as e:
        print(f"{RED}❌ Demo error: {e}{RESET}")
        return False

def main():
    """Main test function"""
    
    print(f"{GREEN}🔥 Model Warmup Server Test Suite{RESET}")
    print("=" * 70)
    
    # Run component tests
    test_success = test_warmup_server()
    
    # Run demo
    demo_success = demo_warmup_server()
    
    # Overall result
    print(f"\n{'='*70}")
    if test_success and demo_success:
        print(f"{GREEN}🎉 All tests completed successfully!{RESET}")
        print(f"{BLUE}💡 You can now run the warmup server with confidence.{RESET}")
        return 0
    else:
        print(f"{RED}❌ Some tests failed. Please check the issues above.{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())
