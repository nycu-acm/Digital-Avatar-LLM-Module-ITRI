# ITRI Scrapy Crawler 🕷️

基於 Scrapy 框架的工業技術研究院 (ITRI) 網路資料爬蟲系統，專為收集 ITRI 相關的技術資訊、新聞報導和研究內容而設計。

## 🎯 專案特色

- **多源爬取**: 支援 ITRI 官網、Wikipedia、新聞媒體等多個資料源
- **智慧過濾**: 自動識別和過濾 ITRI 相關內容
- **資料清理**: 內建資料驗證和清理管道
- **去重機制**: 自動過濾重複內容
- **品質評分**: 為每個內容項目計算品質分數
- **結構化輸出**: 生成 JSON 格式的結構化資料
- **詳細報告**: 提供完整的爬取統計和品質報告

## 📁 專案結構

```
dataset_202412_classic/
├── itri_scrapy_crawler/           # Scrapy 專案目錄
│   ├── itri_scrapy_crawler/
│   │   ├── spiders/               # 爬蟲程式
│   │   │   ├── itri_official.py   # ITRI 官網爬蟲
│   │   │   ├── itri_wikipedia.py  # Wikipedia 爬蟲
│   │   │   └── itri_news.py       # 新聞媒體爬蟲
│   │   ├── items.py               # 資料項目定義
│   │   ├── pipelines.py           # 資料處理管道
│   │   ├── settings.py            # 爬蟲設定
│   │   └── middlewares.py         # 中介軟體
│   └── scrapy.cfg                 # Scrapy 設定檔
├── run_itri_crawler.py            # 主要執行腳本
├── requirements.txt               # 依賴套件
├── README.md                      # 說明文件
└── crawled_data/                  # 輸出資料目錄
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd dataset_202412_classic
pip install -r requirements.txt
```

### 2. 檢查設定

```bash
python run_itri_crawler.py --check
```

### 3. 查看可用爬蟲

```bash
python run_itri_crawler.py --list
```

### 4. 執行所有爬蟲

```bash
python run_itri_crawler.py
```

### 5. 執行特定爬蟲

```bash
# 只爬取 ITRI 官網
python run_itri_crawler.py --spiders itri_official

# 爬取官網和 Wikipedia
python run_itri_crawler.py --spiders itri_official itri_wikipedia
```

## 🕷️ 爬蟲說明

### 1. ITRI 官網爬蟲 (`itri_official`)
- **目標**: https://www.itri.org.tw
- **內容**: 官方新聞、研究成果、技術服務、產業合作資訊
- **預估時間**: 10-15 分鐘
- **特色**: 
  - 智慧內容分類 (新聞/研究/服務)
  - 自動提取部門和聯絡資訊
  - 支援中英文內容

### 2. Wikipedia 爬蟲 (`itri_wikipedia`)
- **目標**: Wikipedia (中文/英文)
- **內容**: ITRI 相關百科條目、技術詞條、相關機構資訊
- **預估時間**: 5-10 分鐘
- **特色**:
  - 使用 Wikipedia API 搜尋
  - 自動追蹤相關連結
  - 過濾非相關內容

### 3. 新聞媒體爬蟲 (`itri_news`)
- **目標**: Google News、科技媒體網站
- **內容**: ITRI 相關新聞報導、媒體報導、產業動態
- **預估時間**: 15-20 分鐘
- **特色**:
  - 多媒體來源整合
  - 新聞類型自動分類
  - 時效性內容優先

## 📊 資料輸出

### 輸出格式
所有爬取的資料都會以 JSON 格式儲存，每個項目包含以下欄位：

```json
{
  "id": "唯一識別碼",
  "title": "標題",
  "content": "清理後的內容",
  "url": "原始網址",
  "source": "資料來源",
  "language": "語言 (zh-tw/en)",
  "content_type": "內容類型",
  "crawled_at": "爬取時間",
  "category": "分類",
  "tags": ["標籤列表"],
  "summary": "摘要",
  "quality_score": "品質分數 (0-1)",
  "metadata": {
    "research_area": "研究領域",
    "technology_type": "技術類型",
    "keywords": ["關鍵字"]
  }
}
```

### 輸出檔案
```
crawled_data/
├── crawl_20241218_143052/         # 爬取會話目錄
│   ├── itri_official_articles.json    # ITRI 官網內容
│   ├── itri_wikipedia_articles.json   # Wikipedia 內容
│   ├── itri_news_articles.json        # 新聞內容
│   ├── all_articles_combined.json     # 所有內容合併
│   └── crawl_statistics.json          # 詳細統計
├── session_report.md              # 會話報告
├── session_report.json            # 會話報告 (JSON)
└── *.log                          # 爬蟲日誌
```

## ⚙️ 設定選項

### 爬蟲設定 (`settings.py`)
- **DOWNLOAD_DELAY**: 請求間隔 (預設: 2 秒)
- **CONCURRENT_REQUESTS**: 並發請求數 (預設: 16)
- **USER_AGENT**: 使用者代理字串
- **ROBOTSTXT_OBEY**: 遵守 robots.txt (預設: True)

### 自訂設定
```python
# 在 settings.py 中修改
ITRI_CRAWLER_SETTINGS = {
    "MAX_PAGES_PER_SPIDER": 100,      # 每個爬蟲最大頁面數
    "MIN_CONTENT_LENGTH": 50,         # 最小內容長度
    "PREFERRED_LANGUAGES": ["zh-tw", "en"],  # 偏好語言
    "OUTPUT_DIR": "crawled_data",     # 輸出目錄
    "ENHANCE_CONTENT": True,          # 啟用內容增強
}
```

## 🔧 進階使用

### 1. 單獨執行爬蟲
```bash
cd itri_scrapy_crawler
scrapy crawl itri_official
```

### 2. 自訂輸出格式
```bash
scrapy crawl itri_official -o output.json -t json
```

### 3. 調試模式
```bash
scrapy crawl itri_official -L DEBUG
```

### 4. 使用快取 (開發用)
在 `settings.py` 中設定:
```python
HTTPCACHE_ENABLED = True
```

## 📈 資料品質

### 品質控制機制
1. **內容驗證**: 檢查必要欄位和內容長度
2. **去重過濾**: 基於內容雜湊值去除重複
3. **相關性檢查**: 確保內容與 ITRI 相關
4. **品質評分**: 基於多個因子計算品質分數
5. **資料清理**: 移除導航、廣告等雜訊內容

### 品質分數計算
- **基礎分數**: 0.5
- **內容長度**: +0.1 (>200字) +0.1 (>500字) +0.1 (>1000字)
- **ITRI 相關性**: +0.1 (包含 ITRI 關鍵字)
- **技術內容**: +0.1 (包含技術詞彙)
- **結構完整性**: +0.05 (有分類) +0.05 (有標籤)

## 🔗 與 RAG 系統整合

### 整合範例
```python
import json
from your_rag_system import DocumentChunk, RAGPipeline

# 載入爬取的資料
with open('crawled_data/crawl_latest/all_articles_combined.json', 'r') as f:
    itri_data = json.load(f)

# 轉換為 RAG 系統格式
chunks = []
for item in itri_data:
    if item['quality_score'] >= 0.6:  # 只使用高品質內容
        chunk = DocumentChunk(
            content=item['content'],
            chunk_id=item['id'],
            source_file=item['url'],
            metadata={
                'title': item['title'],
                'source': item['source'],
                'summary': item['summary'],
                'tags': item['tags'],
                'quality_score': item['quality_score']
            }
        )
        chunks.append(chunk)

# 建立向量資料庫
pipeline = RAGPipeline()
pipeline.build_vector_store(chunks, collection_name='itri_knowledge_2024')
```

## 🛠️ 故障排除

### 常見問題

1. **Scrapy 未安裝**
   ```bash
   pip install scrapy
   ```

2. **權限錯誤**
   - 確保有寫入 `crawled_data` 目錄的權限
   - 避免使用 sudo 執行

3. **網路連線問題**
   - 檢查網路連線
   - 調整 `DOWNLOAD_DELAY` 設定

4. **記憶體不足**
   - 減少 `CONCURRENT_REQUESTS`
   - 調整 `MEMUSAGE_LIMIT_MB`

### 日誌分析
```bash
# 查看爬蟲日誌
tail -f crawled_data/itri_official.log

# 搜尋錯誤
grep ERROR crawled_data/*.log
```

## 📋 開發指南

### 新增爬蟲
1. 在 `spiders/` 目錄建立新的 `.py` 檔案
2. 繼承適當的 Spider 類別
3. 定義 `start_urls` 和 `parse` 方法
4. 在 `run_itri_crawler.py` 中註冊新爬蟲

### 自訂資料處理
1. 在 `pipelines.py` 中新增處理管道
2. 在 `settings.py` 中註冊管道
3. 設定適當的優先順序

### 測試
```bash
# 執行測試
pytest tests/

# 測試特定爬蟲
scrapy check itri_official
```

## 📜 授權條款

本專案遵循 MIT 授權條款。請確保在使用爬取的資料時遵守各網站的使用條款和 robots.txt 規範。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改善這個專案！

### 開發環境設定
```bash
git clone <repository>
cd dataset_202412_classic
pip install -r requirements.txt
pip install -e .
```

### 程式碼風格
- 使用 Black 進行程式碼格式化
- 使用 flake8 進行程式碼檢查
- 遵循 PEP 8 規範

---

**由 ITRI Scrapy Crawler 生成 - 專為工業技術研究院資料收集而設計** 🤖












