#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI Chat Demo - Step 3: Chat with RAG
使用建置好的 RAG 資料庫進行對話測試
"""

import time
from datetime import datetime

try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.chat_models import ChatOllama
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
except ImportError as e:
    print("❌ 缺少必要的套件，請先安裝：")
    print("   pip install langchain langchain-community chromadb")
    print(f"\n錯誤詳情: {e}")
    exit(1)

# --- 設定 ---
CHROMA_PATH = "./chroma_db_itri"
EMBED_MODEL = "bge-m3"  # 必須與建置資料庫時使用的模型相同
LLM_MODEL = "llama3.1:70b-instruct-q4-0"    # 或使用其他模型如 "mistral", "gemma"
OLLAMA_BASE_URL = "http://localhost:11435"

# RAG 參數
TOP_K = 5  # 檢索前 K 個最相關的片段


def format_docs(docs):
    """將檢索到的多個區塊組合成一段文字，並附上來源"""
    formatted_content = []
    for i, doc in enumerate(docs):
        source_info = f"[來源 {i+1}: {doc.metadata.get('hierarchy', 'Unknown')}]"
        title_info = f"標題: {doc.metadata.get('title', 'Untitled')}"
        formatted_content.append(f"{source_info}\n{title_info}\n{doc.page_content}")
    return "\n\n".join(formatted_content)


def check_ollama_connection():
    """檢查 Ollama 連接"""
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            # 檢查必要的模型
            missing_models = []
            if EMBED_MODEL not in model_names:
                missing_models.append(EMBED_MODEL)
            if LLM_MODEL not in model_names:
                missing_models.append(LLM_MODEL)
            
            if missing_models:
                print(f"⚠️  警告: 以下模型尚未下載:")
                for model in missing_models:
                    print(f"   - {model}")
                print(f"\n請執行以下指令下載模型:")
                for model in missing_models:
                    print(f"   ollama pull {model}")
                return False
            
            return True
        else:
            print(f"❌ 無法連接到 Ollama ({OLLAMA_BASE_URL})")
            return False
    except Exception as e:
        print(f"❌ 無法連接到 Ollama: {e}")
        print(f"   請確認 Ollama 已啟動並運行在 {OLLAMA_BASE_URL}")
        return False


def check_database():
    """檢查資料庫是否存在"""
    import os
    if not os.path.exists(CHROMA_PATH):
        print(f"❌ 找不到資料庫: {CHROMA_PATH}")
        print("   請先執行 2_build_rag.py 建立資料庫")
        return False
    return True


def main():
    """主函數"""
    print("=" * 60)
    print("🤖 ITRI AI 導覽員 - RAG Chat Demo")
    print("=" * 60)
    
    # 檢查資料庫
    if not check_database():
        return
    
    # 檢查 Ollama 連接
    if not check_ollama_connection():
        return
    
    print(f"\n🚀 啟動工研院 AI 導覽員...")
    print(f"   📚 資料庫: {CHROMA_PATH}")
    print(f"   🤖 Embedding Model: {EMBED_MODEL}")
    print(f"   💬 LLM Model: {LLM_MODEL}")
    print(f"   🔍 檢索數量: Top {TOP_K}")
    
    try:
        # 1. 連接資料庫
        print(f"\n1️⃣  連接向量資料庫...")
        embedding_func = OllamaEmbeddings(
            model=EMBED_MODEL,
            base_url=OLLAMA_BASE_URL
        )
        
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embedding_func
        )
        
        # 檢查資料庫中的文件數量
        collection_count = db._collection.count()
        print(f"   ✅ 資料庫連接成功")
        print(f"   📊 資料庫中的向量數量: {collection_count}")
        
        if collection_count == 0:
            print("   ⚠️  警告: 資料庫為空，請重新建置資料庫")
            return
        
        # 建立檢索器
        retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": TOP_K}
        )
        print(f"   ✅ 檢索器建立完成")
        
        # 2. 設定 LLM
        print(f"\n2️⃣  初始化 LLM...")
        llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7
        )
        print(f"   ✅ LLM 初始化完成")
        
        # 3. 設計 Prompt
        print(f"\n3️⃣  設定 Prompt 模板...")
        template = """你是一位專業的「工研院 (ITRI) 導覽員」。
請根據以下提供的背景知識 (Context) 來回答使用者的問題。

重要原則：
- 如果知識庫中沒有答案，請誠實說不知道，不要編造事實
- 回答時請語氣親切、專業，並盡量引用來源
- 優先使用背景知識中的資訊，不要使用外部知識
- 如果資訊不確定或過時，請明確說明

背景知識 Context:
{context}

使用者問題 Question: 
{question}

回答 Answer (請用繁體中文回答):"""
        
        prompt = ChatPromptTemplate.from_template(template)
        print(f"   ✅ Prompt 模板設定完成")
        
        # 4. 建立 Chain
        print(f"\n4️⃣  建立 RAG Chain...")
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print(f"   ✅ RAG Chain 建立完成")
        
        print("\n" + "=" * 60)
        print("✅ 導覽員準備就緒！")
        print("=" * 60)
        print("💡 提示: 輸入 'exit' 或 'quit' 離開")
        print("=" * 60)
        
        # 5. 互動迴圈
        conversation_count = 0
        while True:
            print()
            query = input("❓ 請輸入問題 (e.g., 工研院的2030技術策略是什麼?): ").strip()
            
            if query.lower() in ['exit', 'quit', '離開', '退出']:
                print("\n👋 感謝使用，再見！")
                break
            
            if not query:
                print("⚠️  請輸入有效的問題")
                continue
            
            conversation_count += 1
            print(f"\n🤖 思考中... (問題 #{conversation_count})")
            start_time = time.time()
            
            try:
                # 執行 RAG
                response = rag_chain.invoke(query)
                
                elapsed_time = time.time() - start_time
                
                print(f"\n{'='*60}")
                print("📝 回答:")
                print(f"{'='*60}")
                print(response)
                print(f"{'='*60}")
                print(f"⏱️  耗時: {elapsed_time:.2f} 秒")
                print(f"{'='*60}")
                
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                print("   請檢查 Ollama 是否正常運行，或模型是否已正確下載")
        
    except Exception as e:
        print(f"\n❌ 初始化失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()







