#!/usr/bin/env python3
"""
Model Warmup Server

A standalone service that runs warmup_models every 10 minutes to keep 
the RAG + LLM system models warm for optimal performance.

Usage:
    python model_warmup_server.py [--api-url URL] [--interval MINUTES]
"""

import time
import signal
import sys
import threading
import argparse
from datetime import datetime, timedelta
from client_utils import warmup_models, check_service_health

# Colors for console output
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

class ModelWarmupServer:
    """Standalone server to keep models warm"""
    
    def __init__(self, api_url: str = "http://localhost:5002", interval_minutes: int = 10):
        self.api_url = api_url
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self.warmup_thread = None
        self.stats = {
            'total_warmups': 0,
            'successful_warmups': 0,
            'failed_warmups': 0,
            'start_time': None,
            'last_warmup': None,
            'next_warmup': None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n{YELLOW}📨 Received signal {signum}, shutting down gracefully...{RESET}")
        self.stop()
        sys.exit(0)
    
    def _print_banner(self):
        """Print startup banner"""
        print("=" * 70)
        print(f"{GREEN}🔥 Model Warmup Server{RESET}")
        print("=" * 70)
        print(f"📡 API URL: {self.api_url}")
        print(f"⏰ Warmup Interval: {self.interval_seconds//60} minutes ({self.interval_seconds}s)")
        print(f"🚀 Starting warmup service...")
        print("=" * 70)
    
    def _print_stats(self):
        """Print current statistics"""
        now = datetime.now()
        uptime = now - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        print(f"\n{BLUE}📊 Warmup Server Statistics:{RESET}")
        print(f"  Uptime: {uptime}")
        print(f"  Total Warmups: {self.stats['total_warmups']}")
        print(f"  Successful: {self.stats['successful_warmups']}")
        print(f"  Failed: {self.stats['failed_warmups']}")
        if self.stats['last_warmup']:
            print(f"  Last Warmup: {self.stats['last_warmup'].strftime('%Y-%m-%d %H:%M:%S')}")
        if self.stats['next_warmup']:
            print(f"  Next Warmup: {self.stats['next_warmup'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def _perform_warmup(self):
        """Perform model warmup and update statistics"""
        try:
            now = datetime.now()
            print(f"{BLUE}🔥 [{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting model warmup...{RESET}")
            
            # Check service health first
            if not check_service_health(self.api_url):
                print(f"{RED}❌ Service health check failed - skipping warmup{RESET}")
                self.stats['failed_warmups'] += 1
                return False
            
            # Perform warmup
            result = warmup_models(self.api_url)
            
            if result and result.get('overall_success'):
                print(f"{GREEN}✅ Model warmup completed successfully{RESET}")
                self.stats['successful_warmups'] += 1
                self.stats['last_warmup'] = now
                return True
            else:
                print(f"{RED}❌ Model warmup failed or partially failed{RESET}")
                self.stats['failed_warmups'] += 1
                return False
                
        except Exception as e:
            print(f"{RED}❌ Warmup error: {e}{RESET}")
            self.stats['failed_warmups'] += 1
            return False
        finally:
            self.stats['total_warmups'] += 1
            self.stats['next_warmup'] = datetime.now() + timedelta(seconds=self.interval_seconds)
    
    def _warmup_loop(self):
        """Main warmup loop that runs in a separate thread"""
        print(f"{GREEN}🚀 Warmup service started{RESET}")
        
        # Perform initial warmup immediately
        self._perform_warmup()
        
        # Continue with regular interval
        while self.running:
            try:
                # Wait for the interval, but check every second if we should stop
                for _ in range(self.interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                
                if self.running:
                    self._perform_warmup()
                    self._print_stats()
                    
            except Exception as e:
                print(f"{RED}❌ Error in warmup loop: {e}{RESET}")
                if self.running:
                    time.sleep(10)  # Wait 10 seconds before retrying
    
    def start(self):
        """Start the warmup service"""
        if self.running:
            print(f"{YELLOW}⚠️ Service is already running{RESET}")
            return
        
        self._print_banner()
        
        # Check initial service health
        print(f"{BLUE}🔍 Checking API service health...{RESET}")
        if not check_service_health(self.api_url):
            print(f"{RED}❌ API service is not healthy at {self.api_url}{RESET}")
            print(f"{YELLOW}⚠️ Make sure the RAG + LLM API service is running{RESET}")
            return False
        
        print(f"{GREEN}✅ API service is healthy{RESET}")
        
        # Start the service
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.warmup_thread = threading.Thread(target=self._warmup_loop, daemon=True)
        self.warmup_thread.start()
        
        print(f"{GREEN}🎯 Warmup server is now running...{RESET}")
        print(f"{BLUE}💡 Press Ctrl+C to stop{RESET}")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}📨 Keyboard interrupt received{RESET}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the warmup service"""
        if not self.running:
            return
        
        print(f"{YELLOW}🛑 Stopping warmup service...{RESET}")
        self.running = False
        
        if self.warmup_thread and self.warmup_thread.is_alive():
            print(f"{BLUE}⏳ Waiting for warmup thread to finish...{RESET}")
            self.warmup_thread.join(timeout=5)
        
        self._print_stats()
        print(f"{GREEN}👋 Warmup service stopped gracefully{RESET}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Model Warmup Server')
    parser.add_argument('--api-url', default='http://localhost:5002', 
                       help='URL of the RAG + LLM API service (default: http://localhost:5002)')
    parser.add_argument('--interval', type=int, default=10, 
                       help='Warmup interval in minutes (default: 10)')
    parser.add_argument('--test', action='store_true', 
                       help='Run a single warmup test and exit')
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - run single warmup and exit
        print(f"{BLUE}🧪 Test Mode: Running single warmup...{RESET}")
        
        if not check_service_health(args.api_url):
            print(f"{RED}❌ API service is not healthy at {args.api_url}{RESET}")
            return 1
        
        result = warmup_models(args.api_url)
        if result and result.get('overall_success'):
            print(f"{GREEN}✅ Test warmup completed successfully{RESET}")
            return 0
        else:
            print(f"{RED}❌ Test warmup failed{RESET}")
            return 1
    
    # Normal mode - run warmup server
    server = ModelWarmupServer(api_url=args.api_url, interval_minutes=args.interval)
    
    try:
        success = server.start()
        return 0 if success else 1
    except Exception as e:
        print(f"{RED}❌ Server error: {e}{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())
