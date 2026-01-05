#!/usr/bin/env python3
"""
Script to create a ChromaDB database for ITRI knowledge base.
Optimized for structured JSON data (One Item = One Chunk).
"""

import os
import sys
import json
import requests
import chromadb
import argparse
from typing import List, Dict, Any
import re

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from config import LLM_MODEL_NAME, CHROMA_DB_PATH

# Colors for console output
GRAY = "\033[90m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def load_itri_json_docs(folder_path: str) -> List[Dict[str, Any]]:
    """
    Load JSON files and convert each item into a document structure.
    Does NOT split text; maintains 1-to-1 mapping between JSON item and Chunk.
    """
    documents = []
    
    if not os.path.exists(folder_path):
        print(f"{RED}❌ Data folder not found: {folder_path}{RESET}")
        return []

    # Find all JSON files
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    print(f"{BLUE}📂 Found {len(json_files)} JSON files in {folder_path}{RESET}")

    for file_name in json_files:
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"{YELLOW}⚠️ Skipping {file_name}: Expected a list of objects.{RESET}")
                continue

            print(f"   - Processing {file_name} ({len(data)} items)...")
            
            for index, item in enumerate(data):
                # 1. Construct Content for Embedding (Smart Formatting)
                # This ensures the vector represents the full meaning
                content_for_embedding = ""
                
                # Case 1: QA Pair (Golden QA)
                if 'question' in item and 'answer' in item:
                    content_for_embedding = f"問題：{item['question']}\n答案：{item['answer']}"
                
                # Case 2: Glossary (Term Definition)
                elif 'term' in item and 'content' in item:
                    full_name = item.get('full_name', '')
                    content_for_embedding = f"術語：{item['term']} ({full_name})\n解釋：{item['content']}"
                
                # Case 3: News (Date + Title + Content)
                elif 'date' in item and 'title' in item:
                    content_for_embedding = f"日期：{item['date']}\n標題：{item['title']}\n內容：{item.get('content', '')}"
                
                # Case 4: General Item (Title + Content) - Fallback for most types
                else:
                    title = item.get('title', '')
                    body = item.get('content', '')
                    # If title is not already in body, prepend it
                    if title and title not in body:
                        content_for_embedding = f"{title}\n{body}"
                    else:
                        content_for_embedding = body

                # 2. Prepare Metadata (Flatten for ChromaDB)
                # ChromaDB metadata values must be str, int, float, or bool
                metadata = {"source_file": file_name, "chunk_index": index}
                for k, v in item.items():
                    if k == 'content': continue # Content is stored separately
                    if v is None: continue
                    
                    if isinstance(v, (str, int, float, bool)):
                        metadata[k] = v
                    else:
                        metadata[k] = str(v) # Convert lists/dicts to string representation

                # 3. Create Document Object
                documents.append({
                    "id": f"{file_name}_{index}",
                    "text": content_for_embedding,
                    "metadata": metadata
                })

        except Exception as e:
            print(f"{RED}❌ Error processing {file_name}: {e}{RESET}")

    return documents

def create_showroom_database(
    data_folder: str = "database_wiki_gemini整理_一定對的...",
    collection_name: str = "chroma_db_golden",
    chroma_db_path: str = None,
    embedding_model: str = "bge-m3:latest",
    reload: bool = True
    ):
    """
    Create a ChromaDB database from JSON files.
    """
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Creating ChromaDB database: {collection_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Determine ChromaDB path
    if chroma_db_path is None:
        chroma_db_path = os.path.join(os.path.dirname(CHROMA_DB_PATH), "chroma_db_golden")
    
    print(f"{BLUE}📁 ChromaDB path: {chroma_db_path}{RESET}")
    print(f"{BLUE}📂 Data folder: {data_folder}{RESET}")
    
    # 1. Load Data (One Item = One Chunk)
    full_data_path = os.path.join(current_dir, data_folder)
    documents = load_itri_json_docs(full_data_path)
    
    if not documents:
        print(f"{RED}❌ No valid documents found.{RESET}")
        return False
    
    print(f"{GREEN}✅ Loaded {len(documents)} structured documents.{RESET}")
    
    # 2. Setup ChromaDB
    os.makedirs(chroma_db_path, exist_ok=True)
    try:
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
    except Exception as e:
        print(f"{RED}❌ Failed to initialize ChromaDB client: {e}{RESET}")
        return False
    
    # 3. Handle Collection (Reload or Load)
    if reload:
        print(f"\n{BLUE}🔄 Reloading vector store...{RESET}")
        try:
            chroma_client.delete_collection(collection_name)
            print(f"{GREEN}   - Deleted existing collection.{RESET}")
        except:
            pass
        
        try:
            collection = chroma_client.create_collection(collection_name)
            print(f"{GREEN}   - Created new collection.{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error creating collection: {e}{RESET}")
            return False
            
        # 4. Generate Embeddings & Store
        print(f"\n{BLUE}🧮 Generating embeddings using [{embedding_model}]...{RESET}")
        
        batch_size = 10 
        total_docs = len(documents)
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i : i + batch_size]
            batch_texts = [d['text'] for d in batch]
            batch_ids = [d['id'] for d in batch]
            batch_metadatas = [d['metadata'] for d in batch]
            batch_embeddings = []
            
            print(f"\r{GRAY}   Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({len(batch)} items){RESET}", end="", flush=True)
            
            # Generate Embeddings for the batch
            for text in batch_texts:
                try:
                    # [CRITICAL] Prefix handling for Nomic models
                    prompt_text = text
                    if "nomic" in embedding_model:
                        prompt_text = f"search_document: {text}"
                        
                    response = requests.post("http://localhost:11435/api/embeddings", json={
                        "model": embedding_model,
                        "prompt": prompt_text
                    }, timeout=60) # Increased timeout for safety
                    
                    if response.status_code == 200:
                        batch_embeddings.append(response.json()['embedding'])
                    else:
                        print(f"\n{RED}   ❌ API Error: {response.text}{RESET}")
                        batch_embeddings.append(None) # Handle failure gracefully
                        
                except Exception as e:
                    print(f"\n{RED}   ❌ Connection Error: {e}{RESET}")
                    batch_embeddings.append(None)
            
            # Filter out failed embeddings
            valid_data = [
                (id, txt, meta, emb) 
                for id, txt, meta, emb in zip(batch_ids, batch_texts, batch_metadatas, batch_embeddings) 
                if emb is not None
            ]
            
            if valid_data:
                try:
                    collection.add(
                        ids=[x[0] for x in valid_data],
                        documents=[x[1] for x in valid_data],
                        metadatas=[x[2] for x in valid_data],
                        embeddings=[x[3] for x in valid_data]
                    )
                except Exception as e:
                    print(f"\n{RED}   ❌ ChromaDB Add Error: {e}{RESET}")

        print(f"\n\n{GREEN}🎉 Database creation completed! Stored {collection.count()} items.{RESET}")
        return True
        
    else:
        # Just load existing
        try:
            collection = chroma_client.get_collection(collection_name)
            print(f"{GREEN}✅ Loaded existing collection ({collection.count()} items).{RESET}")
            return True
        except Exception as e:
            print(f"{RED}❌ Collection not found. Please use --reload to create it.{RESET}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Create ChromaDB for ITRI Showroom')
    parser.add_argument('--data-folder', default='database_wiki_gemini整理_一定對的...')
    parser.add_argument('--collection-name', default='chroma_db_golden')
    parser.add_argument('--chroma-db-path', default=None)
    parser.add_argument('--embedding-model', default='bge-m3:latest') 
    parser.add_argument('--reload', action='store_true', default=True)
    parser.add_argument('--golden', action='store_true')
    
    args = parser.parse_args()

    # Special handling for "Golden" dataset path if requested
    if args.golden:
        args.data_folder = 'database_wiki_gemini整理_一定對的...' 
        if args.collection_name == 'chroma_db_golden':
            args.collection_name = 'chroma_db_golden'
    
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