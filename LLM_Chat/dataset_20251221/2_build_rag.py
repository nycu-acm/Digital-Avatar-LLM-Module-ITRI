#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI RAG Database Builder - Step 2: Build Vector Database
讀取爬取的 JSON 資料，進行 Chunking 與 Embedding，並存入 ChromaDB
"""

import json
import os
from pathlib import Path
from datetime import datetime

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document
except ImportError as e:
    print("❌ 缺少必要的套件，請先安裝：")
    print("   pip install langchain langchain-community langchain-huggingface chromadb")
    print(f"\n錯誤詳情: {e}")
    exit(1)

# --- 設定 ---
INPUT_FILE = os.path.join("crawled_data", "itri_raw_data.json")
CHROMA_PATH = "./chroma_db_itri"
OLLAMA_EMBED_MODEL = "bge-m3"  # 或使用 "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11435"

# Chunking 參數
CHUNK_SIZE = 500      # 每個區塊的大小（字元數）
CHUNK_OVERLAP = 100   # 重疊區塊大小，確保上下文不中斷


def load_and_chunk_data():
    """載入原始資料並進行切片"""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到資料檔: {INPUT_FILE}")
        print("   請先執行 1_crawl_data.py 進行資料爬取！")
        return []

    print("=" * 60)
    print("📚 ITRI RAG Database Builder - Step 2: Build Vector Database")
    print("=" * 60)
    
    print(f"\n1️⃣  載入原始資料...")
    print(f"   📁 檔案: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析錯誤: {e}")
        return []
    except Exception as e:
        print(f"❌ 讀取檔案錯誤: {e}")
        return []

    if not data:
        print("⚠️  資料檔為空，請檢查爬蟲是否成功執行")
        return []

    print(f"   ✅ 共載入 {len(data)} 篇文章")

    # 將 JSON 轉為 LangChain Document 物件
    print(f"\n2️⃣  轉換為 Document 物件...")
    documents = []
    for i, item in enumerate(data):
        doc = Document(
            page_content=item.get('content', ''),
            metadata={
                "source": item.get('source', 'Unknown'),
                "title": item.get('title', 'Untitled'),
                "url": item.get('url', ''),
                "hierarchy": item.get('hierarchy', ''),
                "language": item.get('language', 'zh-tw'),
                "crawled_at": item.get('crawled_at', ''),
                "depth": item.get('depth', 0),
                "doc_id": i  # 添加文件 ID
            }
        )
        documents.append(doc)
    
    print(f"   ✅ 轉換完成，共 {len(documents)} 個文件")

    # 執行切片 (Chunking)
    print(f"\n3️⃣  執行切片 (Chunking)...")
    print(f"   📏 Chunk Size: {CHUNK_SIZE} 字元")
    print(f"   🔗 Chunk Overlap: {CHUNK_OVERLAP} 字元")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"   ✅ 切片完成，共生成 {len(chunks)} 個知識區塊")
    
    # 顯示統計資訊
    if chunks:
        avg_chunk_size = sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
        print(f"   📊 平均區塊大小: {avg_chunk_size:.0f} 字元")
    
    return chunks


def save_to_chroma(chunks):
    """將切片後的資料向量化並存入 ChromaDB"""
    if not chunks:
        print("❌ 沒有資料可以儲存")
        return False
    
    print(f"\n4️⃣  向量化並存入 ChromaDB...")
    print(f"   🤖 Embedding Model: {OLLAMA_EMBED_MODEL}")
    print(f"   🌐 Ollama URL: {OLLAMA_BASE_URL}")
    print(f"   💾 資料庫路徑: {CHROMA_PATH}")
    
    # 檢查 Ollama 是否可用
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  警告: 無法連接到 Ollama ({OLLAMA_BASE_URL})")
            print("   請確認 Ollama 已啟動，並已下載模型:")
            print(f"   ollama pull {OLLAMA_EMBED_MODEL}")
    except Exception as e:
        print(f"⚠️  警告: 無法連接到 Ollama: {e}")
        print("   請確認 Ollama 已啟動")
    
    try:
        # 建立 Embedding 函數
        print(f"\n   🔄 初始化 Embedding 模型...")
        embedding_function = OllamaEmbeddings(
            model=OLLAMA_EMBED_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        
        # 測試 Embedding（確保模型可用）
        print(f"   🧪 測試 Embedding...")
        test_embedding = embedding_function.embed_query("測試")
        print(f"   ✅ Embedding 維度: {len(test_embedding)}")
        
        # 如果資料庫已存在，先刪除舊的
        if os.path.exists(CHROMA_PATH):
            print(f"   🗑️  刪除舊資料庫...")
            import shutil
            shutil.rmtree(CHROMA_PATH)
        
        # 建立並持久化資料庫
        print(f"\n   💾 開始向量化並儲存（這可能需要一些時間）...")
        print(f"   ⏳ 處理 {len(chunks)} 個區塊...")
        
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            persist_directory=CHROMA_PATH
        )
        
        # 驗證資料庫
        collection_count = db._collection.count()
        print(f"\n   ✅ 資料庫建置完成！")
        print(f"   📊 儲存的向量數量: {collection_count}")
        print(f"   💾 資料庫位置: {os.path.abspath(CHROMA_PATH)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 建立資料庫時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    chunks = load_and_chunk_data()
    if chunks:
        success = save_to_chroma(chunks)
        if success:
            print("\n" + "=" * 60)
            print("🎉 RAG 資料庫建置成功！")
            print("=" * 60)
            print(f"\n下一步：執行 3_chat_demo.py 開始對話測試")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ RAG 資料庫建置失敗")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 無法載入資料，請檢查輸入檔案")
        print("=" * 60)


if __name__ == "__main__":
    main()







