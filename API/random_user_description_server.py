#!/usr/bin/env python3
"""
Vision Context API Simulator

This server simulates the Vision Context API for testing the dynamic tone selection system.
It provides random visual context descriptions (simulating VLM output) using the same
API format as the real Vision Context API.

Usage:
    python random_user_description_server.py --port 5003
"""

import random
import time
from flask import Flask, jsonify
from flask_cors import CORS

# Colors for console output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Pool of user descriptions (simulating VLM output)
USER_DESCRIPTION_POOL = [
    # "a little boy",
    # # Child-friendly descriptionss
    # "a young boy wearing glasses, and is smiling",
    # "a little girl with pigtails holding a backpack",
    # "a teenager in school uniform looking curious",
    # "a young child with curious eyes pointing at something",
    # "a smiling girl around 8 years old wearing a colorful dress",
    # "a boy in elementary school uniform holding a notebook",
    
    # # Elder-friendly descriptions
    "an elderly man",
    #"an elderly man with gray hair and wrinkles, wearing a cardigan",
    # "an old woman with white hair using a walking stick",
    # "一位白髮蒼蒼坐在輪椅上的老奶奶",
    # "an elderly person with glasses sitting in a comfortable chair",
    #"a senior man with white beard wearing traditional clothing",
    # "一位拄著拐杖的老爺爺",
    
    # # Professional-friendly descriptions
    # "a middle-aged person in business suit standing confidently in an office",
    # "a man in formal attire holding documents in a conference room",
    # "穿西裝的商務人士站在辦公室裡",
    # "a professional woman in business attire with a laptop",
    # "a businessman wearing a tie in a corporate setting",
    # "穿正式服裝的職場人士",
    
    # # Casual-friendly descriptions
    # "a person wearing jeans and t-shirt sitting relaxed",
    # "a woman wearing casual clothes at home on a couch",
    # "穿便服的中年人在家裡",
    # "someone in comfortable casual wear having coffee",
    # "a relaxed adult in everyday clothing",
    # "穿著休閒的年輕人",
    
    # # Edge cases
    # "a person standing",
    # "",  # Empty description for fallback testing
]

class VisionContextAPISimulator:
    """Server that simulates the Vision Context API with random descriptions"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Simulate active sessions (in production this would be managed by the vision system)
        self.active_sessions = {}  # session_id -> {"vision_enabled": bool, "last_context": str, "timestamp": float}
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/sessions', methods=['GET'])
        def get_active_sessions():
            """Get active sessions with visual perception capabilities (Vision API compatible)"""
            # Automatically create some demo sessions if none exist
            if not self.active_sessions:
                demo_sessions = [
                    f"demo_session_{i}_{int(time.time())}" for i in range(1, 4)
                ]
                for session_id in demo_sessions:
                    self.active_sessions[session_id] = {
                        "vision_enabled": True,
                        "last_context": random.choice(USER_DESCRIPTION_POOL),
                        "timestamp": time.time()
                    }
            
            sessions_data = []
            for session_id, session_info in self.active_sessions.items():
                sessions_data.append({
                    "sessionid": session_id,
                    "vision_enabled": session_info["vision_enabled"],
                    "has_visual_context": bool(session_info["last_context"])
                })
            
            return jsonify({
                "active_sessions": sessions_data,
                "total_sessions": len(sessions_data)
            })
        
        @self.app.route('/visual-context/<sessionid>', methods=['GET'])
        def get_visual_context(sessionid):
            """
            Get visual context for a specific session (Vision API compatible)
            
            Args:
                sessionid: Session ID to get visual context for
            
            Returns:
                JSON response matching Vision API specification
            """
            # Simulate processing delay (like a real VLM would have)
            # time.sleep(0.1)
            
            # Always provide a fresh random description regardless of session state
            context = random.choice(USER_DESCRIPTION_POOL)
            vision_enabled = True

            self.active_sessions[sessionid] = {
                "vision_enabled": vision_enabled,
                "last_context": context,
                "timestamp": time.time()
            }
            
            session_info = self.active_sessions[sessionid]
            context = session_info["last_context"]
            
            # Determine if visual context is available
            available = session_info["vision_enabled"] and bool(context and context.strip())
            
            print(f"{BLUE}📸 Session {sessionid}: {'Available' if available else 'Not Available'} - '{context}'{RESET}")
            
            # Return Vision API compatible response
            return jsonify({
                "sessionid": sessionid,
                "visual_context": context if available else None,
                "available": available
            })
        
        @self.app.route('/api/simulator/pool', methods=['GET'])
        def get_pool_info():
            """Get information about the description pool (simulator-specific endpoint)"""
            return jsonify({
                'success': True,
                'pool_size': len(USER_DESCRIPTION_POOL),
                'pool': USER_DESCRIPTION_POOL,
                'active_sessions': len(self.active_sessions),
                'timestamp': time.time()
            })
    
    def run(self, host: str = '0.0.0.0', port: int = 5003, debug: bool = False):
        """Run the server"""
        print(f"{GREEN}🚀 Vision Context API Simulator Starting{RESET}")
        print("=" * 70)
        print(f"🌐 Service URL: http://{host}:{port}")
        print(f"👥 Sessions List: GET http://{host}:{port}/sessions")
        print(f"📸 Visual Context: GET http://{host}:{port}/visual-context/{{sessionid}}")
        print(f"📊 Pool Info: GET http://{host}:{port}/api/simulator/pool")
        print(f"🎲 Pool Size: {len(USER_DESCRIPTION_POOL)} descriptions")
        print("=" * 70)
        print(f"{YELLOW}💡 This simulates the Vision Context API for testing.{RESET}")
        print(f"{YELLOW}   Compatible with Vision API specification format.{RESET}")
        print("=" * 70)
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vision Context API Simulator (Compatible with Vision API Specification)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5003, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run server
    server = VisionContextAPISimulator()
    
    try:
        server.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print(f"\n{BLUE}👋 Server shutting down...{RESET}")
        return 0
    except Exception as e:
        print(f"\n{RED}💥 Server error: {e}{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())



