import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import time
from ..items import ITRIServiceItem

# Optional Selenium imports (currently not required for iStaging basic text)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class ItriShowroomSpider(scrapy.Spider):
    name = "itri_showroom"
    allowed_domains = ["www.itri-showroom.com", "itri-showroom.com", "livetour.istaging.com", "istaging.com"]
    
    start_urls = [
        "https://www.itri-showroom.com/",
    ]
    
    # Custom settings for this spider
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Virtual showroom may need special handling
        'DOWNLOAD_DELAY': 3,      # Be respectful to servers
        'CONCURRENT_REQUESTS': 4,  # Lower concurrency for complex sites
        'COOKIES_ENABLED': True,
        
        # Longer timeouts for complex 3D content
        'DOWNLOAD_TIMEOUT': 60,
        'DEPTH_LIMIT': 5,
        'CLOSESPIDER_PAGECOUNT': 100,  # Smaller limit for focused crawling
        
        # Better user agent for virtual showroom
        'USER_AGENT': 'ITRI-Showroom-Bot/1.0 (+https://www.itri.org.tw; research@itri.org.tw)',
        
        # Request headers
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        },
        
        # Memory monitoring
        'MEMUSAGE_WARNING_MB': 256,
        'MEMUSAGE_LIMIT_MB': 512,
    }

    def __init__(self, *args, **kwargs):
        super(ItriShowroomSpider, self).__init__(*args, **kwargs)
        self.exhibit_count = 0
        self.technology_count = 0
        # 對於目前的 iStaging 展間，我們用純 HTML 解析即可，不強制啟用 Selenium
        self.driver = None
        
    def setup_selenium(self):
        """Setup Selenium WebDriver for handling JavaScript content"""
        """目前保留此方法以便未來擴充互動式 3D 內容，預設不啟用"""
        if not SELENIUM_AVAILABLE:
            self.logger.info("ℹ️  Selenium not available, staying in basic HTML mode")
            self.driver = None
            return

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=ITRI-Showroom-Bot/1.0")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.logger.info("✅ Selenium WebDriver initialized successfully")
        except Exception as e:
            self.logger.warning(f"⚠️  Could not initialize Selenium: {e}")
            self.driver = None

    def parse(self, response):
        """Parse the main showroom page"""
        self.logger.info(f"🏛️  Parsing ITRI Virtual Showroom: {response.url}")
        
        # Extract basic page information
        title = response.css('title::text').get() or "ITRI Virtual Showroom"
        description = response.css('meta[name="description"]::attr(content)').get() or ""
        
        # Look for iframe containing the virtual tour
        iframe_src = response.css('iframe::attr(src)').get()
        if iframe_src:
            self.logger.info(f"🎯 Found virtual tour iframe: {iframe_src}")
            
            # Create main showroom item
            item = self._create_showroom_item(response, title, description)
            yield item
            
            # Follow the iframe to extract 3D content
            if iframe_src.startswith('http'):
                yield response.follow(
                    iframe_src,
                    callback=self.parse_istaging_tour,
                    meta={'main_url': response.url, 'title': title}
                )
        
        # Look for any additional links or content
        for link in response.css('a::attr(href)').getall():
            if link and not link.startswith('#'):
                absolute_url = urljoin(response.url, link)
                if self._is_showroom_related(absolute_url):
                    yield response.follow(link, callback=self.parse)

    def parse_istaging_tour(self, response):
        """Parse the iStaging virtual tour content"""
        self.logger.info(f"🌐 Parsing iStaging tour: {response.url}")

        # 這個頁面實際上在 <div id="app"><div hidden>...</div></div> 中
        # 包含多個 <section><h1>..</h1><h2>..長文..</h2>，純 HTML 就能取得

        sections = response.css("div#app > div[hidden] > section")
        self.logger.info(f"🔎 Found {len(sections)} sections in iStaging tour HTML")

        for idx, section in enumerate(sections):
            title = section.css("h1::text").get()
            # h2 可能分成多個 text node，合併起來
            body_parts = section.css("h2::text").getall()
            body = " ".join([t.strip() for t in body_parts if t.strip()])

            self.logger.info(
                f"Section #{idx}: title={title!r}, body_len={len(body)}"
            )

            # 如果沒有 h2，但有 h1（像「智慧醫療」「智慧交通」），就先略過，避免被 pipeline 當成太短內容丟掉
            if not body or len(body) < 50:
                self.logger.debug(
                    f"Skipping short section #{idx}: title={title!r}, body_len={len(body)}"
                )
                continue

            # 建立展區 item，使用 ITRIServiceItem，符合現有 pipeline 的欄位需求
            item = ITRIServiceItem()
            item_id = self._generate_id(response.url + f"#section_{idx}")

            item["id"] = item_id
            item["title"] = title or "ITRI Virtual Showroom Section"
            item["content"] = body
            item["url"] = response.url
            item["source"] = "itri_showroom"
            # 判斷語言：這幾段主要是英文敘述
            item["language"] = "en"
            item["content_type"] = "virtual_showroom_exhibit"
            item["crawled_at"] = datetime.now().isoformat()
            item["category"] = self._categorize_exhibit(title or body)
            item["tags"] = self._extract_exhibit_tags(body)
            item["summary"] = body[:200]
            item["images"] = []
            item["published_date"] = ""

            # Service-specific fields（僅使用 ITRIServiceItem 中已定義欄位）
            item["service_type"] = "virtual_exhibition"
            item["target_industry"] = "general"
            item["collaboration_type"] = "showcase"
            item["contact_department"] = "ITRI"

            # Metadata fields
            parsed = urlparse(response.url)
            item["author"] = "ITRI"
            item["domain"] = parsed.netloc
            item["path"] = parsed.path
            item["content_length"] = len(body)
            item["content_quality"] = self._calculate_quality_score(body)

            self.exhibit_count += 1
            self.logger.info(
                f"✅ Extracted showroom exhibit #{self.exhibit_count}: {item['title'][:60]}..."
            )
            yield item

        # 原本 Selenium 互動邏輯暫時關閉，有需要再開啟

    def _selenium_extract_tour_data(self, response):
        """Use Selenium to extract data from the interactive 3D tour"""
        self.logger.info("🤖 Using Selenium to extract 3D tour data...")
        
        try:
            self.driver.get(response.url)
            
            # Wait for the tour to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give extra time for 3D content to load
            time.sleep(10)
            
            # Look for interactive elements, hotspots, or information panels
            hotspots = self._find_tour_hotspots()
            exhibits = self._find_exhibit_information()
            
            for exhibit in exhibits:
                yield self._create_exhibit_item(response, exhibit)
                
        except TimeoutException:
            self.logger.warning("⏰ Selenium timeout waiting for tour to load")
        except Exception as e:
            self.logger.error(f"❌ Selenium error: {e}")

    def _find_tour_hotspots(self):
        """Find interactive hotspots in the virtual tour"""
        hotspots = []
        
        try:
            # Common selectors for iStaging hotspots
            hotspot_selectors = [
                '[class*="hotspot"]',
                '[class*="marker"]',
                '[class*="info"]',
                '[data-hotspot]',
                '.hotspot-marker',
                '.info-point'
            ]
            
            for selector in hotspot_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        # Try to click and extract information
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)
                        
                        # Look for popup content
                        popup_text = self._extract_popup_content()
                        if popup_text:
                            hotspots.append({
                                'type': 'hotspot',
                                'content': popup_text,
                                'position': element.location
                            })
                            
                        # Close popup if exists
                        self._close_popup()
                        
                    except Exception as e:
                        self.logger.debug(f"Could not interact with hotspot: {e}")
                        continue
                        
        except Exception as e:
            self.logger.warning(f"Error finding hotspots: {e}")
            
        return hotspots

    def _find_exhibit_information(self):
        """Extract exhibit information from the tour"""
        exhibits = []
        
        try:
            # Look for text content that might be exhibit information
            page_source = self.driver.page_source
            
            # Extract structured exhibit data from hidden content
            exhibit_patterns = [
                r'<h1[^>]*>(.*?)</h1>.*?<h2[^>]*>(.*?)</h2>',
                r'<section[^>]*>.*?<h1[^>]*>(.*?)</h1>.*?<h2[^>]*>(.*?)</h2>.*?</section>',
            ]
            
            for pattern in exhibit_patterns:
                matches = re.findall(pattern, page_source, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        title = self._clean_text(match[0])
                        description = self._clean_text(match[1])
                        
                        if title and description and len(description) > 50:
                            exhibits.append({
                                'title': title,
                                'description': description,
                                'type': 'exhibit'
                            })
                            
        except Exception as e:
            self.logger.warning(f"Error extracting exhibit information: {e}")
            
        return exhibits

    def _extract_popup_content(self):
        """Extract content from popup dialogs"""
        popup_selectors = [
            '.popup-content',
            '.modal-content',
            '.info-popup',
            '[class*="popup"]',
            '[class*="modal"]',
            '[role="dialog"]'
        ]
        
        for selector in popup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and len(text) > 20:
                            return text
            except:
                continue
                
        return None

    def _close_popup(self):
        """Close any open popups"""
        close_selectors = [
            '.close',
            '.close-button',
            '[class*="close"]',
            '[aria-label="close"]',
            '[aria-label="Close"]'
        ]
        
        for selector in close_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        time.sleep(1)
                        return
            except:
                continue

    def _extract_tour_content(self, response):
        """Extract visible content from the tour page"""
        content_parts = []
        
        # Extract title and description
        title = response.css('title::text').get()
        if title:
            content_parts.append(f"Title: {title.strip()}")
            
        description = response.css('meta[name="description"]::attr(content)').get()
        if description:
            content_parts.append(f"Description: {description.strip()}")
        
        # Extract any visible text content
        text_content = response.css('body ::text').getall()
        meaningful_text = []
        
        for text in text_content:
            cleaned = text.strip()
            if cleaned and len(cleaned) > 10 and not self._is_noise_text(cleaned):
                meaningful_text.append(cleaned)
        
        if meaningful_text:
            content_parts.append("Content: " + " ".join(meaningful_text))
        
        return "\n".join(content_parts) if content_parts else ""

    def _is_noise_text(self, text):
        """Check if text is noise (CSS, JS, etc.)"""
        noise_patterns = [
            r'^[{}()\[\];,.:]+$',
            r'^\s*$',
            r'^(function|var|const|let)\s',
            r'^\d+px$',
            r'^#[0-9a-fA-F]+$',
            r'^(true|false|null|undefined)$'
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text):
                return True
                
        return False

    def _create_showroom_item(self, response, title, description):
        """Create item for main showroom page"""
        item = ITRIServiceItem()
        
        item['id'] = self._generate_id(response.url)
        item['title'] = title
        item['content'] = description
        item['url'] = response.url
        item['source'] = 'itri_showroom'
        item['language'] = 'zh-tw'
        item['content_type'] = 'virtual_showroom'
        item['crawled_at'] = datetime.now().isoformat()
        item['category'] = 'Virtual Exhibition'
        item['tags'] = ['虛擬展示', '3D展覽', '互動展示']
        item['summary'] = description[:200] if description else ""
        item['images'] = []
        item['published_date'] = ""
        
        # Service-specific fields (only use fields defined in ITRIServiceItem)
        item['service_type'] = 'virtual_exhibition'
        item['target_industry'] = 'general'
        item['collaboration_type'] = 'showcase'
        item['contact_department'] = 'ITRI'
        
        # Metadata fields
        item['author'] = 'ITRI'
        item['domain'] = urlparse(response.url).netloc
        item['path'] = urlparse(response.url).path
        item['content_length'] = len(description)
        item['content_quality'] = self._calculate_quality_score(description)
        
        self.exhibit_count += 1
        self.logger.info(f'✅ Created showroom item: {title[:50]}... (#{self.exhibit_count})')
        
        return item

    def _create_tour_content_item(self, response, content):
        """Create item for tour content"""
        item = ITRIServiceItem()
        
        item['id'] = self._generate_id(response.url + "_tour")
        item['title'] = "ITRI Virtual Tour Content"
        item['content'] = content
        item['url'] = response.url
        item['source'] = 'itri_showroom'
        item['language'] = 'en'  # iStaging content is often in English
        item['content_type'] = 'virtual_tour'
        item['crawled_at'] = datetime.now().isoformat()
        item['category'] = 'Interactive Tour'
        item['tags'] = ['virtual_tour', 'interactive', '3D']
        item['summary'] = content[:200] if content else ""
        item['images'] = []
        item['published_date'] = ""
        
        # Service-specific fields (only existing fields)
        item['service_type'] = 'interactive_tour'
        item['target_industry'] = 'general'
        item['collaboration_type'] = 'showcase'
        item['contact_department'] = 'ITRI'
        
        # Metadata fields
        item['author'] = 'ITRI'
        item['domain'] = urlparse(response.url).netloc
        item['path'] = urlparse(response.url).path
        item['content_length'] = len(content)
        item['content_quality'] = self._calculate_quality_score(content)
        
        return item

    def _create_exhibit_item(self, response, exhibit):
        """Create item for individual exhibit"""
        item = ITRIServiceItem()
        
        exhibit_id = self._generate_id(response.url + "_" + exhibit['title'])
        item['id'] = exhibit_id
        item['title'] = exhibit['title']
        item['content'] = exhibit['description']
        item['url'] = response.url + f"#exhibit_{self.technology_count}"
        item['source'] = 'itri_showroom'
        item['language'] = 'en' if self._is_english_content(exhibit['description']) else 'zh-tw'
        item['content_type'] = 'technology_exhibit'
        item['crawled_at'] = datetime.now().isoformat()
        item['category'] = self._categorize_exhibit(exhibit['title'])
        item['tags'] = self._extract_exhibit_tags(exhibit['description'])
        item['summary'] = exhibit['description'][:200]
        item['images'] = []
        item['published_date'] = ""
        
        # Service-specific fields (only existing fields)
        item['service_type'] = 'technology_showcase'
        item['target_industry'] = 'research'
        item['collaboration_type'] = 'demonstration'
        item['contact_department'] = 'ITRI'
        
        # Metadata fields
        item['author'] = 'ITRI'
        item['domain'] = urlparse(response.url).netloc
        item['path'] = urlparse(response.url).path + f"#exhibit_{self.technology_count}"
        item['content_length'] = len(exhibit['description'])
        item['content_quality'] = self._calculate_quality_score(exhibit['description'])
        
        self.technology_count += 1
        self.logger.info(f'✅ Created exhibit item: {exhibit["title"][:50]}... (#{self.technology_count})')
        
        return item

    def _categorize_exhibit(self, title):
        """Categorize exhibit based on title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['smart', '智慧', 'ai', 'iot']):
            return 'Smart Technology'
        elif any(keyword in title_lower for keyword in ['medical', '醫療', 'health', '健康']):
            return 'Smart Healthcare'
        elif any(keyword in title_lower for keyword in ['transport', '交通', 'traffic', 'vehicle']):
            return 'Smart Transportation'
        elif any(keyword in title_lower for keyword in ['eco', '生態', 'green', '環保', 'energy', '能源']):
            return 'Green Technology'
        elif any(keyword in title_lower for keyword in ['tree', '樹', 'solar', '太陽能']):
            return 'Renewable Energy'
        else:
            return 'Technology Innovation'

    def _extract_exhibit_tags(self, description):
        """Extract relevant tags from exhibit description"""
        tags = []
        description_lower = description.lower()
        
        # Technology keywords
        tech_keywords = {
            'ai': ['ai', 'artificial intelligence', '人工智慧'],
            'iot': ['iot', 'internet of things', '物聯網'],
            'solar': ['solar', 'photovoltaic', '太陽能', '光電'],
            'medical': ['medical', 'healthcare', '醫療', '健康'],
            'green': ['green', 'eco', 'environmental', '綠色', '環保'],
            'smart': ['smart', 'intelligent', '智慧', '智能'],
            'energy': ['energy', 'power', '能源', '電力'],
            'water': ['water', 'purification', '水', '淨化'],
            'transportation': ['transport', 'traffic', 'vehicle', '交通', '運輸']
        }
        
        for tag, keywords in tech_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                tags.append(tag)
        
        return tags[:5]  # Limit to 5 most relevant tags

    def _is_english_content(self, text):
        """Detect if content is primarily in English"""
        if not text:
            return False
            
        # Count English vs Chinese characters
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        return english_chars > chinese_chars

    def _clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters at start/end
        text = text.strip('•─●\n\r\t ')
        
        return text

    def _is_showroom_related(self, url):
        """Check if URL is related to the showroom"""
        showroom_indicators = [
            'showroom', 'exhibition', 'virtual', 'tour', 'itri'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in showroom_indicators)

    def _generate_id(self, url):
        """Generate unique ID for items"""
        import hashlib
        return f"itri_showroom_{hashlib.md5(url.encode()).hexdigest()[:8]}"

    def _calculate_quality_score(self, content):
        """Calculate content quality score"""
        if not content:
            return 0
            
        score = 0
        
        # Length factor
        if len(content) > 100:
            score += 30
        if len(content) > 500:
            score += 20
            
        # Technical content indicators
        tech_indicators = [
            'technology', 'innovation', 'research', 'development',
            '技術', '創新', '研發', '開發'
        ]
        
        for indicator in tech_indicators:
            if indicator.lower() in content.lower():
                score += 10
                
        # Structure indicators
        if '●' in content or '─' in content:  # Bullet points
            score += 15
        if 'Design concept' in content or 'Application scenario' in content:
            score += 20
            
        return min(score, 100)

    def closed(self, reason):
        """Clean up when spider closes"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            self.logger.info("🔧 Selenium WebDriver closed")
            
        self.logger.info(f"🏛️  ITRI Showroom Spider finished: {reason}")
        self.logger.info(f"📊 Total exhibits extracted: {self.exhibit_count}")
        self.logger.info(f"🔬 Total technologies documented: {self.technology_count}")
