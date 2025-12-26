# ITRI 資料爬蟲與 RAG 系統 🕷️

這是一套完整的、模組化的程式碼系統，用於爬取工研院相關資料並建立 RAG (Retrieval-Augmented Generation) 對話系統。

## 📋 系統架構

為了讓您容易操作，我將其拆分為三個步驟：

1. **爬蟲資料搜集** (`1_crawl_data.py`) - 使用 Scrapy 爬取資料
2. **建立向量資料庫** (`2_build_rag.py`) - 使用 LangChain + ChromaDB 建立 RAG 資料庫
3. **對話測試** (`3_chat_demo.py`) - 使用建置好的資料庫進行對話

---

## 🚀 快速開始

### 步驟 0: 準備工作

#### 1. 安裝 Python 套件

```bash
cd dataset_20251221
pip install -r requirements.txt
```

#### 2. 準備 Ollama 模型

請在終端機執行以下指令下載模型：

```bash
# 下載 Embedding 模型（用於向量化）
ollama pull bge-m3

# 或使用其他模型
ollama pull nomic-embed-text

# 下載 LLM 模型（用於回答）
ollama pull llama3

# 或使用其他模型
ollama pull mistral
ollama pull gemma
```

#### 3. 確認 Ollama 已啟動

```bash
# 檢查 Ollama 是否運行
curl http://localhost:11434/api/tags
```

如果沒有回應，請啟動 Ollama：

```bash
ollama serve
```

---

### 步驟 1: 資料搜集

執行爬蟲腳本，爬取維基百科和工研院官網資料：

```bash
python 1_crawl_data.py
```

**輸出：**
- `crawled_data/itri_raw_data.json` - 爬取的原始資料（JSON 格式）

**預估時間：** 5-15 分鐘（取決於網路速度和網站結構）

**功能：**
- ✅ 爬取維基百科工研院相關頁面（BFS 深度 2）
- ✅ 爬取工研院官網主要頁面
- ✅ 自動過濾相關內容
- ✅ 保留階層資訊（hierarchy）和來源資訊

---

### 步驟 2: 建立 RAG 資料庫

讀取爬取的資料，進行切片和向量化，存入 ChromaDB：

```bash
python 2_build_rag.py
```

**輸出：**
- `chroma_db_itri/` - ChromaDB 向量資料庫目錄

**預估時間：** 5-20 分鐘（取決於資料量和 Ollama 效能）

**功能：**
- ✅ 使用 LangChain 進行文件切片（Chunking）
- ✅ 使用 Ollama BGE-M3 進行向量化（Embedding）
- ✅ 儲存到 ChromaDB 持久化資料庫
- ✅ 保留完整的 metadata（來源、標題、URL 等）

**重要設定：**
- **Chunk Size:** 500 字元
- **Chunk Overlap:** 100 字元（確保上下文連貫）
- **Embedding Model:** `bge-m3`（可在腳本中修改）

---

### 步驟 3: 對話測試

使用建置好的 RAG 資料庫進行對話：

```bash
python 3_chat_demo.py
```

**功能：**
- ✅ 連接 ChromaDB 向量資料庫
- ✅ 使用相似度檢索相關知識片段
- ✅ 使用 LLM 生成回答
- ✅ 顯示來源資訊（hierarchy）

**使用方式：**
```
❓ 請輸入問題 (e.g., 工研院的2030技術策略是什麼?): 工研院成立於哪一年？
🤖 思考中...
📝 回答: 工研院成立於1973年...
```

輸入 `exit` 或 `quit` 離開。

---

## 📁 專案結構

```
dataset_20251221/
├── 1_crawl_data.py          # 步驟 1: 資料爬取
├── 2_build_rag.py           # 步驟 2: 建立 RAG 資料庫
├── 3_chat_demo.py           # 步驟 3: 對話測試
├── requirements.txt         # Python 依賴套件
├── README.md               # 本說明文件
├── crawled_data/           # 爬取的原始資料（自動建立）
│   └── itri_raw_data.json
└── chroma_db_itri/         # ChromaDB 向量資料庫（自動建立）
```

---

## 🔧 系統特色

### 1. 階層性資訊保留

在爬蟲階段，系統會保留完整的階層資訊（hierarchy），例如：
- `Wiki > 工業技術研究院`
- `ITRI > Official > 2030技術策略`

這讓使用者在對話時可以知道資訊來自哪個具體頁面。

### 2. Overlap Chunking

使用 `chunk_overlap=100` 確保關鍵資訊不會被切斷在兩個區塊中間，提高檢索準確度。

### 3. 多模型支援

- **Embedding 模型：** `bge-m3`（繁體中文優化）、`nomic-embed-text`
- **LLM 模型：** `llama3`、`mistral`、`gemma` 等

可在腳本中輕鬆修改模型設定。

### 4. 完整的錯誤處理

每個步驟都包含：
- 輸入驗證
- 錯誤提示
- 進度顯示
- 結果統計

---

## 📊 資料格式

### 爬取的原始資料格式

```json
{
  "source": "Wikipedia",
  "title": "工業技術研究院",
  "url": "https://zh.wikipedia.org/...",
  "content": "工研院成立於1973年...",
  "hierarchy": "Wiki > 工業技術研究院",
  "depth": 0,
  "language": "zh-tw",
  "crawled_at": "2025-12-21T10:30:00"
}
```

### ChromaDB 儲存格式

每個向量包含：
- **page_content:** 文本內容
- **metadata:**
  - `source`: 資料來源
  - `title`: 標題
  - `url`: 原始 URL
  - `hierarchy`: 階層資訊
  - `language`: 語言
  - `crawled_at`: 爬取時間
  - `depth`: 爬取深度
  - `doc_id`: 文件 ID

---

## 🛠️ 進階設定

### 修改 Chunking 參數

在 `2_build_rag.py` 中修改：

```python
CHUNK_SIZE = 500      # 調整區塊大小
CHUNK_OVERLAP = 100   # 調整重疊大小
```

### 修改檢索數量

在 `3_chat_demo.py` 中修改：

```python
TOP_K = 5  # 檢索前 K 個最相關的片段
```

### 修改模型

在各個腳本中修改：

```python
# Embedding 模型
EMBED_MODEL = "bge-m3"  # 或 "nomic-embed-text"

# LLM 模型
LLM_MODEL = "llama3"    # 或 "mistral", "gemma"
```

---

## ❓ 常見問題

### Q: 爬蟲執行時間很長？

A: 可以調整 `1_crawl_data.py` 中的限制：
- 減少 `max_pages` 參數
- 調整 `DEPTH_LIMIT` 設定

### Q: Ollama 連接失敗？

A: 確認：
1. Ollama 已啟動：`ollama serve`
2. 模型已下載：`ollama pull <model_name>`
3. 端口正確：預設為 `http://localhost:11434`

### Q: 資料庫建置失敗？

A: 檢查：
1. 輸入檔案是否存在且格式正確
2. Ollama 是否正常運行
3. 模型是否已正確下載

### Q: 回答品質不佳？

A: 嘗試：
1. 增加 `TOP_K` 檢索更多相關片段
2. 調整 Chunk Size 和 Overlap
3. 使用更強大的 LLM 模型
4. 優化 Prompt 模板

---

## 📝 授權與使用

本系統僅供學習和研究使用。請遵守：
- 網站的使用條款
- robots.txt 規範
- 資料使用規範

---

## 🎯 下一步

完成基本設定後，您可以：
1. 擴展爬蟲範圍（新增更多資料源）
2. 優化 Prompt 模板（提升回答品質）
3. 整合到 Web 應用（使用 Flask/FastAPI）
4. 添加更多功能（如對話歷史、多輪對話等）

---

## 📞 支援

如有問題，請檢查：
1. 所有依賴套件是否已安裝
2. Ollama 是否正常運行
3. 模型是否已正確下載
4. 輸入檔案是否存在且格式正確

祝使用愉快！🚀







