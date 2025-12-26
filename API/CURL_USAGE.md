# RAG LLM API - curl 使用指南

本文件說明如何使用 `curl` 命令與 RAG LLM API 伺服器互動。

## 基本資訊

- **預設伺服器位址**: `http://localhost:5002`
- **預設主機**: `0.0.0.0` (監聽所有網路介面)
- **預設埠號**: `5002`

## 1. 健康檢查 (Health Check)

檢查伺服器是否正常運行：

```bash
curl -X GET http://localhost:5002/health
```

**回應範例**:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "timestamp": 1234567890.123
}
```

## 2. 初始化 RAG 系統

初始化 RAG 系統（如果尚未初始化）：

```bash
curl -X POST http://localhost:5002/api/rag-llm/init \
  -H "Content-Type: application/json"
```

**回應範例**:
```json
{
  "success": true,
  "rag_initialized": true,
  "message": "RAG system initialized successfully"
}
```

## 3. 主要查詢端點 (Query)

### 3.1 基本查詢（無語調轉換）

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "my_session_123",
    "include_history": true,
    "convert_tone": false
  }'
```

### 3.2 查詢（含語調轉換）

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "my_session_123",
    "include_history": true,
    "user_description": "a young boy wearing glasses, and is smiling",
    "convert_tone": true
  }'
```

### 3.3 查詢（使用預設語調）

```bash
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院的主要研究領域有哪些？",
    "session_id": "my_session_123"
  }'
```

**參數說明**:
- `text_user_msg` (必填): 使用者的問題
- `session_id` (選填): 會話 ID，預設為 "default"
- `include_history` (選填): 是否包含歷史對話，預設為 `true`
- `user_description` (選填): 視覺描述（例如："a young boy wearing glasses"），用於動態語調選擇
- `tone` (選填，已棄用): 語調類型，建議使用 `user_description` 代替
- `convert_tone` (選填): 是否轉換語調，預設為 `false`

**注意**: 此端點會回傳串流回應，回應會以文字形式逐步回傳，最後以 `END_FLAG` 標記結束。

## 4. 查詢（含自動語調轉換）

使用專用的查詢端點，自動進行語調轉換：

```bash
curl -X POST http://localhost:5002/api/rag-llm/query-with-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院成立於哪一年？",
    "session_id": "my_session_123",
    "include_history": true,
    "user_description": "an elderly person with gray hair",
    "convert_tone": true
  }'
```

## 5. 語調轉換端點

單獨轉換文字的語調：

### 5.1 串流模式（預設）

```bash
curl -X POST http://localhost:5002/api/rag-llm/convert-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text": "工研院是台灣最大的應用研究機構，成立於1973年。",
    "tone": "child_friendly",
    "stream": true,
    "user_description": "a young child",
    "user_msg": "工研院是什麼？"
  }'
```

### 5.2 非串流模式

```bash
curl -X POST http://localhost:5002/api/rag-llm/convert-tone \
  -H "Content-Type: application/json" \
  -d '{
    "text": "工研院是台灣最大的應用研究機構，成立於1973年。",
    "tone": "elder_friendly",
    "stream": false
  }'
```

**參數說明**:
- `text` (必填): 要轉換的文字
- `tone` (選填): 目標語調，預設為 `child_friendly`
- `stream` (選填): 是否使用串流模式，預設為 `true`
- `user_description` (選填): 視覺描述
- `user_msg` (選填): 原始使用者訊息

**可用語調**:
- `child_friendly`: 兒童友善
- `elder_friendly`: 長者友善
- `professional_friendly`: 專業友善
- `casual_friendly`: 輕鬆友善（預設）

## 6. 會話歷史管理

### 6.1 取得會話歷史

```bash
curl -X GET http://localhost:5002/api/rag-llm/sessions/my_session_123/history
```

**回應範例**:
```json
{
  "session_id": "my_session_123",
  "history": [
    {"role": "user", "content": "工研院是什麼？"},
    {"role": "assistant", "content": "工研院是..."}
  ],
  "message_count": 2
}
```

### 6.2 清除會話歷史

```bash
curl -X DELETE http://localhost:5002/api/rag-llm/sessions/my_session_123/history
```

**回應範例**:
```json
{
  "session_id": "my_session_123",
  "message": "History cleared"
}
```

## 7. 關閉連線

優雅地關閉連線並清理會話資料：

```bash
curl -X POST http://localhost:5002/api/rag-llm/close \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session_123"
  }'
```

**回應範例**:
```json
{
  "success": true,
  "session_id": "my_session_123",
  "message": "Connection closed successfully",
  "session_existed": true,
  "messages_cleared": 4,
  "timestamp": 1234567890.123
}
```

## 8. 模型預熱 (Warmup)

預先載入嵌入模型和 LLM 模型，減少首次請求的延遲：

```bash
curl -X POST http://localhost:5002/api/rag-llm/warmup \
  -H "Content-Type: application/json"
```

**回應範例**:
```json
{
  "embedding_model": {
    "status": "success",
    "message": "Embedding model warmed up successfully",
    "time_ms": 1234.56,
    "test_query": "ITRI warmup test",
    "results_found": 1
  },
  "llm_model": {
    "status": "success",
    "message": "LLM model warmed up successfully",
    "time_ms": 5678.90,
    "test_response": "OK"
  },
  "overall_success": true,
  "timestamp": 1234567890.123
}
```

## 完整使用範例

### 範例 1: 完整對話流程

```bash
# 1. 檢查伺服器狀態
curl -X GET http://localhost:5002/health

# 2. 初始化 RAG 系統（如果需要）
curl -X POST http://localhost:5002/api/rag-llm/init

# 3. 發送第一個問題
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是什麼？",
    "session_id": "demo_session_001",
    "convert_tone": true,
    "user_description": "a young student"
  }'

# 4. 發送後續問題（會使用歷史對話）
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院有哪些主要的研究領域？",
    "session_id": "demo_session_001",
    "convert_tone": true,
    "user_description": "a young student"
  }'

# 5. 查看對話歷史
curl -X GET http://localhost:5002/api/rag-llm/sessions/demo_session_001/history

# 6. 關閉連線
curl -X POST http://localhost:5002/api/rag-llm/close \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo_session_001"}'
```

### 範例 2: 處理串流回應

由於查詢端點會回傳串流回應，您可以使用以下方式處理：

```bash
# 將回應儲存到檔案
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "請介紹工研院",
    "session_id": "stream_demo"
  }' \
  --no-buffer \
  -o response.txt

# 或者即時顯示（使用 --no-buffer 確保即時輸出）
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "請介紹工研院",
    "session_id": "stream_demo"
  }' \
  --no-buffer
```

### 範例 3: 使用不同的語調

```bash
# 兒童友善語調
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是做什麼的？",
    "session_id": "child_demo",
    "user_description": "a 5-year-old child",
    "convert_tone": true
  }'

# 長者友善語調
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{
    "text_user_msg": "工研院是做什麼的？",
    "session_id": "elder_demo",
    "user_description": "an elderly person",
    "convert_tone": true
  }'
```

## 錯誤處理

如果請求失敗，API 會回傳錯誤訊息：

```bash
# 範例：缺少必要參數
curl -X POST http://localhost:5002/api/rag-llm/query \
  -H "Content-Type: application/json" \
  -d '{}'
```

**錯誤回應範例**:
```json
{
  "error": "text_user_msg is required"
}
```

## 注意事項

1. **串流回應**: 查詢端點會回傳串流回應，最後以 `END_FLAG` 標記結束
2. **會話管理**: 使用相同的 `session_id` 可以維持對話歷史
3. **語調轉換**: 當 `convert_tone=true` 時，系統會根據 `user_description` 自動選擇合適的語調
4. **預熱**: 首次請求可能較慢，建議先呼叫 `/api/rag-llm/warmup` 端點
5. **CORS**: API 已啟用 CORS，可以從瀏覽器直接呼叫

## 疑難排解

### 檢查伺服器是否運行

```bash
curl -X GET http://localhost:5002/health
```

### 檢查 RAG 系統是否已初始化

```bash
curl -X GET http://localhost:5002/health | jq '.rag_initialized'
```

### 如果 RAG 未初始化，手動初始化

```bash
curl -X POST http://localhost:5002/api/rag-llm/init
```

### 檢查 Ollama 服務是否運行

```bash
curl http://localhost:11435/api/tags
```

## 相關文件

- API 詳細規格: 請參考 `rag_llm_api.py` 原始碼
- 啟動腳本: `start_servers.sh`
- 快速開始指南: `QUICK_START.md`

