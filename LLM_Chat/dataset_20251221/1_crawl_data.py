#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI Data Crawler - Step 1: Data Collection
使用 Scrapy 爬取工研院相關資料（維基百科 + 官網）
"""

import os
import re
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import HtmlResponse
from datetime import datetime
from urllib.parse import parse_qs, urlparse

# Selenium 支持（可選）
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium 未安裝，將使用標準 HTTP 請求。如需處理動態網頁，請安裝: pip install selenium")

# --- 設定輸出檔案 ---
OUTPUT_DIR = "crawled_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "itri_raw_data.json")

# 確保輸出目錄存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 如果檔案已存在，先備份
if os.path.exists(OUTPUT_FILE):
    backup_file = OUTPUT_FILE.replace(".json", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.rename(OUTPUT_FILE, backup_file)
    print(f"📦 已備份舊檔案至: {backup_file}")


class ItriWikiSpider(CrawlSpider):
    """維基百科工研院相關頁面爬蟲"""
    name = 'wiki_itri'
    allowed_domains = ['zh.wikipedia.org', 'en.wikipedia.org']
    
    # 起始頁面：工研院主頁面
    start_urls = [
        'https://zh.wikipedia.org/zh-tw/工業技術研究院',
        'https://en.wikipedia.org/wiki/Industrial_Technology_Research_Institute',
    ]
    
    # 設定 BFS 爬取規則
    rules = (
        # 允許中文和英文維基頁面，排除特殊頁面（如編輯頁面）
        Rule(
            LinkExtractor(
                allow=(r'/wiki/', r'/zh-tw/', r'/zh-cn/'),
                deny=(r':', r'Special:', r'User:', r'File:', r'Template:', r'Category:', r'Help:')
            ),
            callback='parse_item',
            follow=True
        ),
    )
    
    def parse(self, response):
        """處理起始 URL，也調用 parse_item"""
        print(f"🔍 解析起始 URL: {response.url}")
        # 對於起始 URL，直接調用 parse_item
        yield from self.parse_item(response)
        # 然後繼續跟隨連結（CrawlSpider 會自動處理）

    def parse_item(self, response):
        """解析維基百科頁面內容"""
        # 抓取標題
        title = response.css('h1#firstHeading::text').get()
        if not title:
            title = response.css('h1.firstHeading::text').get()
        if not title:
            # 嘗試其他選擇器
            title = response.css('h1::text').get()
        
        if not title:
            # 如果沒有標題，跳過這個頁面
            return
        
        # 排除表格與導航，只抓主要段落
        # 使用 XPath 提取所有文字節點，更可靠
        content_list = response.xpath('//div[@id="mw-content-text"]//div[@class="mw-parser-output"]//p//text()').getall()
        if not content_list:
            # 嘗試英文版格式
            content_list = response.xpath('//div[@id="content"]//div[@class="mw-parser-output"]//p//text()').getall()
        if not content_list:
            # 嘗試更寬鬆的選擇器
            content_list = response.xpath('//div[@id="mw-content-text"]//p//text()').getall()
        if not content_list:
            # 最後嘗試：直接從 body 提取段落
            content_list = response.xpath('//div[@id="bodyContent"]//p//text()').getall()
        
        # 過濾太短的內容（降低門檻）
        content = " ".join([t.strip() for t in content_list if len(t.strip()) > 3])
        
        # 如果內容太短，嘗試提取更多文字
        if len(content) < 50:
            # 嘗試提取所有段落文字（包括更短的）
            all_text = response.xpath('//div[@id="mw-content-text"]//p//text()').getall()
            content = " ".join([t.strip() for t in all_text if len(t.strip()) > 2])
        
        # 如果還是沒有內容，嘗試從整個內容區域提取
        if len(content) < 30:
            all_text = response.xpath('//div[@id="mw-content-text"]//text()').getall()
            content = " ".join([t.strip() for t in all_text if len(t.strip()) > 2])
            # 過濾掉導航和無用文字
            content = re.sub(r'\[編輯\]|\[edit\]', '', content)
        
        # 檢查是否與工研院相關（簡單關鍵字檢查）
        # 放寬條件：只要標題或內容中包含關鍵字即可
        itri_keywords = ['工研院', 'ITRI', 'Industrial Technology Research', '工業技術研究院', '工業技術', '技術研究院', 'Industrial Technology']
        title_content = (title or '') + ' ' + (content or '')
        is_relevant = any(keyword.lower() in title_content.lower() for keyword in itri_keywords)
        
        # 如果是起始頁面（工研院主頁面），無論如何都要保存
        is_start_page = any(start_url in response.url for start_url in self.start_urls)
        
        # 調試信息
        if is_start_page:
            print(f"📄 處理起始頁面: {response.url}")
            print(f"   標題: {title}")
            print(f"   內容長度: {len(content)}")
        
        # 放寬條件：起始頁面或相關頁面，且內容長度 > 20
        if (is_start_page or is_relevant) and content and len(content) > 20:
            print(f"✅ 保存維基頁面: {title} ({len(content)} 字元)")
            yield {
                'source': 'Wikipedia',
                'title': title.strip() if title else 'Untitled',
                'url': response.url,
                'content': content,
                'hierarchy': f"Wiki > {title.strip() if title else 'Untitled'}",
                'depth': response.meta.get('depth', 0),
                'language': 'zh-tw' if 'zh.wikipedia.org' in response.url else 'en',
                'crawled_at': datetime.now().isoformat()
            }
        else:
            # 調試信息：為什麼沒有保存
            if is_start_page:
                print(f"⚠️  起始頁面未保存: 內容長度={len(content)}, 相關性={is_relevant}")
            elif not is_relevant:
                print(f"⚠️  頁面不相關: {title} (URL: {response.url})")
            elif not content or len(content) <= 20:
                print(f"⚠️  內容太短: {title} (長度: {len(content)})")


class ItriOfficialSpider(scrapy.Spider):
    """工研院官網爬蟲"""
    name = 'official_itri'
    allowed_domains = ['itri.org.tw', 'www.itri.org.tw']
    
    # 從首頁和網站地圖開始
    start_urls = [
        'https://www.itri.org.tw/',
        'https://www.itri.org.tw/ListStyle.aspx?DisplayStyle=SiteMap&SiteID=1'
    ]

    def __init__(self, *args, **kwargs):
        super(ItriOfficialSpider, self).__init__(*args, **kwargs)
        self.visited_urls = set()
        self.max_pages = 200  # 增加限制以獲取更多頁面
        self.use_selenium = kwargs.get('use_selenium', False) and SELENIUM_AVAILABLE
        
        # 初始化 Selenium（如果需要）
        self.driver = None
        if self.use_selenium:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # 無頭模式
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(60)  # 增加到 60 秒，避免超時
                print("✅ Selenium WebDriver 已初始化")
            except Exception as e:
                print(f"⚠️  Selenium 初始化失敗: {e}，將使用標準 HTTP 請求")
                self.use_selenium = False
                self.driver = None
    
    def closed(self, reason):
        """爬蟲關閉時清理資源"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Selenium WebDriver 已關閉")
            except:
                pass

    def parse(self, response):
        """解析首頁或網站地圖"""
        if 'SiteMap' in response.url:
            # 從網站地圖抓取所有連結
            links = response.css('.sitemap-list a::attr(href), .sitemap a::attr(href)').getall()
            for link in links[:self.max_pages]:
                if link and ('ListStyle' in link or 'Content' in link or 'News' in link):
                    full_url = response.urljoin(link)
                    if full_url not in self.visited_urls:
                        self.visited_urls.add(full_url)
                        yield response.follow(link, self.parse_detail, dont_filter=True)
        else:
            # 從首頁抓取主要連結
            # 如果使用 Selenium，先獲取動態載入的內容
            if self.use_selenium and self.driver:
                try:
                    # 設置更長的超時時間
                    self.driver.set_page_load_timeout(60)  # 增加到 60 秒
                    self.driver.get(response.url)
                    # 等待頁面載入完成（增加超時時間）
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    # 等待 JavaScript 執行（給一些時間讓動態內容載入）
                    import time
                    time.sleep(3)  # 增加等待時間
                    # 獲取渲染後的 HTML
                    html = self.driver.page_source
                    # 創建新的 response 對象
                    response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
                except TimeoutException as e:
                    self.logger.warning(f"Selenium 超時 {response.url}: {e}，使用原始 HTML")
                except Exception as e:
                    self.logger.warning(f"Selenium 處理失敗 {response.url}: {e}，使用原始 HTML")
            
            # 使用 XPath 從 HTML 源碼中提取所有連結（包括可能被 CSS 隱藏的）
            # 重要：使用更全面的 XPath 來提取所有連結，不管它們是否被 CSS 隱藏
            processed_urls = set()
            
            # 1. 從導航菜單（mega-menu）中提取所有連結（包括隱藏的）
            # 使用更寬鬆的選擇器，確保能提取到所有連結
            mega_menu_links = response.xpath(
                '//*[contains(@class, "mega-menu")]//a/@href | '
                '//*[contains(@class, "has-mega-menu")]//a/@href | '
                '//nav//a/@href | '
                '//ul[contains(@class, "mega-menu")]//a/@href | '
                '//li[contains(@class, "has-mega-menu")]//a/@href'
            ).getall()
            
            print(f"🔍 從 mega-menu 提取到 {len(mega_menu_links)} 個連結")
            
            for link in mega_menu_links:
                if not link:
                    continue
                # 不要清理連結，保留完整 URL（包括參數）
                full_url = response.urljoin(link)
                # 驗證 URL 是否有效（排除無效域名）
                if self._is_valid_url(full_url):
                    # 標準化 URL（移除片段，但保留參數）
                    url_normalized = full_url.split('#')[0]
                    if url_normalized not in processed_urls:
                        processed_urls.add(url_normalized)
                        self.visited_urls.add(url_normalized)
                        print(f"  ✅ 添加連結: {url_normalized}")
                        yield response.follow(link, self.parse_detail, dont_filter=True)
            
            # 2. 從所有連結中提取 ListStyle 連結（使用 XPath 確保能提取到所有連結）
            # 這會提取頁面中所有包含 ListStyle 的連結，不管它們在哪裡
            all_liststyle_links = response.xpath('//a[contains(@href, "ListStyle")]/@href').getall()
            print(f"🔍 從所有連結中提取到 {len(all_liststyle_links)} 個 ListStyle 連結")
            
            for link in all_liststyle_links:
                if not link:
                    continue
                full_url = response.urljoin(link)
                # 驗證 URL 是否有效
                if self._is_valid_url(full_url):
                    # 標準化 URL
                    url_normalized = full_url.split('#')[0]
                    if url_normalized not in processed_urls:
                        processed_urls.add(url_normalized)
                        self.visited_urls.add(url_normalized)
                        print(f"  ✅ 添加連結: {url_normalized}")
                        yield response.follow(link, self.parse_detail, dont_filter=True)
            
            # 3. 也提取 Content 連結
            all_content_links = response.xpath('//a[contains(@href, "Content")]/@href').getall()
            print(f"🔍 從所有連結中提取到 {len(all_content_links)} 個 Content 連結")
            
            for link in all_content_links:
                if not link:
                    continue
                full_url = response.urljoin(link)
                if self._is_valid_url(full_url):
                    url_normalized = full_url.split('#')[0]
                    if url_normalized not in processed_urls:
                        processed_urls.add(url_normalized)
                        self.visited_urls.add(url_normalized)
                        print(f"  ✅ 添加連結: {url_normalized}")
                        yield response.follow(link, self.parse_detail, dont_filter=True)
    
    def _is_valid_url(self, url):
        """驗證 URL 是否有效（排除無效域名）"""
        try:
            parsed = urlparse(url)
            # 排除無效域名
            invalid_domains = ['itriwww.itri.org.tw', 'itriwww.org.tw']  # 錯誤的域名
            if parsed.netloc in invalid_domains:
                return False
            # 只允許正確的域名（允許空 netloc，表示相對路徑）
            if parsed.netloc:
                valid_domains = ['www.itri.org.tw', 'itri.org.tw']
                if parsed.netloc not in valid_domains and not any(d in parsed.netloc for d in valid_domains):
                    return False
            # 確保是 ListStyle 或 Content 連結
            if 'ListStyle' not in url and 'Content' not in url:
                return False
            return True
        except:
            return False

    def parse_detail(self, response):
        """解析詳細頁面內容"""
        # 如果使用 Selenium，先獲取動態載入的內容
        if self.use_selenium and self.driver:
            try:
                # 設置更長的超時時間
                self.driver.set_page_load_timeout(60)  # 增加到 60 秒
                self.driver.get(response.url)
                # 等待頁面載入完成（增加超時時間）
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # 等待 JavaScript 執行（給一些時間讓動態內容載入）
                import time
                time.sleep(3)  # 增加等待時間
                # 獲取渲染後的 HTML
                html = self.driver.page_source
                # 創建新的 response 對象
                response = HtmlResponse(url=response.url, body=html.encode('utf-8'), encoding='utf-8')
            except TimeoutException as e:
                self.logger.warning(f"Selenium 超時 {response.url}: {e}，使用原始 HTML")
            except Exception as e:
                self.logger.warning(f"Selenium 處理失敗 {response.url}: {e}，使用原始 HTML")
        # 嘗試多種標題選擇器
        # 優先提取詳細頁面的標題（h3 span#spanTitle）
        title = (
            response.css('h3 span#spanTitle::text, h3#spanTitle::text').get() or
            response.css('h2.title::text, h1.title::text, h1::text, h2::text').get() or
            response.css('.article-title::text, .content-title::text').get() or
            response.css('.page-title::text, .title-text::text').get() or
            response.css('title::text').get()
        )
        
        # 改進 breadcrumb 提取（包括最後的純文字部分）
        breadcrumb_parts = []
        breadcrumb = response.css('.breadcrumb, #divBreadcrumb')
        if breadcrumb:
            # 方法1：提取所有連結文字（按順序）
            breadcrumb_links = breadcrumb.css('a')
            for link in breadcrumb_links:
                # 提取連結文字，排除圖標
                link_texts = link.css('::text').getall()
                link_text = ' '.join([t.strip() for t in link_texts if t.strip() and 'icon-' not in t])
                if link_text and len(link_text) > 1:
                    breadcrumb_parts.append(link_text.strip())
            
            # 方法2：提取 breadcrumb 的完整文字內容，然後找出最後的純文字部分
            breadcrumb_full_text = breadcrumb.get()
            if breadcrumb_full_text:
                # 使用正則表達式提取所有文字（包括連結內和連結外的）
                # 先提取所有連結文字
                link_texts_in_html = re.findall(r'<a[^>]*>([^<]*(?:<i[^>]*>.*?</i>[^<]*)*)</a>', breadcrumb_full_text)
                for link_text in link_texts_in_html:
                    # 移除圖標標籤
                    link_text_clean = re.sub(r'<i[^>]*>.*?</i>', '', link_text).strip()
                    if link_text_clean and link_text_clean not in breadcrumb_parts:
                        breadcrumb_parts.append(link_text_clean)
                
                # 移除所有連結標籤，提取剩餘的純文字
                text_without_links = re.sub(r'<a[^>]*>.*?</a>', '', breadcrumb_full_text)
                # 移除所有 HTML 標籤
                text_without_tags = re.sub(r'<[^>]+>', '', text_without_links)
                # 提取非空白文字
                remaining_texts = [t.strip() for t in text_without_tags.split() if t.strip() and len(t.strip()) > 1]
                for text in remaining_texts:
                    if text not in breadcrumb_parts:
                        breadcrumb_parts.append(text)
        
        # 提取頁面主標題（詳細頁面的標題，如 h3 span#spanTitle）
        page_title = response.css('h3 span#spanTitle::text, h3#spanTitle::text').get()
        if page_title:
            page_title = page_title.strip()
        
        # 組合標題：breadcrumb + 頁面標題
        if breadcrumb_parts:
            if page_title and page_title not in breadcrumb_parts:
                # 如果 breadcrumb 最後一項不是頁面標題，則添加頁面標題
                title = ' > '.join(breadcrumb_parts + [page_title]) if page_title else ' > '.join(breadcrumb_parts)
            else:
                title = ' > '.join(breadcrumb_parts)
        elif page_title:
            title = page_title
        elif not title or not title.strip():
            # 嘗試從其他導航中提取
            nav_title = response.css('.nav-current::text').getall()
            if nav_title:
                title = ' > '.join([t.strip() for t in nav_title if t.strip()])
            else:
                # 從 URL 參數提取（如果有）
                parsed = urlparse(response.url)
                params = parse_qs(parsed.query)
                if 'MmmID' in params or 'DisplayStyle' in params:
                    title = "工研院頁面"  # 預設標題
        
        # 如果還是沒有，使用頁面標題
        if not title or not title.strip():
            title = response.css('title::text').get() or "工研院頁面"
        
        title = title.strip() if title else "工研院頁面"
        
        # 收集所有可能的文字內容
        content_parts = []
        
        # 首先提取日期信息（如果有的話）
        pub_date = response.css('#pubDate::text, p.Lb#pubDate::text').get()
        if pub_date:
            pub_date = pub_date.strip()
            if pub_date and len(pub_date) > 3:
                content_parts.append(pub_date)
        
        # 0. 特別處理 #divContent 區塊（工研院網站常用）
        div_content = response.css('#divContent')
        if div_content:
            # 首先檢查 URL：如果包含 DisplayStyle=01_content，這是詳細內容頁面，不是目錄頁
            is_detail_page = 'DisplayStyle=01_content' in response.url or 'DisplayStyle=01%5Fcontent' in response.url
            
            # 檢查是否為目錄頁（ListStyle 頁面，包含新聞列表）
            # 識別標誌：有 <dl class="Bb_dotted pic_list"> 或類似的列表結構
            # 但如果是詳細內容頁面，則不視為目錄頁
            is_list_page = False
            if not is_detail_page:
                is_list_page = div_content.css('dl.Bb_dotted.pic_list, dl.pic_list, .pic_list').get() is not None
            
            if is_list_page:
                # 這是目錄頁，將每個項目作為獨立條目 yield
                # 提取頁面主標題（如果有）
                page_main_title = response.css('h3 span#spanTitle::text, h3::text').get()
                page_main_title = page_main_title.strip() if page_main_title else ""
                
                # 提取每個列表項目的標題和簡介
                list_items = div_content.css('dl.Bb_dotted.pic_list dd, dl.pic_list dd, .pic_list dd')
                
                # 如果找到列表項目，每個項目作為獨立條目
                if list_items:
                    for idx, item in enumerate(list_items):
                        # 提取標題
                        item_title = item.css('a.title::text, a[class*="title"]::text').get()
                        if not item_title:
                            item_title = item.css('a::attr(title)').get()
                        
                        # 提取簡介
                        item_desc = item.css('p::text').get()
                        
                        # 提取圖片 alt（如果有）
                        item_img_alt = item.xpath('./preceding-sibling::dt[1]//img/@alt').get()
                        
                        # 提取連結 URL
                        item_url = item.css('a::attr(href)').get()
                        if item_url:
                            item_url = response.urljoin(item_url)
                        
                        if item_title:
                            # 構建該項目的完整標題（包含頁面路徑）
                            item_full_title = f"{title} > {item_title.strip()}" if title else item_title.strip()
                            
                            # 構建內容
                            item_content_parts = []
                            if item_desc and item_desc.strip():
                                item_content_parts.append(item_desc.strip())
                            if item_img_alt and item_img_alt.strip():
                                item_content_parts.append(f"圖片說明: {item_img_alt.strip()}")
                            
                            item_content = "\n".join(item_content_parts) if item_content_parts else item_title.strip()
                            
                            # Yield 每個項目作為獨立條目
                            yield {
                                'source': 'ITRI_Official',
                                'title': item_full_title,
                                'url': item_url or response.url,
                                'content': item_content,
                                'hierarchy': f"ITRI > Official > {item_full_title}",
                                'depth': 1,
                                'language': 'zh-tw',
                                'crawled_at': datetime.now().isoformat(),
                                'item_type': 'list_item',  # 標記為列表項目
                                'parent_page': title  # 記錄父頁面
                            }
                    
                    # 目錄頁的項目已經作為獨立條目 yield，不需要繼續處理
                    # 不 return，讓函數自然結束（避免 Scrapy 警告）
                
                # 如果沒有找到列表項目，嘗試備用方案
                list_links = div_content.css('a.title, a[class*="title"]')
                if list_links:
                    for link in list_links:
                        link_title = link.css('::text').get() or link.css('::attr(title)').get()
                        link_url = link.css('::attr(href)').get()
                        if link_url:
                            link_url = response.urljoin(link_url)
                        
                        if link_title and link_title.strip():
                            item_full_title = f"{title} > {link_title.strip()}" if title else link_title.strip()
                            yield {
                                'source': 'ITRI_Official',
                                'title': item_full_title,
                                'url': link_url or response.url,
                                'content': link_title.strip(),  # 只有標題
                                'hierarchy': f"ITRI > Official > {item_full_title}",
                                'depth': 1,
                                'language': 'zh-tw',
                                'crawled_at': datetime.now().isoformat(),
                                'item_type': 'list_item',
                                'parent_page': title
                            }
                    
                    # 目錄頁處理完成
                    # 不 return，讓函數自然結束（避免 Scrapy 警告）
            else:
                # 不是目錄頁，正常處理
                # 優先提取 div.run_around 中的內容（這是最重要的內容）
                run_around = div_content.css('div.run_around')
                if run_around:
                    # 方法1：使用 XPath 提取所有文字節點
                    run_around_texts = run_around.xpath('.//text()').getall()
                    if run_around_texts:
                        # 合併文字，保留結構
                        run_around_content = ' '.join([t.strip() for t in run_around_texts if t.strip()])
                        # 清理多餘的空白
                        run_around_content = re.sub(r'\s+', ' ', run_around_content).strip()
                        if run_around_content and len(run_around_content) > 10:
                            content_parts.append(run_around_content)
                    
                    # 方法2：如果方法1沒有足夠內容，使用 HTML 解析
                    if not content_parts or len(content_parts[-1]) < 50:
                        run_around_html = run_around.get()
                        if run_around_html:
                            # 將 <br> 和 <br/> 替換為換行符
                            run_around_html = re.sub(r'<br\s*/?>', '\n', run_around_html, flags=re.IGNORECASE)
                            # 移除所有 HTML 標籤
                            run_around_text = re.sub(r'<[^>]+>', '', run_around_html)
                            # 清理多餘的空白，但保留換行
                            lines = [line.strip() for line in run_around_text.split('\n') if line.strip()]
                            run_around_content = '\n'.join(lines)
                            if run_around_content and len(run_around_content) > 10:
                                # 如果已有內容，比較長度，保留較長的
                                if content_parts and len(run_around_content) > len(content_parts[-1]):
                                    content_parts[-1] = run_around_content
                                elif not content_parts:
                                    content_parts.append(run_around_content)
                
                # 提取所有標題（h4, h5, h6）
                headings = div_content.css('h4, h5, h6')
                for heading in headings:
                    heading_text = ' '.join(heading.css('::text').getall()).strip()
                    if heading_text and len(heading_text) > 2:
                        content_parts.append(f"標題: {heading_text}")
                
                # 提取所有段落文字（使用 XPath 以正確處理 <br/> 標籤）
                # 但排除已經在 run_around 中處理過的段落
                paragraphs = div_content.css('p')
                for para in paragraphs:
                    # 檢查是否在 run_around 中（避免重複）
                    in_run_around = para.xpath('./ancestor::div[@class="run_around"]').get()
                    if in_run_around:
                        continue
                    
                    # 使用 XPath 提取所有文字節點（包括 <br/> 後的文字）
                    para_html = para.get()
                    if para_html:
                        # 將 <br> 和 <br/> 替換為換行符
                        para_html = re.sub(r'<br\s*/?>', '\n', para_html, flags=re.IGNORECASE)
                        # 移除所有 HTML 標籤
                        para_text = re.sub(r'<[^>]+>', '', para_html)
                        # 清理多餘的空白，但保留換行
                        lines = [line.strip() for line in para_text.split('\n') if line.strip()]
                        para_text = '\n'.join(lines)
                        if para_text and len(para_text) > 10:
                            # 檢查是否已經在內容中（避免重複）
                            if not any(para_text in part or part in para_text for part in content_parts if len(part) > 20):
                                content_parts.append(para_text)
                
                # 提取聯絡人信息（.connection 區塊）
                connection_blocks = div_content.css('.connection, .connection Lb')
                for conn in connection_blocks:
                    conn_texts = conn.xpath('.//text()').getall()
                    conn_content = ' '.join([t.strip() for t in conn_texts if t.strip()])
                    if conn_content and len(conn_content) > 5:
                        # 檢查前面是否有標題（如「【新聞連絡人】」）
                        prev_h5 = conn.xpath('./preceding-sibling::h5[1]')
                        if not prev_h5.get():
                            prev_h5 = conn.xpath('./ancestor::p[1]/h5[1]')
                        if prev_h5.get():
                            h5_text = ' '.join(prev_h5.css('::text').getall()).strip()
                            if h5_text:
                                content_parts.append(f"{h5_text}\n{conn_content}")
                            else:
                                content_parts.append(conn_content)
                        else:
                            content_parts.append(conn_content)
            
            # 特別處理 .imglist 區塊（院士列表、項目列表等）
            img_lists = div_content.css('.imglist')
            for img_list in img_lists:
                # 找到這個 imglist 前面的標題（h5）
                prev_heading = img_list.xpath('./preceding-sibling::h5[1]')
                if not prev_heading.get():
                    prev_heading = img_list.xpath('./preceding-sibling::*[self::h4 or self::h5][1]')
                
                section_title = ""
                if prev_heading.get():
                    section_title = ' '.join(prev_heading.css('::text').getall()).strip()
                
                # 提取該區塊中的所有項目
                items = []
                # 從 figure 中提取
                figures_in_list = img_list.css('figure')
                for figure in figures_in_list:
                    # 提取 figcaption 中的 span 文字（院士名稱等）
                    figcaption_spans = figure.css('figcaption span::text').getall()
                    figcaption_text = ' '.join([s.strip() for s in figcaption_spans if s.strip()])
                    
                    # 如果沒有，嘗試從 a 標籤的 title 提取
                    if not figcaption_text:
                        link_title = figure.css('a::attr(title)').get()
                        if link_title:
                            figcaption_text = link_title.strip()
                    
                    if figcaption_text:
                        items.append(figcaption_text)
                
                # 如果沒有從 figure 提取到，嘗試從 a 標籤提取
                if not items:
                    links = img_list.css('a[title]')
                    for link in links:
                        link_title = link.css('::attr(title)').get()
                        if link_title and link_title.strip():
                            items.append(link_title.strip())
                
                # 組織成結構化內容
                if items:
                    if section_title:
                        content_parts.append(f"{section_title}:")
                    for item in items:
                        content_parts.append(f"  - {item}")
        
        # 1. 提取相關新聞/項目的標題和描述（重要！）
        # 提取 figure 和 figcaption 中的內容（只在 #divContent 或 #mainContent 中）
        figures = response.css('figure')
        for figure in figures:
            # 只提取在 #divContent 或 #mainContent 中的 figure
            in_content = figure.xpath('./ancestor-or-self::div[@id="divContent"] | ./ancestor-or-self::*[@id="mainContent"]').get()
            if not in_content:
                continue
            
            # 排除導航區域
            in_nav = figure.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")]').get()
            if in_nav:
                continue
            
            # 提取 figcaption 中的 span 文字
            figcaption_spans = figure.css('figcaption span::text').getall()
            figcaption_text = ' '.join([s.strip() for s in figcaption_spans if s.strip()])
            
            if figcaption_text:
                content_parts.append(f"相關項目: {figcaption_text}")
            else:
                # 如果沒有 span，嘗試直接提取 figcaption 文字
                figcaption = figure.css('figcaption::text').get()
                if figcaption and figcaption.strip():
                    content_parts.append(f"相關項目: {figcaption.strip()}")
            
            # 提取 a 標籤的 title 屬性
            link_title = figure.css('a::attr(title)').get()
            if link_title and link_title.strip() and link_title.strip() not in [item.split(': ')[-1] if ': ' in item else '' for item in content_parts]:
                content_parts.append(f"項目標題: {link_title.strip()}")
            
            # 提取圖片 alt 文字
            img_alt = figure.css('img::attr(alt)').get()
            if img_alt and img_alt.strip():
                content_parts.append(f"圖片說明: {img_alt.strip()}")
        
        # 提取所有連結的 title 屬性（相關新聞/項目），但排除已經處理過的
        # 只提取在 #divContent 或 #mainContent 中的連結
        links = response.css('a[title]')
        processed_titles = set()
        for link in links:
            # 只提取在 #divContent 或 #mainContent 中的連結
            in_content = link.xpath('./ancestor-or-self::div[@id="divContent"] | ./ancestor-or-self::*[@id="mainContent"]').get()
            if not in_content:
                continue
            
            # 排除導航區域
            in_nav = link.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")]').get()
            if in_nav:
                continue
            
            link_title = link.css('::attr(title)').get()
            if link_title and link_title.strip() and len(link_title.strip()) > 5:
                # 過濾掉常見的無用標題
                if not any(skip in link_title for skip in ['回上一頁', '回頂端', '更多', 'More', 'javascript', '另開視窗', 'Share to']):
                    if link_title.strip() not in processed_titles:
                        processed_titles.add(link_title.strip())
                        # 檢查是否已經在內容中
                        if not any(link_title.strip() in item for item in content_parts):
                            content_parts.append(f"相關連結: {link_title.strip()}")
        
        # 2. 提取頁面特定區域的內容（確保每個頁面都有獨特內容）
        # 嘗試提取頁面主標題下的內容區塊（但排除已經處理過的 #divContent 和導航區域）
        page_specific_selectors = [
            '.content-detail',
            '.detail-content',
            '.page-detail',
            '.main-detail',
            '.article-detail',
            '[class*="detail"]',
            '[class*="content"]:not(#divContent)',  # 排除已處理的
            '[id*="detail"]'
        ]
        
        for selector in page_specific_selectors:
            elements = response.css(selector)
            if elements:
                for element in elements:
                    # 檢查是否在 #divContent 中（避免重複）
                    ancestor_div = element.xpath('./ancestor-or-self::div[@id="divContent"]')
                    if ancestor_div.get():
                        continue
                    
                    # 排除導航區域
                    in_nav = element.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")]').get()
                    if in_nav:
                        continue
                    
                    # 只提取在 #mainContent 中的內容
                    in_main = element.xpath('./ancestor-or-self::*[@id="mainContent"]').get()
                    if not in_main:
                        continue
                    
                    # 提取該元素的所有文字
                    text = element.css('::text').getall()
                    if text:
                        text_content = ' '.join([t.strip() for t in text if len(t.strip()) > 3])
                        if len(text_content) > 20:  # 確保有實質內容
                            content_parts.append(text_content)
        
        # 3. 先嘗試常見的內容區塊選擇器（但不要 break，繼續收集）
        # 排除已經處理過的 #divContent 和導航區域
        content_selectors = [
            '.article-content',
            '.content-box',
            '.editor-content',
            '.main-content',
            '#content:not(#divContent)',  # 排除已處理的
            '.article-body',
            'article',
            '.content-area',
            '.page-content'
        ]
        
        for selector in content_selectors:
            elements = response.css(selector)
            if elements:
                for element in elements:
                    # 檢查是否在 #divContent 中（避免重複）
                    ancestor_div = element.xpath('./ancestor-or-self::div[@id="divContent"]')
                    if ancestor_div.get():
                        continue
                    
                    # 排除導航區域
                    in_nav = element.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")]').get()
                    if in_nav:
                        continue
                    
                    # 只提取在 #mainContent 中的內容
                    in_main = element.xpath('./ancestor-or-self::*[@id="mainContent"]').get()
                    if not in_main:
                        continue
                    
                    # 從這些區塊中提取所有文字
                    text = element.css('::text').getall()
                    if text:
                        text_content = ' '.join([t.strip() for t in text if len(t.strip()) > 3])
                        if len(text_content) > 20:
                            content_parts.append(text_content)
        
        # 4. 如果還沒有足夠內容，嘗試抓取表格內容（重要！）
        # 只提取在 #divContent 或 #mainContent 中的表格
        if not content_parts or len(' '.join(content_parts).strip()) < 50:
            # 使用 XPath 提取表格內容（能更好地處理 <br> 標籤）
            tables = response.xpath('//table')
            for table in tables:
                # 只提取在 #divContent 或 #mainContent 中的表格
                in_content = table.xpath('./ancestor-or-self::div[@id="divContent"] | ./ancestor-or-self::*[@id="mainContent"]').get()
                if not in_content:
                    continue
                
                # 排除導航區域
                in_nav = table.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")]').get()
                if in_nav:
                    continue
                
                # 提取表頭
                headers = table.xpath('.//th//text()').getall()
                if headers:
                    header_text = ' | '.join([h.strip() for h in headers if h.strip()])
                    if header_text:
                        content_parts.append(header_text)
                
                # 提取表格行
                rows = table.xpath('.//tr')
                for row in rows:
                    # 提取每個單元格的所有文字（包括 <br> 分隔的內容）
                    cells = row.xpath('.//td')
                    row_data = []
                    for cell in cells:
                        # 使用 XPath 提取所有文字節點（包括 <br> 後的文字）
                        cell_texts = cell.xpath('.//text()').getall()
                        # 合併並清理
                        cell_text = ' '.join([t.strip() for t in cell_texts if t.strip()])
                        if cell_text:
                            row_data.append(cell_text)
                    if row_data:
                        content_parts.append(' | '.join(row_data))
        
        # 5. 抓取列表內容（包括項目列表），但嚴格排除導航區域
        list_items = response.css('ul li, ol li, dl dt, dl dd')
        for item in list_items:
            # 嚴格排除導航區域
            in_nav = item.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")] | ./ancestor::*[contains(@class, "function_link")]').get()
            if in_nav:
                continue
            
            # 只提取在 #divContent 或 #mainContent 中的內容
            in_content = item.xpath('./ancestor-or-self::div[@id="divContent"] | ./ancestor-or-self::*[@id="mainContent"]').get()
            if not in_content:
                continue
            
            item_text = ' '.join(item.css('::text').getall())
            if item_text and len(item_text.strip()) > 5:
                content_parts.append(item_text.strip())
        
        # 6. 抓取所有段落（但過濾太短的，且排除已經在 #divContent 中處理過的）
        paragraphs = response.css('p')
        for para in paragraphs:
            # 嚴格排除導航區域
            in_nav = para.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")] | ./ancestor::*[contains(@class, "function_link")]').get()
            if in_nav:
                continue
            
            # 只提取在 #divContent 或 #mainContent 中的內容
            in_content = para.xpath('./ancestor-or-self::div[@id="divContent"] | ./ancestor-or-self::*[@id="mainContent"]').get()
            if not in_content:
                continue
            
            para_text = ' '.join(para.css('::text').getall())
            if para_text and len(para_text.strip()) > 10:
                content_parts.append(para_text.strip())
        
        # 7. 提取 div 中的文字內容（嚴格排除導航和頁腳）
        # 只從 #mainContent 或 #divContent 中提取
        main_content = response.css('#mainContent, #divContent')
        if main_content:
            for content_div in main_content:
                # 排除導航區域
                in_nav = content_div.xpath('./ancestor::nav | ./ancestor::header | ./ancestor::*[contains(@class, "nav")] | ./ancestor::*[contains(@class, "menu")] | ./ancestor::*[contains(@class, "mega-menu")]').get()
                if in_nav:
                    continue
                
                # 提取文字，但排除子元素中的導航
                text_nodes = content_div.xpath('.//text()[not(ancestor::nav) and not(ancestor::header) and not(ancestor::*[contains(@class, "nav")]) and not(ancestor::*[contains(@class, "menu")]) and not(ancestor::*[contains(@class, "mega-menu")])]').getall()
                if text_nodes:
                    text_content = ' '.join([t.strip() for t in text_nodes if t.strip() and len(t.strip()) > 3])
                    if len(text_content) > 20:
                        content_parts.append(text_content)
        
        # 清理和組合內容（去重並保持順序）
        # 使用更智能的去重：保留較長的內容，避免短內容覆蓋長內容
        seen = set()
        unique_content_parts = []
        # 先按長度排序，長內容優先
        sorted_parts = sorted(content_parts, key=lambda x: len(x.strip()), reverse=True)
        
        for part in sorted_parts:
            part_clean = part.strip()
            if not part_clean or len(part_clean) <= 3:
                continue
            
            # 檢查是否與已有內容重複（允許部分重疊，但不允許完全重複）
            is_duplicate = False
            for existing in unique_content_parts:
                # 如果新內容是已有內容的子串，跳過
                if part_clean in existing and len(part_clean) < len(existing) * 0.8:
                    is_duplicate = True
                    break
                # 如果已有內容是新內容的子串，替換已有內容
                if existing in part_clean and len(existing) < len(part_clean) * 0.8:
                    unique_content_parts.remove(existing)
                    break
            
            if not is_duplicate and part_clean not in seen:
                seen.add(part_clean)
                unique_content_parts.append(part_clean)
        
        # 組合內容，使用換行分隔不同類型的內容
        content = "\n".join(unique_content_parts)
        
        # 過濾掉 JavaScript 錯誤訊息和無用文字
        filter_patterns = [
            '您的瀏覽器不支援JavaScript',
            '請開啟瀏覽器JavaScript',
            'INNOVATIONG A BETTER FUTURE',
            'JavaScript',
            'function',
            'var ',
            'document.',
            'window.',
        ]
        
        for pattern in filter_patterns:
            if pattern in content:
                # 移除包含這些模式的句子
                sentences = content.split('。')
                content = '。'.join([s for s in sentences if pattern not in s])
        
        # 清理多餘的空白（但保留換行）
        lines = content.split('\n')
        cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines if line.strip()]
        content = '\n'.join(cleaned_lines)
        
        # 過濾條件：至少有 30 個字元（降低門檻以包含表格內容）
        # 但也要確保不是只有重複的簡介
        if len(content) >= 30:
            # 檢查是否只是重複的簡介（如果內容太短且與標題相似，可能是重複）
            content_words = set(content.split())
            title_words = set(title.split())
            # 如果內容和標題重疊度太高，可能只是導航，需要更多內容
            # 但我們仍然保存，因為可能包含相關項目列表
            
            # 如果標題為空，嘗試從內容中提取
            if not title or title == "工研院頁面":
                # 嘗試從內容第一行提取標題
                first_line = content.split('\n')[0][:50] if '\n' in content else content[:50]
                if len(first_line.strip()) > 5:
                    title = first_line.strip()
            
                    yield {
                        'source': 'ITRI_Official',
                        'title': title,
                        'url': response.url,
                        'content': content,
                        'hierarchy': f"ITRI > Official > {title}",
                        'depth': 1,
                        'language': 'zh-tw',
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    # 從當前頁面中提取連結，繼續爬取（但限制深度）
                    if len(self.visited_urls) < self.max_pages:
                        # 從當前頁面提取所有 ListStyle 連結（包括 mega-menu 中的）
                        page_links = response.xpath(
                            '//a[contains(@href, "ListStyle")]/@href | '
                            '//*[contains(@class, "mega-menu")]//a[contains(@href, "ListStyle")]/@href | '
                            '//nav//a[contains(@href, "ListStyle")]/@href'
                        ).getall()
                        
                        # 去重
                        unique_links = list(set(page_links))
                        
                        for link in unique_links[:20]:  # 每個頁面最多跟隨 20 個連結
                            if not link:
                                continue
                            full_url = response.urljoin(link)
                            # 標準化 URL
                            url_normalized = full_url.split('#')[0]
                            # 驗證 URL 是否有效
                            if self._is_valid_url(full_url) and url_normalized not in self.visited_urls:
                                self.visited_urls.add(url_normalized)
                                yield response.follow(link, self.parse_detail, dont_filter=True)


# --- 執行爬蟲 ---
if __name__ == "__main__":
    print("=" * 60)
    print("🕷️  ITRI Data Crawler - Step 1: Data Collection")
    print("=" * 60)
    print(f"📁 輸出檔案: {OUTPUT_FILE}")
    print(f"📅 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    process = CrawlerProcess(settings={
        'FEEDS': {
            OUTPUT_FILE: {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 4,
                'overwrite': True
            },
        },
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,   # 遵守 robots.txt（維基百科允許合理的爬取）
        'DEPTH_LIMIT': 2,           # Wiki BFS 限制深度 2
        'CONCURRENT_REQUESTS': 16,  # 加快爬取速度
        'DOWNLOAD_DELAY': 1,        # 禮貌延遲
        'LOG_LEVEL': 'INFO',
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
    })

    print("\n🚀 開始爬取維基百科...")
    process.crawl(ItriWikiSpider)
    
    print("🚀 開始爬取工研院官網...")
    # 檢查是否要使用 Selenium（通過環境變數或命令行參數）
    use_selenium = os.getenv('USE_SELENIUM', 'false').lower() == 'true'
    if use_selenium and not SELENIUM_AVAILABLE:
        print("⚠️  環境變數 USE_SELENIUM=true，但 Selenium 未安裝")
        print("   請執行: pip install selenium")
        use_selenium = False
    
    process.crawl(ItriOfficialSpider, use_selenium=use_selenium)
    
    print("\n⏳ 爬蟲執行中，請稍候...\n")
    process.start()
    
    # 檢查輸出檔案
    if os.path.exists(OUTPUT_FILE):
        import json
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n✅ 爬蟲完成！")
        print(f"📊 共爬取 {len(data)} 筆資料")
        print(f"💾 資料已儲存至: {OUTPUT_FILE}")
    else:
        print("\n⚠️  警告：未找到輸出檔案，爬蟲可能未成功執行")

