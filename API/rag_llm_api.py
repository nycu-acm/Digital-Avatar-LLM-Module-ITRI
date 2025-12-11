#!/usr/bin/env python3
"""
RAG + LLM API Service

A standalone API service that exposes the RAG + LLM functionality from the integrated pipeline.
Provides streaming text responses with END_FLAG for completion indication.

Input: text_user_msg
Output: streaming llm_text_response with END_FLAG when done
"""

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["POSTHOG_DISABLED"] = "1"
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify, Response, stream_template, stream_with_context
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add parent directories to path to import RAG components
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import LLM_MODEL_NAME, CHROMA_DB_PATH

sys.path.insert(0, os.path.join(parent_dir, 'LLM_Chat'))
from LLM_Chat.RAG_LLM_realtime import ImprovedRAGPipeline

# Import tone system prompts
from tone_system_prompts_no_tag import get_tone_system_prompt, build_tone_selector_system_prompt, PERCENTAGE
# from tone_system_prompts import get_tone_system_prompt, build_tone_selector_system_prompt

# Colors for console output
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

class RAGLLMAPIService:
    """Standalone API service for RAG + LLM functionality"""
    
    def __init__(self, user_description_server_url: str = "http://localhost:5004"):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize RAG pipeline
        self.rag_pipeline = None
        self.chroma_collection = None
        self.rag_initialized = False
        
        # Chat history storage (simple in-memory, can be enhanced with persistent storage)
        self.chat_sessions = {}  # session_id -> chat_history
        
        # Vision Context API configuration
        self.user_description_server_url = user_description_server_url
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'rag_initialized': self.rag_initialized,
                'timestamp': time.time()
            })
        
        @self.app.route('/api/rag-llm/query', methods=['POST'])
        def rag_llm_query():
            """
            Main RAG + LLM query endpoint with streaming response
            
            Input JSON:
            {
                "text_user_msg": "Your question here",
                "session_id": "optional_session_id",
                "include_history": true/false (optional, default: true),
                "user_description": "visual description from VLM (e.g., 'a young boy wearing glasses, and is smiling')",
                "tone": "casual_friendly" (optional, deprecated - use user_description instead),
                "convert_tone": true/false (optional, default: true)
            }
            
            Output: Streaming text response with END_FLAG
            """
            try:
                # Parse request
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                text_user_msg = data.get('text_user_msg')
                if not text_user_msg:
                    return jsonify({'error': 'text_user_msg is required'}), 400
                
                session_id = data.get('session_id', 'default')
                include_history = data.get('include_history', True)
                user_description = data.get('user_description', '')  # VLM visual description for dynamic tone selection
                tone = data.get('tone', 'casual_friendly')  # Deprecated but kept for backward compatibility
                convert_tone = data.get('convert_tone', False)  # Updated default to True
                
                # Get chat history for this session
                chat_history = self.chat_sessions.get(session_id, []) if include_history else []
                
                # Generate streaming response (with optional tone conversion)
                if convert_tone:
                    return Response(
                        stream_with_context(self._generate_streaming_response_with_tone(
                            text_user_msg, session_id, chat_history, user_description, convert_tone
                        )),
                        mimetype='text/plain',
                        headers={
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive',
                            'X-Accel-Buffering': 'no'  # Disable nginx buffering if present
                        }
                    )
                else:
                    return Response(
                        stream_with_context(self._generate_streaming_response(
                            text_user_msg, session_id, chat_history
                        )),
                        mimetype='text/plain',
                        headers={
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive',
                            'X-Accel-Buffering': 'no'  # Disable nginx buffering if present
                        }
                    )
                
            except Exception as e:
                self.logger.error(f"Query error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/rag-llm/init', methods=['POST'])
        def initialize_rag():
            """Initialize the RAG system"""
            try:
                success = self._initialize_rag_system()
                
                return jsonify({
                    'success': success,
                    'rag_initialized': self.rag_initialized,
                    'message': 'RAG system initialized successfully' if success else 'RAG initialization failed'
                })
            except Exception as e:
                self.logger.error(f"RAG initialization error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/rag-llm/sessions/<session_id>/history', methods=['GET', 'DELETE'])
        def manage_session_history(session_id):
            """Get or clear chat history for a session"""
            if request.method == 'GET':
                history = self.chat_sessions.get(session_id, [])
                return jsonify({
                    'session_id': session_id,
                    'history': history,
                    'message_count': len(history)
                })
            elif request.method == 'DELETE':
                self.chat_sessions.pop(session_id, None)
                return jsonify({
                    'session_id': session_id,
                    'message': 'History cleared'
                })
        
        @self.app.route('/api/rag-llm/close', methods=['POST'])
        def close_connection():
            """
            Elegant connection close endpoint
            
            Client calls this function before program termination.
            Server will clear the history of the client based on the chat_session_id.
            
            Input JSON:
            {
                "session_id": "your_session_id"
            }
            
            Output: Confirmation of successful closure and cleanup
            """
            try:
                # Parse request
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                session_id = data.get('session_id')
                if not session_id:
                    return jsonify({'error': 'session_id is required'}), 400
                
                # Perform cleanup operations
                session_existed = session_id in self.chat_sessions
                message_count = len(self.chat_sessions.get(session_id, []))
                
                # Clear session history
                self.chat_sessions.pop(session_id, None)
                
                # Log the closure
                self.logger.info(f"Connection closed gracefully for session: {session_id}")
                print(f"{GREEN}👋 Session {session_id} closed gracefully ({message_count} messages cleared){RESET}")
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'message': 'Connection closed successfully',
                    'session_existed': session_existed,
                    'messages_cleared': message_count,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                self.logger.error(f"Connection close error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/rag-llm/warmup', methods=['POST'])
        def warmup_models():
            """
            Warmup endpoint to preload embedding model and LLM
            
            This endpoint performs small test operations to ensure both the embedding
            model and LLM are loaded into memory, reducing latency on first real requests.
            
            Output: Status of warmup operations for both models
            """
            try:
                print(f"{BLUE}🔥 Starting model warmup...{RESET}")
                
                warmup_results = {
                    'embedding_model': {'status': 'skipped', 'message': 'RAG not initialized', 'time_ms': 0},
                    'llm_model': {'status': 'failed', 'message': 'Not attempted', 'time_ms': 0},
                    'overall_success': False,
                    'timestamp': time.time()
                }
                
                # Warmup embedding model
                embedding_result = self._warmup_embedding_model()
                warmup_results['embedding_model'] = embedding_result
                
                # Warmup LLM
                llm_result = self._warmup_llm_model()
                warmup_results['llm_model'] = llm_result
                
                # Determine overall success
                # LLM success is critical, embedding can be skipped due to dimension mismatch
                warmup_results['overall_success'] = (
                    embedding_result['status'] in ['success', 'skipped'] and 
                    llm_result['status'] == 'success'
                )
                
                total_time = embedding_result['time_ms'] + llm_result['time_ms']
                print(f"{GREEN}🔥 Model warmup completed in {total_time:.0f}ms{RESET}")
                
                return jsonify(warmup_results)
                
            except Exception as e:
                self.logger.error(f"Warmup error: {e}")
                return jsonify({
                    'embedding_model': {'status': 'failed', 'message': str(e), 'time_ms': 0},
                    'llm_model': {'status': 'failed', 'message': 'Warmup failed', 'time_ms': 0},
                    'overall_success': False,
                    'timestamp': time.time(),
                    'error': str(e)
                }), 500

        @self.app.route('/api/rag-llm/convert-tone', methods=['POST'])
        def convert_tone():
            """
            Standalone tone conversion endpoint with streaming response
            
            Input JSON:
            {
                "text": "Text to convert",
                "tone": "child_friendly" (optional, default),
                "stream": true/false (optional, default: true),
                "user_description": "visual description from VLM" (optional),
                "user_msg": "original user message" (optional)
            }
            
            Output: Streaming tone-converted text with END_FLAG
            """
            try:
                # Parse request
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                text = data.get('text')
                if not text:
                    return jsonify({'error': 'text is required'}), 400
                
                tone = data.get('tone', 'child_friendly')
                use_streaming = data.get('stream', True)
                user_description = data.get('user_description', '')
                user_msg = data.get('user_msg', '')
                
                if use_streaming:
                    # Generate streaming response
                    return Response(
                        stream_with_context(self._stream_convert_tone(text, tone, user_description, user_msg)),
                        mimetype='text/plain',
                        headers={
                            'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive',
                            'X-Accel-Buffering': 'no'  # Disable nginx buffering if present
                        }
                    )
                else:
                    # Non-streaming response
                    converted_text = self._convert_tone(text, tone, user_description, user_msg)
                    if converted_text is not None:
                        return jsonify({
                            'success': True,
                            'original_text': text,
                            'converted_text': converted_text,
                            'tone': tone,
                            'user_description': user_description
                        })
                    else:
                        return jsonify({'error': 'Tone conversion failed'}), 500
                
            except Exception as e:
                self.logger.error(f"Tone conversion error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/rag-llm/query-with-tone', methods=['POST'])
        def rag_llm_query_with_tone():
            """
            Combined RAG + LLM query with automatic tone conversion
            
            Input JSON:
            {
                "text_user_msg": "Your question here",
                "session_id": "optional_session_id",
                "include_history": true/false (optional, default: true),
                "user_description": "visual description from VLM (e.g., 'a young boy wearing glasses, and is smiling')",
                "tone": "casual_friendly" (optional, deprecated - use user_description instead),
                "convert_tone": true/false (optional, default: true)
            }
            
            Output: Streaming response with automatic tone conversion and END_FLAG
            """
            try:
                # Parse request
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                text_user_msg = data.get('text_user_msg')
                if not text_user_msg:
                    return jsonify({'error': 'text_user_msg is required'}), 400
                
                session_id = data.get('session_id', 'default')
                include_history = data.get('include_history', True)
                user_description = data.get('user_description', '')  # VLM visual description for dynamic tone selection
                tone = data.get('tone', 'casual_friendly')  # Deprecated but kept for backward compatibility
                convert_tone = data.get('convert_tone', True)
                
                # Get chat history for this session
                chat_history = self.chat_sessions.get(session_id, []) if include_history else []
                
                # Generate streaming response with tone conversion
                return Response(
                    stream_with_context(self._generate_streaming_response_with_tone(
                        text_user_msg, session_id, chat_history, user_description, convert_tone
                    )),
                    mimetype='text/plain',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'X-Accel-Buffering': 'no'  # Disable nginx buffering if present
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Query with tone error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _initialize_rag_system(self) -> bool:
        """Initialize the RAG system with ChromaDB path detection"""
        try:
            print(f"{BLUE}🔄 Initializing RAG system...{RESET}")
            
            # Initialize RAG pipeline
            if not self.rag_pipeline:
                self.rag_pipeline = ImprovedRAGPipeline()
                print(f"{GREEN}✅ RAG pipeline created{RESET}")
            
            # Try multiple ChromaDB paths
            potential_paths = [
                f"{CHROMA_DB_PATH}",  # User's actual ChromaDB location
            ]
            
            chroma_client = None
            chroma_db_path = None
            
            import chromadb
            
            # Try to find existing ChromaDB
            for path in potential_paths:
                if os.path.exists(path):
                    try:
                        print(f"{BLUE}🔍 Trying ChromaDB path: {path}{RESET}")
                        chroma_client = chromadb.PersistentClient(path=path)
                        chroma_db_path = path
                        break
                    except Exception as e:
                        print(f"{YELLOW}⚠️ Failed to connect to {path}: {e}{RESET}")
                        continue
            
            # If no existing ChromaDB found, create new one in workspace
            if not chroma_client:
                print(f"{RED}❌ No ChromaDB found{RESET}")
                # Create new ChromaDB in the user's specified location
                chroma_db_path = f"{CHROMA_DB_PATH}"
                print(f"{BLUE}📦 Creating new ChromaDB at: {chroma_db_path}{RESET}")
                os.makedirs(chroma_db_path, exist_ok=True)
                chroma_client = chromadb.PersistentClient(path=chroma_db_path)
            
            print(f"{GREEN}✅ Using ChromaDB at: {chroma_db_path}{RESET}")
            
            # Try different collection names
            collection_names = [
                f"{self.rag_pipeline.museum_name}_collection",  # itri_museum_collection
                "itri_museum_docs",  # From error message
                f"{self.rag_pipeline.museum_name}_docs",  # itri_museum_docs
                "museum_collection",  # Generic name
                "default_collection"  # Fallback
            ]
            
            # List existing collections to see what's available
            try:
                existing_collections = chroma_client.list_collections()
                if existing_collections:
                    print(f"{BLUE}📋 Available collections:{RESET}")
                    for coll in existing_collections:
                        print(f"  - {coll.name} ({coll.count()} docs)")
                        collection_names.insert(0, coll.name)  # Prioritize existing collections
                else:
                    print(f"{YELLOW}📋 No existing collections found{RESET}")
            except Exception as e:
                print(f"{YELLOW}⚠️ Could not list collections: {e}{RESET}")
            
            # Try to load or create collection
            collection_found = False
            for collection_name in collection_names:
                try:
                    self.chroma_collection = chroma_client.get_collection(collection_name)
                    count = self.chroma_collection.count()
                    print(f"{GREEN}✅ Loaded existing collection: {collection_name} ({count} documents){RESET}")
                    collection_found = True
                    break
                except Exception:
                    continue
            
            # If no collection found, create a new one with sample data
            if not collection_found:
                print(f"{YELLOW}🆕 Creating new collection with sample data...{RESET}")
                try:
                    chunks = self.rag_pipeline.load_json_data()
                    if chunks:
                        collection_name = f"{self.rag_pipeline.museum_name}_collection"
                        self.chroma_collection = self.rag_pipeline.build_vector_database(
                            chunks, chroma_client, collection_name
                        )
                        print(f"{GREEN}✅ Created new collection: {collection_name} ({len(chunks)} chunks){RESET}")
                    else:
                        # Create minimal collection for testing (without embeddings for now)
                        collection_name = f"{self.rag_pipeline.museum_name}_collection"
                        try:
                            # Try with default embedding function first
                            self.chroma_collection = chroma_client.create_collection(
                                name=collection_name,
                                metadata={"description": "ITRI Museum collection"}
                            )
                        except Exception as embedding_error:
                            print(f"{YELLOW}⚠️ Default embedding failed: {embedding_error}{RESET}")
                            # Try with simpler embedding function
                            try:
                                import chromadb.utils.embedding_functions as embedding_functions
                                # Use sentence transformer without downloading
                                self.chroma_collection = chroma_client.create_collection(
                                    name=collection_name,
                                    embedding_function=embedding_functions.DefaultEmbeddingFunction(),
                                    metadata={"description": "ITRI Museum collection"}
                                )
                            except Exception as e2:
                                print(f"{YELLOW}⚠️ Embedding function error: {e2}{RESET}")
                                # Final fallback - just create without specific embedding
                                self.chroma_collection = chroma_client.get_or_create_collection(
                                    name=collection_name,
                                    metadata={"description": "ITRI Museum collection"}
                                )
                        
                        # Add sample documents
                        try:
                            sample_docs = [
                                "ITRI (Industrial Technology Research Institute) is Taiwan's largest and most comprehensive research institution.",
                                "ITRI focuses on applied research in areas such as information and communications, electronics, materials, chemical engineering, and biomedical technologies.",
                                "Founded in 1973, ITRI has been instrumental in Taiwan's technological development and industrial transformation."
                            ]
                            sample_ids = ["sample_1", "sample_2", "sample_3"]
                            sample_metadatas = [
                                {"source": "general", "type": "overview"},
                                {"source": "general", "type": "research_areas"},
                                {"source": "general", "type": "history"}
                            ]
                            
                            self.chroma_collection.add(
                                documents=sample_docs, 
                                ids=sample_ids,
                                metadatas=sample_metadatas
                            )
                            print(f"{GREEN}✅ Created minimal collection: {collection_name} ({len(sample_docs)} sample documents){RESET}")
                        except Exception as add_error:
                            print(f"{YELLOW}⚠️ Could not add sample documents: {add_error}{RESET}")
                            print(f"{GREEN}✅ Created empty collection: {collection_name}{RESET}")
                            
                except Exception as e:
                    print(f"{YELLOW}⚠️ Collection creation had issues: {e}{RESET}")
                    # Try to continue anyway - maybe we can work without RAG
                    print(f"{BLUE}🔄 Attempting to continue without full RAG capabilities...{RESET}")
                    try:
                        # Create a dummy collection just to keep the service working
                        collection_name = "fallback_collection"
                        self.chroma_collection = chroma_client.get_or_create_collection(
                            name=collection_name,
                            metadata={"description": "Fallback collection"}
                        )
                        print(f"{YELLOW}⚠️ Using fallback collection - RAG features may be limited{RESET}")
                    except Exception as fallback_error:
                        print(f"{RED}❌ Could not create fallback collection: {fallback_error}{RESET}")
                        # Continue without ChromaDB - LLM only mode
                        self.chroma_collection = None
                        print(f"{YELLOW}⚠️ Running in LLM-only mode without RAG{RESET}")
                        return True  # Still consider this successful
            
            # Build cached system prompt
            self.rag_pipeline.cached_system_prompt = self.rag_pipeline._build_fixed_system_prompt(
                "NOTICE: You must answer in 1 sentence only.(請用一句話回答!只能有一句!不可以超過) The response language should depend on what the user requires. If the user does not specify a language, use the same language as the user input. If Mandarin or Chinese is requested, respond in Traditional Chinese (zh-tw)."
            )
            
            self.rag_initialized = True
            print(f"{GREEN}✅ RAG system initialized successfully{RESET}")
            return True
            
        except Exception as e:
            print(f"{RED}❌ RAG initialization failed: {e}{RESET}")
            self.rag_initialized = False
            return False
    
    def _determine_tone_from_user_description(self, user_description: str) -> str:
        """
        Analyze visual user description from VLM and determine the most appropriate tone.
        
        Args:
            user_description: Visual description from VLM (e.g., "a young boy wearing glasses, and is smiling")
        
        Returns:
            str: The determined tone ('child_friendly', 'elder_friendly', etc.)
        """
        try:
            if not user_description or not user_description.strip():
                return "casual_friendly"  # Default fallback
            
            # Detect input language
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_description)
            target_lang = "Traditional Chinese (繁體中文)" if has_chinese else "English"
            
            # System prompt for VLM-based tone selection agent
            system_prompt = build_tone_selector_system_prompt(target_lang)
            
            # Create user instruction
            user_instruction = f"Analyze this user description and determine the appropriate tone:\n{user_description.strip()}"
            
            payload = {
                "model": f"{LLM_MODEL_NAME}",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_instruction},
                ],
                "stream": False,
                "options": {"temperature": 0.1}  # Low temperature for consistent analysis
            }
            
            resp = requests.post("http://localhost:11435/api/chat", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
                tone_result = data["message"].get("content", "").strip().lower()
            elif isinstance(data, dict) and "response" in data:
                tone_result = str(data.get("response", "")).strip().lower()
            else:
                tone_result = ""
            
            # Validate and return the tone
            valid_tones = ["child_friendly", "elder_friendly", "professional_friendly", "casual_friendly"]
            if tone_result in valid_tones:
                print(f"{BLUE}🎯 Tone selected: {tone_result} (based on VLM description: '{user_description}'){RESET}")
                return tone_result
            else:
                print(f"{YELLOW}⚠️ Invalid tone '{tone_result}', defaulting to casual_friendly{RESET}")
                return "casual_friendly"
                
        except Exception as e:
            self.logger.error(f"Tone determination failed: {e}")
            print(f"{YELLOW}⚠️ Tone determination error: {e}, defaulting to casual_friendly{RESET}")
            return "casual_friendly"  # Safe fallback
    
    def _fetch_user_description_from_server(self, session_id: str) -> str:
        """
        Fetch visual context from the Vision Context API.
        
        Args:
            session_id: Session ID to get visual context for
        
        Returns:
            str: Visual context description from the vision API, or empty string on failure
        """
        try:
            print(f"{BLUE}📸 Fetching visual context for session {session_id} from vision server...{RESET}")
            response = requests.get(
                f"{self.user_description_server_url}/visual-context/{session_id}",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check if visual context is available according to Vision API spec
            if data.get('available', False):
                visual_context = data.get('visual_context', '')
                print(f"{GREEN}✅ Fetched visual context: '{visual_context}'{RESET}")
                return visual_context
            else:
                print(f"{YELLOW}⚠️ No visual context available for session {session_id}{RESET}")
                print(f"{YELLOW}   User may not have enabled vision or no recent analysis available{RESET}")
                return ""
            
        except requests.exceptions.ConnectionError:
            print(f"{YELLOW}⚠️ Could not connect to Vision Context API at {self.user_description_server_url}{RESET}")
            print(f"{YELLOW}   Make sure the vision API server is running on port 5004{RESET}")
            print(f"{YELLOW}   Using empty description (will default to casual_friendly tone){RESET}")
            return ""
        except requests.exceptions.Timeout:
            print(f"{YELLOW}⚠️ Vision Context API timeout{RESET}")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to fetch visual context: {e}")
            print(f"{YELLOW}⚠️ Error fetching visual context: {e}{RESET}")
            return ""
    
    def _convert_tone(self, text: str, tone: str = "child_friendly", user_description: str = "", user_msg: str = "", is_first_message: bool = False) -> str:
        """
        Convert the tone/style of a given text using a secondary agent (LLM rewriter).
        
        Args:
            text: The original text to be rewritten.
            tone: Target tone/style (e.g., "child_friendly", "elder_friendly").
            user_description: Visual description from VLM (for additional context).
            user_msg: Original user message (for additional context).
        
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
            
            # Enhanced instruction with user context and first message guidance
            context_info = ""
            if user_description:
                context_info += f"\nUser Appearance: {user_description}"
            if user_msg:
                context_info += f"\nUser Question: {user_msg}"
            
            # Add first message guidance
            if is_first_message and user_description:
                context_info += f"\nFirst Message: YES (MUST reference user appearance to grab attention)"
            elif user_description:
                context_info += f"\nFirst Message: NO ({PERCENTAGE}% chance to reference appearance for variety)"
            
            user_instruction = (
                f"Rewrite this text to speak to {target_audience} in {target_lang}:{context_info}\n"
                f"---\n{text}\n---"
            )

            payload = {
                "model": f"{LLM_MODEL_NAME}",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_instruction},
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            }

            resp = requests.post("http://localhost:11435/api/chat", json=payload, timeout=None)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", "").strip()
            # Fallback common formats
            if isinstance(data, dict) and "response" in data:
                return str(data.get("response", "")).strip()
            return None
        except Exception as e:
            self.logger.error(f"Tone conversion failed: {e}")
            return None

    def _stream_convert_tone(self, text: str, tone: str = "child_friendly", user_description: str = "", user_msg: str = "", is_first_message: bool = False):
        """
        Stream the tone conversion so users can see the rewritten text as it is generated.
        
        Args:
            text: The text to convert
            tone: Target tone/style (e.g., "child_friendly", "elder_friendly")
            user_description: Visual description from VLM (for additional context)
            user_msg: Original user message (for additional context)
        
        Yields chunks as they arrive and returns the final converted string.
        """
        try:
            if not text:
                yield text
                return

            # Detect input language
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            target_lang = "Traditional Chinese (繁體中文)" if has_chinese else "English"

            # Get appropriate system prompt based on tone
            system_prompt = get_tone_system_prompt(tone, target_lang)

            # Create tone-specific user instruction
            tone_descriptions = {
                "child_friendly": "children",
                "elder_friendly": "elderly people",
                "professional_friendly": "professional adult",
                "casual_friendly": "casual and chill adult"
            }
            target_audience = tone_descriptions.get(tone, tone.replace("_", " "))
            
            # Enhanced instruction with user context and first message guidance
            context_info = ""
            if user_description:
                context_info += f"\nUser Appearance: {user_description}"
            if user_msg:
                context_info += f"\nUser Question: {user_msg}"
            
            # Add first message guidance
            if is_first_message and user_description:
                context_info += f"\nFirst Message: YES (MUST reference user appearance to grab attention)"
            elif user_description:
                context_info += f"\nFirst Message: NO ({PERCENTAGE}% chance to reference appearance for variety)"
            
            user_instruction = (
                f"Rewrite this text to speak to {target_audience} in {target_lang}:{context_info}\n"
                f"---\n{text}\n---"
            )

            payload = {
                "model": f"{LLM_MODEL_NAME}",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_instruction},
                ],
                "stream": True,
                "options": {"temperature": 0.3}
            }

            response = requests.post("http://localhost:11435/api/chat", json=payload, stream=True)
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
                    yield delta
                if chunk.get("done"):
                    print(f"{RED}Converted msg: {converted}{RESET}")
                    yield "END_FLAG"
                    break
                    
        except Exception as e:
            self.logger.error(f"Streaming tone conversion failed: {e}")
            yield f"ERROR: {str(e)}"
            yield "END_FLAG"

    def _generate_streaming_response_with_tone(self, text_user_msg: str, session_id: str, chat_history: List[Dict], user_description: str = None, convert_tone: bool = True):
        """Generate streaming RAG + LLM response with dynamic tone conversion using parallel processing"""
        try:
            # Check if user_description is provided by client (textual input)
            # Only query Vision server if user_description is None or empty string
            has_client_provided_description = user_description and user_description.strip()
            
            if has_client_provided_description:
                print(f"{BLUE}📝 Using client-provided textual user description: '{user_description}'{RESET}")
                print(f"{BLUE}🚀 Starting QA response generation (skipping Vision server query)...{RESET}")
            else:
                print(f"{BLUE}🚀 Starting parallel processing for Vision API query and QA response...{RESET}")
            
            # Storage for parallel results
            fetched_user_description = ""
            response_content = ""
            
            # Create a thread pool for parallel execution (only if we need to query Vision server)
            if has_client_provided_description:
                # Client provided description - no need to query Vision server
                # Just generate QA response
                fetched_user_description = user_description.strip()
                
                print(f"{BLUE}📝 Collecting QA response with client-provided description...{RESET}")
                print(f"{BLUE}📝 Input: text_user_msg='{text_user_msg[:50]}...', session_id='{session_id}', chat_history_size={len(chat_history)}{RESET}")
                
                # Generate QA response directly (no parallel processing needed)
                try:
                    print(f"{BLUE}🔄 Calling _generate_streaming_response...{RESET}")
                    original_response_generator = self._generate_streaming_response(text_user_msg, session_id, chat_history)
                    print(f"{GREEN}✅ Generator created, starting iteration...{RESET}")
                    chunk_count = 0
                    for chunk in original_response_generator:
                        chunk_count += 1
                        if chunk == "END_FLAG":
                            print(f"{GREEN}✅ Received END_FLAG after {chunk_count} chunks{RESET}")
                            break
                        elif chunk.startswith("ERROR:"):
                            print(f"{RED}❌ Error in QA response: {chunk}{RESET}")
                            yield chunk
                            yield "END_FLAG"
                            return
                        else:
                            response_content += chunk
                            if chunk_count <= 5 or chunk_count % 50 == 0:  # Log first 5 chunks and every 50th
                                print(f"{BLUE}📦 Chunk #{chunk_count}: {len(chunk)} chars (total: {len(response_content)} chars){RESET}")
                    
                    print(f"{GREEN}✅ QA response collected! Total chunks: {chunk_count}, Total length: {len(response_content)} chars{RESET}")
                    print(f"{BLUE}📝 Using client-provided user description: '{fetched_user_description}'{RESET}")
                    print(f"{BLUE}💬 QA response preview: '{response_content[:100]}...' (full length: {len(response_content)}){RESET}")
                    
                    if not response_content.strip():
                        print(f"{YELLOW}⚠️ WARNING: QA response is empty!{RESET}")
                        yield "ERROR: QA response is empty"
                        yield "END_FLAG"
                        return
                        
                except Exception as e:
                    error_msg = f"Error collecting QA response: {str(e)}"
                    print(f"{RED}❌ {error_msg}{RESET}")
                    self.logger.error(error_msg, exc_info=True)
                    yield f"ERROR: {error_msg}"
                    yield "END_FLAG"
                    return
            else:
                # No client-provided description - query Vision server in parallel with QA
                with ThreadPoolExecutor(max_workers=2) as executor:
                    # Task 1: Fetch visual context from Vision API
                    print(f"{BLUE}📸 Fetching visual context from Vision server for session ID: '{session_id[20:] if len(session_id) > 20 else session_id}'{RESET}")
                    future_description = executor.submit(self._fetch_user_description_from_server, session_id[20:] if len(session_id) > 20 else session_id)
                    
                    # Task 2: Generate QA response
                    def collect_qa_response():
                        """Helper function to collect full QA response"""
                        try:
                            print(f"{BLUE}[Thread] Starting QA response collection...{RESET}")
                            print(f"[Thread] Input: text_user_msg='{text_user_msg[:50]}...', session_id='{session_id}', chat_history_size={len(chat_history)}{RESET}")
                            
                            content = ""
                            print(f"{BLUE}[Thread] Calling _generate_streaming_response...{RESET}")
                            original_response_generator = self._generate_streaming_response(text_user_msg, session_id, chat_history)
                            print(f"{GREEN}[Thread] Generator created, starting iteration...{RESET}")
                            
                            chunk_count = 0
                            for chunk in original_response_generator:
                                chunk_count += 1
                                if chunk == "END_FLAG":
                                    print(f"{GREEN}[Thread] ✅ Received END_FLAG after {chunk_count} chunks{RESET}")
                                    break
                                elif chunk.startswith("ERROR:"):
                                    print(f"{RED}[Thread] ❌ Error in QA response: {chunk}{RESET}")
                                    return None, chunk  # Return error
                                else:
                                    content += chunk
                                    if chunk_count <= 5 or chunk_count % 50 == 0:
                                        print(f"{BLUE}[Thread] 📦 Chunk #{chunk_count}: {len(chunk)} chars (total: {len(content)} chars){RESET}")
                            
                            print(f"{GREEN}[Thread] ✅ QA response collected! Total chunks: {chunk_count}, Total length: {len(content)} chars{RESET}")
                            if not content.strip():
                                print(f"{YELLOW}[Thread] ⚠️ WARNING: QA response is empty!{RESET}")
                            return content, None
                        except Exception as e:
                            error_msg = f"[Thread] Error in collect_qa_response: {str(e)}"
                            print(f"{RED}❌ {error_msg}{RESET}")
                            import traceback
                            print(f"{RED}[Thread] Traceback: {traceback.format_exc()}{RESET}")
                            return None, f"ERROR: {error_msg}"
                    
                    future_qa = executor.submit(collect_qa_response)
                    
                    # Wait for both tasks to complete
                    print(f"{YELLOW}⏳ Waiting for parallel tasks to complete...{RESET}")
                    
                    # Get user description result from Vision server (with timeout)
                    try:
                        fetched_user_description = future_description.result(timeout=10)
                        print(f"{BLUE}📸 Vision server returned: '{fetched_user_description}'{RESET}")
                    except Exception as e:
                        print(f"{RED}❌ Error getting Vision server result: {e}{RESET}")
                        fetched_user_description = ""
                    
                    # Get QA response result (with timeout)
                    try:
                        print(f"{YELLOW}⏳ Waiting for QA response (this may take a while)...{RESET}")
                        response_content, error = future_qa.result(timeout=120)  # 2 minute timeout for LLM
                        
                        if error:
                            print(f"{RED}❌ QA response collection failed: {error}{RESET}")
                            # Pass through errors immediately
                            yield error
                            yield "END_FLAG"
                            return
                        
                        print(f"{GREEN}✅ Parallel tasks completed!{RESET}")
                        print(f"{BLUE}📸 User description from Vision server: '{fetched_user_description}'{RESET}")
                        print(f"{BLUE}💬 QA response length: {len(response_content)} chars{RESET}")
                        print(f"{BLUE}💬 QA response preview: '{response_content[:100]}...'{RESET}")
                        
                        if not response_content.strip():
                            print(f"{RED}❌ ERROR: QA response is empty!{RESET}")
                            yield "ERROR: QA response is empty"
                            yield "END_FLAG"
                            return
                            
                    except Exception as e:
                        print(f"{RED}❌ Error getting QA response result: {e}{RESET}")
                        import traceback
                        print(f"{RED}Traceback: {traceback.format_exc()}{RESET}")
                        yield f"ERROR: QA response collection failed: {str(e)}"
                        yield "END_FLAG"
                        return
            
            # Now apply tone conversion if requested
            print(f"{YELLOW}🔍 Checking tone conversion: convert_tone={convert_tone}, response_content length={len(response_content)}, response_content empty={not response_content.strip()}, has_description={bool(fetched_user_description and fetched_user_description.strip())}{RESET}")
            
            if not response_content.strip():
                print(f"{RED}❌ ERROR: response_content is empty! Cannot proceed with tone conversion.{RESET}")
                yield "ERROR: QA response is empty"
                yield "END_FLAG"
                return
            
            if convert_tone and response_content.strip():
                # Determine tone based on user description
                if fetched_user_description and fetched_user_description.strip():
                    print(f"{BLUE}🎯 Determining tone from user description: '{fetched_user_description}'{RESET}")
                    selected_tone = self._determine_tone_from_user_description(fetched_user_description)
                    description_source = "client-provided text" if has_client_provided_description else "Vision server"
                    print(f"{BLUE}🎨 Converting tone to {selected_tone} (determined from {description_source}: '{fetched_user_description}')...{RESET}")
                else:
                    selected_tone = "casual_friendly"  # Default fallback
                    print(f"{BLUE}🎨 Converting tone to {selected_tone} (default, no user description available)...{RESET}")
                
                # Check if this is the first message in the conversation
                is_first_message = len(chat_history) == 0
                print(f"{YELLOW}chat history: {chat_history}{RESET}")
                print(f"{BLUE}🎯 Is first message: {is_first_message} (chat history size: {int(len(chat_history) / 2)}){RESET}")
                
                # Stream the tone conversion with user context
                print(f"{BLUE}🔄 Starting tone conversion stream...{RESET}")
                converted_response = ""
                tone_chunk_count = 0
                for tone_chunk in self._stream_convert_tone(
                    response_content, 
                    selected_tone, 
                    user_description=fetched_user_description,
                    user_msg=text_user_msg,
                    is_first_message=is_first_message
                ):
                    tone_chunk_count += 1
                    if tone_chunk == "END_FLAG":
                        # Store the CONVERTED response to chat history (not original)
                        if session_id not in self.chat_sessions:
                            self.chat_sessions[session_id] = []
                        
                        self.chat_sessions[session_id].append({"role": "user", "content": text_user_msg})
                        self.chat_sessions[session_id].append({"role": "assistant", "content": converted_response})
                        print(f"{GREEN}🎨 Tone conversion completed! Total chunks: {tone_chunk_count}, Converted length: {len(converted_response)} chars{RESET}")
                        print(f"{GREEN}🎨 Chat history updated with tone-converted response for session {session_id}{RESET}")
                        
                        yield "END_FLAG"
                        break
                    else:
                        converted_response += tone_chunk
                        if tone_chunk_count <= 5 or tone_chunk_count % 50 == 0:
                            print(f"{BLUE}🎨 Tone chunk #{tone_chunk_count}: {len(tone_chunk)} chars (total: {len(converted_response)} chars){RESET}")
                        yield tone_chunk
            else:
                # Just return the original response if no tone conversion
                # Add both user message and original response to chat history
                if session_id not in self.chat_sessions:
                    self.chat_sessions[session_id] = []
                
                self.chat_sessions[session_id].append({"role": "user", "content": text_user_msg})
                self.chat_sessions[session_id].append({"role": "assistant", "content": response_content})
                print(f"{GREEN}🤖 Chat history updated with original response for session {session_id}{RESET}")
                yield response_content
                yield "END_FLAG"
                
        except Exception as e:
            self.logger.error(f"Streaming response with tone error: {e}")
            yield f"ERROR: {str(e)}"
            yield "END_FLAG"

    def _generate_streaming_response(self, text_user_msg: str, session_id: str, chat_history: List[Dict]) -> str:
        """Generate streaming RAG + LLM response"""
        try:
            context = ""
            
            # Get RAG context if available
            if self.rag_initialized and self.rag_pipeline and self.chroma_collection:
                try:
                    search_results = self.rag_pipeline.hybrid_search(
                        text_user_msg, self.chroma_collection, top_k=10
                    )
                    
                    # Extract museum context
                    museum_context = []
                    for result in search_results:
                        content = result.get('content', '')
                        if content and not (content.startswith('[Q') or content.startswith('[A')):
                            museum_context.append(content)
                    
                    context = self.rag_pipeline._process_context(museum_context, text_user_msg)
                    print(f"{YELLOW}📚 RAG CONTEXT: {len(context)} chars{RESET}")
                    
                except Exception as e:
                    print(f"{YELLOW}⚠️ RAG search failed: {e}{RESET}")
                    context = ""
            else:
                print(f"{YELLOW}⚠️ RAG not available, using LLM-only mode{RESET}")
                context = ""
            
            # Build messages for LLM
            if self.rag_initialized and self.rag_pipeline:
                # Use RAG pipeline's message building
                system_prompt = self.rag_pipeline.cached_system_prompt
                # print(f"{YELLOW}🤖 SYSTEM PROMPT: {system_prompt}{RESET}")
                messages = self.rag_pipeline._build_messages(
                    system_prompt, text_user_msg, chat_history, context
                )
                print(f"{YELLOW}🤖 chat_history size: {int(len(chat_history) / 2)}{RESET}")
            else:
                # Fallback to simple messages
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. Keep your responses concise and engaging."},
                    {"role": "user", "content": text_user_msg}
                ]
            
            # Stream LLM response
            request_payload = {
                "model": f"{LLM_MODEL_NAME}",
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0.7}
            }
            
            print(f"{YELLOW}🤖 Starting streaming LLM response for session {session_id}...{RESET}")
            response = requests.post("http://localhost:11435/api/chat", json=request_payload, stream=True)
            response.raise_for_status()
            
            # Process streaming response
            response_content = ""
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
                    response_content += delta
                    # Stream the delta to client
                    yield delta
                
                if chunk.get("done"):
                    # Note: Chat history is now updated in the calling method after tone conversion
                    # Keep only recent history (last 10 messages)
                    # if len(self.chat_sessions[session_id]) > 10:
                    #     self.chat_sessions[session_id] = self.chat_sessions[session_id][-10:]
                    
                    print(f"{GREEN}🤖 Streaming response completed for session {session_id}: {len(response_content)} chars{RESET}")
                    print(f"{YELLOW}🤖 Response content (before tone conversion): {response_content}{RESET}")
                    
                    # Send END_FLAG when done
                    yield "END_FLAG"
                    break
        except Exception as e:
            self.logger.error(f"Streaming response error: {e}")
            yield f"ERROR: {str(e)}"
            yield "END_FLAG"
    
    def _warmup_embedding_model(self) -> Dict[str, Any]:
        """Warmup the embedding model by performing a small embedding operation"""
        start_time = time.time()
        
        try:
            if not self.rag_initialized or not self.chroma_collection:
                return {
                    'status': 'skipped',
                    'message': 'RAG system not initialized',
                    'time_ms': 0
                }
            
            print(f"{BLUE}🔥 Warming up embedding model...{RESET}")
            
            # Perform a small query to warm up the embedding model
            warmup_query = "ITRI warmup test"
            
            # Generate embedding using Ollama API (same approach as LLM_Chat)
            q_response = requests.post("http://localhost:11435/api/embeddings", json={
                "model": "nomic-embed-text",
                "prompt": warmup_query
            })
            q_response.raise_for_status()
            q_emb = [q_response.json()['embedding']]
            
            # Use ChromaDB's query method with pre-generated embeddings
            result = self.chroma_collection.query(
                query_embeddings=q_emb,
                n_results=1
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            print(f"{GREEN}✅ Embedding model warmed up in {elapsed_ms:.0f}ms{RESET}")
            
            return {
                'status': 'success',
                'message': f'Embedding model warmed up successfully',
                'time_ms': round(elapsed_ms, 2),
                'test_query': warmup_query,
                'results_found': len(result.get('documents', []))
            }
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_str = str(e)
            
            # Handle specific embedding dimension mismatch
            if "expecting embedding with dimension" in error_str:
                print(f"{YELLOW}⚠️ Embedding dimension mismatch detected{RESET}")
                print(f"{YELLOW}   This usually means the collection was created with a different embedding model{RESET}")
                print(f"{YELLOW}   Embedding warmup will be skipped, but this won't affect LLM performance{RESET}")
                
                return {
                    'status': 'skipped',
                    'message': f'Embedding dimension mismatch - collection and current model incompatible',
                    'time_ms': round(elapsed_ms, 2),
                    'details': error_str,
                    'recommendation': 'Consider recreating the collection with the current embedding model'
                }
            else:
                # Other embedding errors
                error_msg = f"Embedding warmup failed: {error_str}"
                print(f"{YELLOW}⚠️ {error_msg}{RESET}")
                
                return {
                    'status': 'failed',
                    'message': error_msg,
                    'time_ms': round(elapsed_ms, 2)
                }
    
    def _warmup_llm_model(self) -> Dict[str, Any]:
        """Warmup the LLM by sending a small test request"""
        start_time = time.time()
        
        try:
            print(f"{BLUE}🔥 Warming up LLM model...{RESET}")
            
            # Send a minimal request to warm up the LLM
            warmup_messages = [
                {"role": "system", "content": "You are a helpful assistant. Respond with just 'OK'."},
                {"role": "user", "content": "Warmup test"}
            ]
            
            request_payload = {
                "model": f"{LLM_MODEL_NAME}",
                "messages": warmup_messages,
                "stream": False,  # Non-streaming for faster warmup
                "options": {
                    "temperature": 0.1,
                    # "max_tokens": 5  # Very short response
                }
            }
            
            response = requests.post(
                "http://localhost:11435/api/chat", 
                json=request_payload, 
                timeout=None  # 30 second timeout for warmup
            )
            response.raise_for_status()
            
            result = response.json()
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Check if we got a valid response
            if 'message' in result and 'content' in result['message']:
                response_content = result['message']['content']
                print(f"{GREEN}✅ LLM model warmed up in {elapsed_ms:.0f}ms{RESET}")
                
                return {
                    'status': 'success',
                    'message': 'LLM model warmed up successfully',
                    'time_ms': round(elapsed_ms, 2),
                    'test_response': response_content.strip()
                }
            else:
                return {
                    'status': 'failed',
                    'message': 'LLM returned unexpected response format',
                    'time_ms': round(elapsed_ms, 2)
                }
            
        except requests.exceptions.Timeout:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = "LLM warmup timed out (30s)"
            print(f"{YELLOW}⚠️ {error_msg}{RESET}")
            
            return {
                'status': 'failed',
                'message': error_msg,
                'time_ms': round(elapsed_ms, 2)
            }
            
        except requests.exceptions.ConnectionError:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = "Could not connect to LLM service (check if Ollama is running)"
            print(f"{YELLOW}⚠️ {error_msg}{RESET}")
            
            return {
                'status': 'failed',
                'message': error_msg,
                'time_ms': round(elapsed_ms, 2)
            }
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_msg = f"LLM warmup failed: {str(e)}"
            print(f"{YELLOW}⚠️ {error_msg}{RESET}")
            
            return {
                'status': 'failed',
                'message': error_msg,
                'time_ms': round(elapsed_ms, 2)
            }
    
    def run(self, host: str = '0.0.0.0', port: int = 5002, debug: bool = False):
        """Run the API service"""
        print(f"{GREEN}🚀 RAG + LLM API Service Starting{RESET}")
        print("=" * 70)
        print(f"🌐 Service URL: http://{host}:{port}")
        print(f"📋 Health Check: GET http://{host}:{port}/health")
        print(f"🤖 Query Endpoint: POST http://{host}:{port}/api/rag-llm/query")
        print(f"🎨 Tone Convert: POST http://{host}:{port}/api/rag-llm/convert-tone")
        print(f"🤖🎨 Query + Dynamic Tone: POST http://{host}:{port}/api/rag-llm/query-with-tone")
        print(f"🔄 Init Endpoint: POST http://{host}:{port}/api/rag-llm/init")
        print(f"🔥 Warmup Endpoint: POST http://{host}:{port}/api/rag-llm/warmup")
        print(f"👋 Close Endpoint: POST http://{host}:{port}/api/rag-llm/close")
        print("=" * 70)
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG + LLM API Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5002, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--auto-init', action='store_true', help='Auto-initialize RAG system on startup')
    parser.add_argument('--user-description-server', default='http://localhost:5004', 
                        help='URL of the Vision Context API server (default: http://localhost:5004)')
    
    args = parser.parse_args()
    
    # Create and configure service
    service = RAGLLMAPIService(user_description_server_url=args.user_description_server)
    
    # Auto-initialize if requested
    if args.auto_init:
        print(f"{BLUE}🔄 Auto-initializing RAG system...{RESET}")
        if service._initialize_rag_system():
            print(f"{GREEN}✅ RAG system initialized{RESET}")
        else:
            print(f"{RED}❌ RAG initialization failed{RESET}")
            return 1
    
    # Run the service
    try:
        service.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print(f"\n{BLUE}👋 API service shutting down...{RESET}")
        return 0
    except Exception as e:
        print(f"\n{RED}💥 Service error: {e}{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())