#!/usr/bin/env python3
"""
Script to create a ChromaDB database called 'db_for_showroom' 
using data from itri_online_showroom folder.

This script:
1. Loads all text files from itri_online_showroom folder
2. Chunks them using semantic chunking
3. Creates a new ChromaDB collection named 'db_for_showroom'
4. Generates embeddings and stores them in the database
"""

import os
import sys
import shutil
import requests
import chromadb
import argparse
from pathlib import Path

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import LLM_MODEL_NAME, CHROMA_DB_PATH

# Import RAG pipeline
from LLM_Chat.RAG_LLM_realtime import ImprovedRAGPipeline

# Colors for console output
GRAY = "\033[90m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def create_showroom_database(
    data_folder: str = "itri_museum_docs/itri_online_showroom",
    collection_name: str = "db_for_showroom",
    chroma_db_path: str = None,
    embedding_model: str = "bge-m3:latest",
    reload: bool = True
    ):
    """
    Create a ChromaDB database for the showroom data.
    """
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Creating ChromaDB database: {collection_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Determine ChromaDB path
    if chroma_db_path is None:
        chroma_db_path = os.path.join(os.path.dirname(CHROMA_DB_PATH), "chroma_db_showroom")
    
    print(f"{BLUE}📁 ChromaDB path: {chroma_db_path}{RESET}")
    print(f"{BLUE}📂 Data folder: {data_folder}{RESET}")
    
    # Ensure data folder exists
    full_data_path = os.path.join(current_dir, data_folder)
    if not os.path.exists(full_data_path):
        print(f"{RED}❌ Data folder not found: {full_data_path}{RESET}")
        return False
    
    # Initialize RAG pipeline
    print(f"\n{BLUE}🔄 Initializing RAG pipeline...{RESET}")
    rag_pipeline = ImprovedRAGPipeline(museum_name='itri_showroom')
    
    # Load and chunk documents
    print(f"\n{BLUE}📚 Loading and chunking documents from {full_data_path}...{RESET}")
    chunks = rag_pipeline.load_and_chunk_docs(full_data_path)
    
    if not chunks:
        print(f"{RED}❌ No chunks created from documents{RESET}")
        return False
    
    print(f"{GREEN}✅ Created {len(chunks)} chunks from documents{RESET}")
    
    # Ensure ChromaDB directory exists
    os.makedirs(chroma_db_path, exist_ok=True)
    os.chmod(chroma_db_path, 0o755)
    
    # Create ChromaDB client
    chroma_client = chromadb.PersistentClient(path=chroma_db_path)
    
    # Handle collection creation/deletion
    if reload:
        print(f"\n{BLUE}🔄 Reloading vector store - cleaning up old data...{RESET}")
        try:
            chroma_client.delete_collection(collection_name)
            print(f"{GREEN}✅ Deleted existing collection: {collection_name}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠️ Collection '{collection_name}' does not exist or could not be deleted: {e}{RESET}")
        
        # Reset internal state
        rag_pipeline.vectorizer = None
        rag_pipeline.tfidf_matrix = None
        rag_pipeline.chunks = []
        
        # Create new collection
        try:
            chroma_collection = chroma_client.create_collection(collection_name)
            print(f"{GREEN}✅ Created new ChromaDB collection: {collection_name}{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error creating collection: {e}{RESET}")
            return False
        
        # Build TF-IDF for sparse retrieval
        print(f"\n{BLUE}🔧 Building TF-IDF index for sparse retrieval...{RESET}")
        rag_pipeline._build_tfidf_index(chunks)
        
        # Generate dense embeddings
        print(f"\n{BLUE}🧮 Generating embeddings for {len(chunks)} chunks...{RESET}")
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if (i + 1) % 10 == 0 or i == 0:
                print(f"\r{GRAY}Processing chunk {i+1}/{len(chunks)}{RESET}", end="", flush=True)
            
            try:
                # ---------------------------------------------------------
                # [FIX] Add 'search_document:' prefix for Nomic models
                # This drastically improves retrieval quality
                # ---------------------------------------------------------
                prompt_text = chunk.content
                if "nomic" in embedding_model:
                    prompt_text = f"search_document: {chunk.content}"

                # Generate dense embedding
                response = requests.post("http://localhost:11435/api/embeddings", json={
                    "model": embedding_model,
                    "prompt": prompt_text
                }, timeout=30)
                response.raise_for_status()
                embedding = response.json()['embedding']
                
                embeddings.append(embedding)
                documents.append(chunk.content)
                
                # Clean metadata
                safe_metadata = {}
                for k, v in (chunk.metadata or {}).items():
                    if v is None: continue
                    if isinstance(v, (bool, int, float, str)):
                        safe_metadata[k] = v
                    else:
                        safe_metadata[k] = str(v)
                metadatas.append(safe_metadata)
                ids.append(chunk.chunk_id)
            except Exception as e:
                print(f"\n{RED}❌ Error generating embedding for chunk {i+1}: {e}{RESET}")
                continue
        
        print() 
        
        if not documents:
            print(f"{RED}❌ No documents to store{RESET}")
            return False
        
        # Store in ChromaDB
        BATCH_SIZE = 5000
        print(f"\n{BLUE}💾 Storing {len(documents)} chunks in ChromaDB...{RESET}")
        for i in range(0, len(documents), BATCH_SIZE):
            batch_end = min(i + BATCH_SIZE, len(documents))
            try:
                chroma_collection.add(
                    documents=documents[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
                print(f"{GREEN}✅ Stored batch {i//BATCH_SIZE + 1} ({batch_end - i} chunks){RESET}")
            except Exception as e:
                print(f"{RED}❌ Error storing batch: {e}{RESET}")
                return False
        
        print(f"\n{GREEN}✅ Database creation successful!{RESET}")
        return True
    else:
        try:
            chroma_collection = chroma_client.get_collection(collection_name)
            print(f"{GREEN}✅ Loaded existing collection ({chroma_collection.count()} docs){RESET}")
            return True
        except Exception as e:
            print(f"{RED}❌ Failed to load collection: {e}{RESET}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Create ChromaDB')
    parser.add_argument('--data-folder', default='itri_museum_docs/itri_online_showroom')
    parser.add_argument('--collection-name', default='db_for_showroom')
    parser.add_argument('--chroma-db-path', default=None)
    parser.add_argument('--embedding-model', default='bge-m3:latest')
    parser.add_argument('--reload', action='store_true', default=True)
    parser.add_argument('--golden', action='store_true')
    
    args = parser.parse_args()

    if args.golden:
        if args.data_folder == 'itri_museum_docs/itri_online_showroom':
            args.data_folder = 'database_wiki_gemini整理_一定對的...'
        if args.collection_name == 'db_for_showroom':
            args.collection_name = 'db_for_itri_golden'
        if args.chroma_db_path is None:
            args.chroma_db_path = os.path.join(os.path.dirname(CHROMA_DB_PATH), "chroma_db_golden")
    
    success = create_showroom_database(
        data_folder=args.data_folder,
        collection_name=args.collection_name,
        chroma_db_path=args.chroma_db_path,
        embedding_model=args.embedding_model,
        reload=args.reload
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())