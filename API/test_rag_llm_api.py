#!/usr/bin/env python3
"""
RAG LLM API 測試腳本

這個腳本示範如何使用 Python 與 RAG LLM API 伺服器互動，
發送查詢請求並接收串流回應。
"""

import requests
import json
import sys
import argparse
from typing import Optional, Dict, Any


class RAGLLMAPIClient:
    """RAG LLM API 客戶端"""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        """
        初始化 API 客戶端
        
        Args:
            base_url: API 伺服器基礎 URL，預設為 http://localhost:5002
        """
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> Dict[str, Any]:
        """
        檢查伺服器健康狀態
        
        Returns:
            健康狀態資訊字典
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 健康檢查失敗: {e}")
            return {}
    
    def query(
        self,
        text_user_msg: str,
        session_id: str = "default",
        include_history: bool = True,
        user_description: str = "",
        convert_tone: bool = False,
        stream: bool = True
    ) -> str:
        """
        發送查詢請求到 RAG LLM API
        
        Args:
            text_user_msg: 使用者的問題訊息
            session_id: 會話 ID，用於維持對話歷史
            include_history: 是否包含歷史對話
            user_description: 使用者視覺描述（用於語調選擇）
            convert_tone: 是否轉換語調
            stream: 是否使用串流模式（預設為 True）
        
        Returns:
            完整的回應文字（串流模式下會逐步顯示）
        """
        url = f"{self.base_url}/api/rag-llm/query"
        
        payload = {
            "text_user_msg": text_user_msg,
            "session_id": session_id,
            "include_history": include_history,
            "convert_tone": convert_tone
        }
        
        # 只有在提供 user_description 時才加入
        if user_description:
            payload["user_description"] = user_description
        
        try:
            if stream:
                # 串流模式：逐步接收並顯示回應
                print(f"📤 發送請求到: {url}")
                print(f"📝 問題: {text_user_msg}")
                print(f"🆔 會話 ID: {session_id}")
                if user_description:
                    print(f"👤 使用者描述: {user_description}")
                print(f"🎨 語調轉換: {convert_tone}")
                print("\n" + "="*70)
                print("📥 回應內容:")
                print("="*70 + "\n")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    stream=True,
                    timeout=None  # 串流請求可能需要較長時間
                )
                response.raise_for_status()
                
                # 處理串流回應
                full_response = ""
                chunk_count = 0
                
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    chunk_count += 1
                    
                    # 檢查是否為結束標記
                    if line == "END_FLAG":
                        print("\n" + "="*70)
                        print(f"✅ 回應完成（共接收 {chunk_count} 個區塊）")
                        print("="*70)
                        break
                    
                    # 檢查錯誤訊息
                    if line.startswith("ERROR:"):
                        print(f"\n❌ 錯誤: {line}")
                        return None
                    
                    # 顯示並累積回應內容
                    print(line, end='', flush=True)
                    full_response += line
                
                return full_response
            else:
                # 非串流模式（如果 API 支援）
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                response.raise_for_status()
                return response.text
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 無法連接到伺服器 {self.base_url}")
            print("   請確認 RAG LLM API 伺服器是否正在運行")
            return None
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 請求失敗: {e}")
            if hasattr(e.response, 'text'):
                print(f"   錯誤詳情: {e.response.text}")
            return None
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        取得會話歷史
        
        Args:
            session_id: 會話 ID
        
        Returns:
            會話歷史資訊字典
        """
        try:
            url = f"{self.base_url}/api/rag-llm/sessions/{session_id}/history"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 取得會話歷史失敗: {e}")
            return None
    
    def clear_session_history(self, session_id: str) -> bool:
        """
        清除會話歷史
        
        Args:
            session_id: 會話 ID
        
        Returns:
            是否成功清除
        """
        try:
            url = f"{self.base_url}/api/rag-llm/sessions/{session_id}/history"
            response = requests.delete(url, timeout=5)
            response.raise_for_status()
            result = response.json()
            print(f"✅ {result.get('message', 'History cleared')}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ 清除會話歷史失敗: {e}")
            return False
    
    def close_session(self, session_id: str) -> bool:
        """
        關閉會話並清理資源
        
        Args:
            session_id: 會話 ID
        
        Returns:
            是否成功關閉
        """
        try:
            url = f"{self.base_url}/api/rag-llm/close"
            payload = {"session_id": session_id}
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ {result.get('message', 'Connection closed')}")
            if 'messages_cleared' in result:
                print(f"   已清除 {result['messages_cleared']} 則訊息")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ 關閉會話失敗: {e}")
            return False
    
    def initialize_rag(self) -> bool:
        """
        初始化 RAG 系統
        
        Returns:
            是否成功初始化
        """
        try:
            url = f"{self.base_url}/api/rag-llm/init"
            response = requests.post(url, timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                print("✅ RAG 系統初始化成功")
                return True
            else:
                print(f"❌ RAG 系統初始化失敗: {result.get('message', 'Unknown error')}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 初始化 RAG 系統失敗: {e}")
            return False
    
    def warmup_models(self) -> Optional[Dict[str, Any]]:
        """
        預熱模型
        
        Returns:
            預熱結果字典
        """
        try:
            url = f"{self.base_url}/api/rag-llm/warmup"
            response = requests.post(url, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 模型預熱失敗: {e}")
            return None


def main():
    """主函數：示範如何使用 API 客戶端"""
    
    # 解析命令行參數
    parser = argparse.ArgumentParser(
        description='RAG LLM API 測試客戶端',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  python3 test_rag_llm_api.py --usr_msg "你好！" --session_id "my_session_1"
  python3 test_rag_llm_api.py -usr_msg "工研院在哪裡？" -sid "test_session"
  python3 test_rag_llm_api.py  # 使用預設值
        """
    )
    parser.add_argument(
        '-usr_msg', '--usr_msg',
        type=str,
        default="你好！",
        help='使用者訊息內容（預設: "你好！"）'
    )
    parser.add_argument(
        '-sid', '--session_id',
        type=str,
        default="my_session_1",
        help='會話 ID（預設: "my_session_1"）'
    )
    parser.add_argument(
        '--user_description',
        type=str,
        default="a young boy wearing glasses, and is smiling",
        help='使用者視覺描述（預設: "a young boy wearing glasses, and is smiling"）'
    )
    parser.add_argument(
        '--convert_tone',
        action='store_true',
        default=True,
        help='是否轉換語調（預設: True）'
    )
    parser.add_argument(
        '--no_convert_tone',
        dest='convert_tone',
        action='store_false',
        help='不轉換語調'
    )
    parser.add_argument(
        '--base_url',
        type=str,
        default="http://localhost:5002",
        help='API 伺服器基礎 URL（預設: http://localhost:5002）'
    )
    
    args = parser.parse_args()
    
    # 建立 API 客戶端
    client = RAGLLMAPIClient(base_url=args.base_url)
    
    # 檢查伺服器狀態
    print("🔍 檢查伺服器狀態...")
    health = client.health_check()
    if health:
        print(f"✅ 伺服器狀態: {health.get('status', 'unknown')}")
        print(f"   RAG 已初始化: {health.get('rag_initialized', False)}")
    else:
        print("❌ 無法連接到伺服器")
        print("   請確認 RAG LLM API 伺服器是否正在運行")
        print("   啟動命令: python3 rag_llm_api.py --auto-init")
        sys.exit(1)
    
    print("\n" + "="*70)
    
    # 如果 RAG 未初始化，嘗試初始化
    if not health.get('rag_initialized', False):
        print("⚠️  RAG 系統尚未初始化，正在初始化...")
        if not client.initialize_rag():
            print("❌ RAG 初始化失敗，但將繼續嘗試查詢...")
    
    print("\n" + "="*70)
    
    # 發送查詢請求
    print("📤 發送查詢請求...\n")
    print(f"📝 使用者訊息: {args.usr_msg}")
    print(f"🆔 會話 ID: {args.session_id}")
    print(f"👤 使用者描述: {args.user_description}")
    print(f"🎨 語調轉換: {args.convert_tone}\n")
    
    response = client.query(
        text_user_msg=args.usr_msg,
        session_id=args.session_id,
        include_history=True,
        user_description=args.user_description,
        convert_tone=args.convert_tone
    )
    
    # ===== 舊的硬編碼版本（已註解） =====
    # session_id_now = "my_session_1"
    # response = client.query(
    #     # text_user_msg="哈摟！",
    #     # text_user_msg="可以解釋得更詳細一點嗎？",
    #     text_user_msg="哇，我剛剛看到你們博物館的入口有一顆大樹，是有什麼功能嗎？",
    #     # text_user_msg="嗯！很厲害。然後，我想要知道工研院現在的院長是誰啊？",
    #     # text_user_msg="工研院在哪裡啊？",
    #     # text_user_msg="喔，那除了總部，還有其他的分部嗎？",
    #     session_id=session_id_now,
    #     include_history=True,
    #     # user_description="an adult male dressing professional",
    #     # user_description="an adult male dressing casual",
    #     user_description="a young boy wearing glasses, and is smiling",
    #     # user_description="an old woman dressing elegant, and is smiling",
    #     convert_tone=True
    # )
    
    if response is None:
        print("\n❌ 查詢失敗")
        sys.exit(1)
    
    # 顯示會話歷史
    print("\n" + "="*70)
    print("📜 查看會話歷史...\n")
    history = client.get_session_history(args.session_id)
    if history:
        print(f"會話 ID: {history.get('session_id')}")
        print(f"訊息數量: {history.get('message_count', 0)}")
        if history.get('history'):
            print("\n對話歷史:")
            for i, msg in enumerate(history['history'], 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]  # 只顯示前 100 字元
                print(f"  {i}. [{role}]: {content}...")
    
    # 可選：關閉會話
    # print("\n" + "="*70)
    # print("👋 關閉會話...\n")
    # client.close_session("my_session_123")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程式已中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

