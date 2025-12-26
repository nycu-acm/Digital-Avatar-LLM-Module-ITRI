import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from ..items import ITRIArticleItem, ITRINewsItem, ITRIResearchItem, ITRIServiceItem


class ItriOfficialSpider(scrapy.Spider):
    name = "itri_official"
    allowed_domains = ["www.itri.org.tw", "itri.org.tw"]
    
    # Single starting point - let spider discover all content organically
    start_urls = [
        "https://www.itri.org.tw/",  # Start from homepage and crawl everything
    ]
    
    # Custom settings for this spider
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # ITRI allows comprehensive crawling
        'DOWNLOAD_DELAY': 2,      # Be respectful to server
        'CONCURRENT_REQUESTS': 8,
        'COOKIES_ENABLED': True,  # Some pages may need cookies
        
        # Download timeout - increased for slow-responding pages
        'DOWNLOAD_TIMEOUT': 90,   # 90 seconds timeout (increased from default 30s)
        
        # Depth and safety limits
        'DEPTH_LIMIT': 10,        # Maximum link depth from start_urls
        'CLOSESPIDER_PAGECOUNT': 10000,  # Stop after 10000 pages as requested
        # 'CLOSESPIDER_TIMEOUT': 3600,   # No timeout limit as requested
        
        # Better user agent
        'USER_AGENT': 'ITRI-Research-Bot/2.0 (+https://www.itri.org.tw; research@itri.org.tw)',
        
        # Request headers
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        },
        
        # Enable better duplicate filtering
        'DUPEFILTER_DEBUG': True,
        
        # Memory monitoring
        'MEMUSAGE_WARNING_MB': 512,
        'MEMUSAGE_LIMIT_MB': 1024,
    }

    def __init__(self, *args, **kwargs):
        super(ItriOfficialSpider, self).__init__(*args, **kwargs)
        self.crawled_urls = set()
        self.article_count = 0
        self.discovered_urls = 0
        
        # Progress logging
        self.logger.info("🏢 ITRI Official Website Spider initialized")
        self.logger.info("📍 Strategy: Single-point deep crawling from homepage")
        self.logger.info(f"⚙️ Limits: {self.custom_settings.get('CLOSESPIDER_PAGECOUNT', 'No')} pages, "
                        f"{self.custom_settings.get('DEPTH_LIMIT', 'No')} depth, "
                        f"{self.custom_settings.get('CLOSESPIDER_TIMEOUT', 'No')}s timeout")

    def parse(self, response):
        """Parse page and recursively discover all internal links"""
        self.logger.info(f'🔍 Parsing: {response.url}')
        self.logger.info(f'📊 Progress: {len(self.crawled_urls)} URLs discovered, {self.article_count} articles extracted')
        
        # First, try to extract content from current page
        yield from self.parse_content(response)
        
        # Then discover and follow all internal links
        # Priority 1: Navigation and menu links (most important)
        nav_links = response.css('''
            nav a::attr(href), 
            .menu a::attr(href),
            .navigation a::attr(href),
            [class*="nav"] a::attr(href),
            [id*="nav"] a::attr(href),
            [class*="menu"] a::attr(href)
        ''').getall()
        
        # Priority 2: Main content area links
        content_links = response.css('''
            main a::attr(href),
            .content a::attr(href), 
            .main a::attr(href),
            article a::attr(href),
            [class*="content"] a::attr(href)
        ''').getall()
        
        # Priority 3: All other internal links
        all_links = response.css('a::attr(href)').getall()
        
        # Combine all links with priority order
        discovered_links = nav_links + content_links + all_links
        new_links_count = 0
        
        self.logger.info(f'🔗 Found {len(discovered_links)} total links on this page')
        
        # Process links in order of discovery
        for link in discovered_links:
            if not link:
                continue
                
            # Skip fragment-only links and external protocols
            if link.startswith('#') or link.startswith('mailto:') or link.startswith('javascript:'):
                continue
                
            # Convert relative URLs to absolute
            absolute_url = urljoin(response.url, link)
            parsed_url = urlparse(absolute_url)
            
            # Filter for ITRI domain and avoid duplicates
            if (parsed_url.netloc in self.allowed_domains and 
                absolute_url not in self.crawled_urls and
                self._is_content_url(absolute_url)):
                
                self.crawled_urls.add(absolute_url)
                new_links_count += 1
                
                # Use different callbacks based on URL patterns for better handling
                if self._looks_like_list_page(absolute_url):
                    # List pages should continue discovering links
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.parse,  # Use parse for further link discovery
                        dont_filter=False,
                        meta={'source_page': response.url, 'depth': response.meta.get('depth', 0) + 1}
                    )
                else:
                    # Content pages should extract content
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.parse_content,
                        dont_filter=False,
                        meta={'source_page': response.url, 'depth': response.meta.get('depth', 0) + 1}
                    )
        
        # Look for pagination and "load more" functionality
        pagination_links = response.css('''
            a[href*="page"], 
            a[href*="Page"],
            a[href*="更多"], 
            a[href*="下一頁"],
            a[href*="next"],
            .next::attr(href), 
            .pagination a::attr(href),
            [class*="paging"] a::attr(href),
            [class*="more"] a::attr(href)
        ''').getall()
        
        for page_link in pagination_links:
            if page_link:
                page_url = urljoin(response.url, page_link)
                if page_url not in self.crawled_urls and self._is_content_url(page_url):
                    self.crawled_urls.add(page_url)
                    yield scrapy.Request(
                        url=page_url, 
                        callback=self.parse,
                        meta={'source_page': response.url, 'is_pagination': True}
                    )
        
        if new_links_count > 0:
            self.logger.info(f'✅ Discovered {new_links_count} new URLs from {response.url}')

    def _looks_like_list_page(self, url):
        """Check if URL likely contains lists of other content (should continue parsing for links)"""
        list_indicators = [
            '/list', '/List', '/index', '/Index', 
            '/news', '/News', '/article', '/Article',
            '/category', '/Category', '/search', '/Search',
            '頁面', '列表', '目錄', '索引'
        ]
        
        return any(indicator in url for indicator in list_indicators)

    def parse_content(self, response):
        """Parse content pages for articles, news, research info"""
        content = self._extract_main_content(response)
        title = self._extract_title(response)
        
        # Skip if no meaningful content
        if not content or len(content.strip()) < 50:
            return
            
        # Determine content type and create appropriate item
        content_type = self._determine_content_type(response.url, title, content)
        
        if content_type == 'news':
            item = ITRINewsItem()
            item['news_type'] = self._extract_news_type(response)
            item['department'] = self._extract_department(response)
            item['contact_info'] = self._extract_contact_info(response)
        elif content_type == 'research':
            item = ITRIResearchItem()
            item['research_area'] = self._extract_research_area(response)
            item['technology_type'] = self._extract_technology_type(response)
            item['applications'] = self._extract_applications(response)
            item['keywords'] = self._extract_keywords(content)
        elif content_type == 'service':
            item = ITRIServiceItem()
            item['service_type'] = self._extract_service_type(response)
            item['target_industry'] = self._extract_target_industry(response)
            item['collaboration_type'] = self._extract_collaboration_type(response)
        else:
            item = ITRIArticleItem()
            
        # Common fields for all item types
        item['id'] = self._generate_id(response.url)
        item['title'] = title
        item['content'] = content
        item['url'] = response.url
        item['source'] = 'itri_official'
        item['language'] = self._detect_language(content)
        item['crawled_at'] = datetime.now().isoformat()
        item['content_type'] = content_type
        item['category'] = self._extract_category(response)
        item['tags'] = self._extract_tags(content)
        item['summary'] = self._generate_summary(content)
        item['images'] = self._extract_images(response)
        item['published_date'] = self._extract_published_date(response)
        
        self.article_count += 1
        self.logger.info(f'✅ Extracted {content_type}: {title[:50]}... (#{self.article_count})')
        
        yield item

    def _is_content_url(self, url):
        """Check if URL likely contains content worth scraping"""
        # Skip certain file types and admin pages
        skip_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|jpg|jpeg|png|gif|css|js|ico|svg)$',
            r'/(admin|login|search|print|download|logout|register)/',
            r'javascript:',
            r'mailto:',
            r'^#',  # Only skip fragment-only links
            r'/RSSAction\.aspx',  # RSS feeds
            r'/search\.aspx',     # Search results
            r'/sitemap',          # Sitemap pages
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # For ITRI domain, be very inclusive - most pages contain valuable content
        # Instead of restrictive include patterns, use broad acceptance
        parsed_url = urlparse(url)
        
        # Must be ITRI domain
        if parsed_url.netloc not in ['www.itri.org.tw', 'itri.org.tw']:
            return False
            
        # Exclude very specific unwanted paths
        exclude_paths = [
            '/map',           # Site maps
            '/contact',       # Contact forms only
            '/feedback',      # Feedback forms
            '/subscribe',     # Subscription pages
        ]
        
        path_lower = parsed_url.path.lower()
        for exclude_path in exclude_paths:
            if exclude_path in path_lower:
                return False
        
        # Accept all other ITRI internal pages - let content filtering handle quality
        return True

    def _extract_main_content(self, response):
        """Extract main content from page, avoiding footer and navigation"""
        
        # First, try to find main content areas specifically
        main_content_selectors = [
            '.main-content, #main-content',
            '.content-area, .content-main',
            '.article-content, .post-content',
            '.entry-content',
            'article',
            'main',
            '[role="main"]',
            '.page-content'
        ]
        
        for selector in main_content_selectors:
            elements = response.css(selector)
            if elements:
                # Extract text but exclude footer elements
                content_parts = []
                for element in elements:
                    # Skip footer, navigation, and other noise
                    text_nodes = element.css('*::text').getall()
                    clean_texts = []
                    
                    for text in text_nodes:
                        text = text.strip()
                        if len(text) > 15 and not self._is_noise_text(text):
                            clean_texts.append(text)
                    
                    if clean_texts:
                        content_parts.extend(clean_texts)
                
                if content_parts:
                    content = ' '.join(content_parts)
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Validate extracted content
                    if len(content) > 100 and not self._is_footer_content(content):
                        return content
        
        # Secondary attempt: extract paragraphs directly
        paragraphs = response.css('p::text').getall()
        meaningful_paragraphs = []
        
        for p in paragraphs:
            p = p.strip()
            if len(p) > 20 and not self._is_noise_text(p):
                meaningful_paragraphs.append(p)
        
        if meaningful_paragraphs:
            content = ' '.join(meaningful_paragraphs)
            content = re.sub(r'\s+', ' ', content).strip()
            if len(content) > 100 and not self._is_footer_content(content):
                return content
        
        # Last resort: careful body extraction
        return self._extract_body_content_carefully(response)

    def _is_noise_text(self, text):
        """Check if text is likely navigation/noise content"""
        noise_indicators = [
            '跳到主要內容', '網站導覽', '選單按鈕', '搜尋', '輸入關鍵字',
            '熱門搜尋', 'Cookie', '隱私權', '使用條款',
            'facebook', 'youtube', 'instagram', 'twitter',
            '訂閱', '分享', '列印', '字級',
            '回頂端', '關閉視窗', 'English', '中文'
        ]
        
        text_lower = text.lower()
        return any(noise.lower() in text_lower for noise in noise_indicators)

    def _is_footer_content(self, content):
        """Check if content is primarily footer information"""
        footer_indicators = [
            '法律聲明', '採購資訊', '工研院圖書館', '專業連結',
            '常見問答', '聯絡我們', '© 工業技術研究院', '權利所有',
            '客服專線', '0800-45-8899', '新竹縣竹東鎮中興路四段195號'
        ]
        
        content_lower = content.lower()
        footer_matches = sum(1 for indicator in footer_indicators if indicator.lower() in content_lower)
        
        # If content has many footer indicators and is relatively short, it's probably footer-only
        return footer_matches >= 3 and len(content) < 800

    def _extract_body_content_carefully(self, response):
        """Carefully extract content from body, excluding known noise areas"""
        
        # Elements to exclude completely
        exclude_selectors = [
            'nav', 'header', 'footer', '.nav', '.header', '.footer',
            '.navigation', '.menu', '.breadcrumb', '.sidebar',
            '.social', '.share', '.print', '.search',
            '[class*="nav"]', '[class*="menu"]', '[class*="footer"]',
            '[id*="nav"]', '[id*="menu"]', '[id*="footer"]'
        ]
        
        # Get all text, then filter
        all_text = response.css('body *::text').getall()
        
        # Remove text that comes from excluded areas
        excluded_text = []
        for selector in exclude_selectors:
            try:
                excluded_elements = response.css(selector)
                for element in excluded_elements:
                    excluded_text.extend(element.css('*::text').getall())
            except:
                continue
        
        excluded_text = set(t.strip() for t in excluded_text)
        
        # Filter content
        clean_content = []
        for text in all_text:
            text = text.strip()
            if (len(text) > 15 and 
                text not in excluded_text and
                not self._is_noise_text(text) and
                not any(indicator in text.lower() for indicator in ['©', 'copyright', '版權'])):
                clean_content.append(text)
        
        if clean_content:
            content = ' '.join(clean_content)
            content = re.sub(r'\s+', ' ', content).strip()
            return content
        
        return ""

    def _extract_title(self, response):
        """Extract title from page"""
        # Try multiple title selectors
        title_selectors = [
            'h1::text',
            'title::text',
            '.page-title::text',
            '.article-title::text',
            '.entry-title::text',
            '[class*="title"]::text',
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        
        return response.url.split('/')[-1]  # Fallback to URL segment

    def _determine_content_type(self, url, title, content):
        """Determine the type of content based on URL, title, and content"""
        url_lower = url.lower()
        title_lower = title.lower() if title else ""
        content_lower = content.lower()
        
        # Check for news indicators
        news_keywords = ['news', 'newsletter', '新聞', '消息', '公告', '最新']
        if any(keyword in url_lower or keyword in title_lower for keyword in news_keywords):
            return 'news'
            
        # Check for research indicators
        research_keywords = ['research', 'technology', 'innovation', '研究', '技術', '創新', '研發']
        if any(keyword in url_lower or keyword in title_lower for keyword in research_keywords):
            return 'research'
            
        # Check for service indicators
        service_keywords = ['service', 'collaboration', 'industry', '服務', '合作', '產業']
        if any(keyword in url_lower or keyword in title_lower for keyword in service_keywords):
            return 'service'
            
        return 'article'

    def _generate_id(self, url):
        """Generate unique ID for content"""
        return f"itri_official_{hash(url) % 1000000:06d}"

    def _detect_language(self, text):
        """Simple language detection"""
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh-tw'
        elif re.search(r'[a-zA-Z]', text):
            return 'en'
        return 'unknown'

    def _extract_category(self, response):
        """Extract category from breadcrumb or URL"""
        # Try breadcrumb
        breadcrumb = response.css('.breadcrumb a::text, .nav-breadcrumb a::text').getall()
        if breadcrumb and len(breadcrumb) > 1:
            return breadcrumb[-2].strip()
            
        # Extract from URL path
        path_parts = response.url.split('/')
        for part in reversed(path_parts):
            if part and part not in ['www.itri.org.tw', 'chi', 'eng', 'Content']:
                return part.replace('%20', ' ').replace('_', ' ')
        
        return 'general'

    def _extract_tags(self, content):
        """Extract relevant tags from content"""
        # Simple keyword extraction based on ITRI domains
        itri_keywords = [
            '人工智慧', 'AI', '機器學習', '深度學習',
            '半導體', '電子', '資通訊', 'ICT',
            '生醫', '醫療', '健康照護',
            '綠能', '再生能源', '節能',
            '智慧製造', '工業4.0', '物聯網', 'IoT',
            '創新', '研發', '技術轉移',
            '產業合作', '新創', 'startup'
        ]
        
        found_tags = []
        content_lower = content.lower()
        for keyword in itri_keywords:
            if keyword.lower() in content_lower:
                found_tags.append(keyword)
        
        return found_tags

    def _generate_summary(self, content, max_length=200):
        """Generate a simple summary"""
        # Clean JavaScript warnings from content before generating summary
        cleaned_content = self._clean_javascript_warnings(content)
        
        # Take first meaningful sentences up to max_length
        sentences = re.split(r'[。！？.!?]', cleaned_content)
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Skip very short sentences
                if len(summary + sentence) < max_length:
                    summary += sentence + "。"
                else:
                    break
        return summary.strip()
    
    def _clean_javascript_warnings(self, text):
        """Remove JavaScript warning messages from text"""
        if not text:
            return text
            
        # JavaScript warning and code patterns
        js_warning_patterns = [
            r'『您的瀏覽器不支援JavaScript功能，若網頁功能無法正常使用時，請開啟瀏覽器JavaScript狀態』\s*',
            r'Your browser does not support JavaScript.*?please enable JavaScript\s*',
            r'請開啟瀏覽器JavaScript功能.*?\s*',
            r'//\s*\(function\s*\([^)]*\)\s*\{.*?\}\)\s*\([^)]*\)\s*;?\s*',  # GTM JavaScript code
            r'function\s*\([^)]*\)\s*\{[^}]*gtm[^}]*\}',  # GTM function blocks
        ]
        
        cleaned_text = text
        for pattern in js_warning_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up excessive whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text

    def _extract_images(self, response):
        """Extract image URLs from page"""
        images = []
        img_urls = response.css('img::attr(src)').getall()
        for img_url in img_urls[:5]:  # Limit to first 5 images
            if img_url:
                absolute_img_url = urljoin(response.url, img_url)
                images.append(absolute_img_url)
        return images

    def _extract_published_date(self, response):
        """Extract published date with enhanced detection"""
        import re
        from datetime import datetime
        
        # 1. Try meta tags first (most reliable)
        meta_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[property="article:modified_time"]::attr(content)',
            'meta[name="pubdate"]::attr(content)',
            'meta[name="date"]::attr(content)',
            'meta[name="DC.date"]::attr(content)',
            'meta[name="DC.Date.Created"]::attr(content)',
        ]
        
        for selector in meta_selectors:
            date_text = response.css(selector).get()
            if date_text:
                parsed_date = self._parse_date_string(date_text.strip())
                if parsed_date:
                    return parsed_date
        
        # 2. Try structured data (JSON-LD)
        json_ld_scripts = response.css('script[type="application/ld+json"]::text').getall()
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script)
                if isinstance(data, dict):
                    for date_field in ['datePublished', 'dateCreated', 'dateModified']:
                        if date_field in data:
                            parsed_date = self._parse_date_string(data[date_field])
                            if parsed_date:
                                return parsed_date
            except:
                continue
        
        # 3. Try HTML time elements
        time_selectors = [
            'time::attr(datetime)',
            'time[datetime]::attr(datetime)',
            'time::text',
            '.publish-time::text',
            '.post-time::text',
        ]
        
        for selector in time_selectors:
            date_text = response.css(selector).get()
            if date_text:
                parsed_date = self._parse_date_string(date_text.strip())
                if parsed_date:
                    return parsed_date
        
        # 4. Try common date class patterns
        date_class_selectors = [
            '.publish-date::text',
            '.publication-date::text',
            '.post-date::text',
            '.news-date::text',
            '.article-date::text',
            '.date::text',
            '[class*="date"]::text',
            '[class*="time"]::text',
            '.created-date::text',
            '.updated-date::text',
        ]
        
        for selector in date_class_selectors:
            date_texts = response.css(selector).getall()
            for date_text in date_texts:
                if date_text:
                    parsed_date = self._parse_date_string(date_text.strip())
                    if parsed_date:
                        return parsed_date
        
        # 5. Try to extract from URL patterns
        url_date_patterns = [
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2024/12/18/
            r'/(\d{4})(\d{2})(\d{2})/',        # /20241218/
            r'date=(\d{4}-\d{2}-\d{2})',       # ?date=2024-12-18
            r'time=(\d{4}\d{2}\d{2})',         # ?time=20241218
        ]
        
        for pattern in url_date_patterns:
            match = re.search(pattern, response.url)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    try:
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except:
                        continue
                elif len(match.groups()) == 1:
                    parsed_date = self._parse_date_string(match.group(1))
                    if parsed_date:
                        return parsed_date
        
        # 6. Try to extract from page content (last resort)
        content_date_patterns = [
            r'發布日期[：:\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            r'發表時間[：:\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            r'更新時間[：:\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',  # Generic date pattern
        ]
        
        page_text = response.text
        for pattern in content_date_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                parsed_date = self._parse_date_string(match)
                if parsed_date:
                    return parsed_date
        
        # 7. Use last-modified header as fallback
        last_modified = response.headers.get('Last-Modified')
        if last_modified:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(last_modified.decode())
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        return ""
    
    def _parse_date_string(self, date_str):
        """Parse various date string formats and return standardized YYYY-MM-DD"""
        if not date_str:
            return None
            
        # Clean the date string
        date_str = re.sub(r'[年月日]', '-', date_str)
        date_str = re.sub(r'[-/\s]+', '-', date_str)
        date_str = re.sub(r'[^\d-]', '', date_str)
        
        # Common date patterns to try
        date_patterns = [
            r'^(\d{4})-(\d{1,2})-(\d{1,2})$',      # 2024-12-18
            r'^(\d{4})(\d{2})(\d{2})$',             # 20241218
            r'^(\d{1,2})-(\d{1,2})-(\d{4})$',      # 18-12-2024
            r'^(\d{1,2})/(\d{1,2})/(\d{4})$',      # 18/12/2024
        ]
        
        for pattern in date_patterns:
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # Year first
                            year, month, day = groups
                        else:  # Day/Month first
                            day, month, year = groups
                        
                        # Validate date
                        from datetime import datetime
                        dt = datetime(int(year), int(month), int(day))
                        
                        # Only return dates that are reasonable (not too old or future)
                        current_year = datetime.now().year
                        if 2000 <= dt.year <= current_year + 1:
                            return dt.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None

    # Additional extraction methods for specific item types
    def _extract_news_type(self, response):
        """Extract news type (press release, etc.)"""
        if '新聞稿' in response.text or 'press' in response.url.lower():
            return 'press_release'
        return 'general_news'

    def _extract_department(self, response):
        """Extract responsible department"""
        # Look for department mentions in content
        dept_pattern = r'([\u4e00-\u9fff]+部|[\u4e00-\u9fff]+中心|[\u4e00-\u9fff]+組)'
        match = re.search(dept_pattern, response.text)
        return match.group(1) if match else ""

    def _extract_contact_info(self, response):
        """Extract contact information"""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, response.text)
        if emails:
            contact_info['email'] = emails[0]
            
        # Phone pattern (Taiwan format)
        phone_pattern = r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})'
        phones = re.findall(phone_pattern, response.text)
        if phones:
            contact_info['phone'] = phones[0]
            
        return contact_info

    def _extract_research_area(self, response):
        """Extract research area"""
        research_areas = [
            '資通訊', '電子', '機械', '材料', '化工', '生醫',
            '綠能', '光電', '奈米', '智慧系統'
        ]
        
        for area in research_areas:
            if area in response.text:
                return area
        return ""

    def _extract_technology_type(self, response):
        """Extract technology type"""
        tech_types = [
            '人工智慧', '機器學習', '物聯網', '區塊鏈',
            '5G', '半導體', '感測器', '機器人',
            '生物技術', '奈米技術'
        ]
        
        for tech in tech_types:
            if tech in response.text:
                return tech
        return ""

    def _extract_applications(self, response):
        """Extract application areas"""
        applications = []
        app_keywords = [
            '智慧城市', '智慧交通', '智慧醫療', '智慧製造',
            '環保', '節能', '安全監控', '自動化'
        ]
        
        for app in app_keywords:
            if app in response.text:
                applications.append(app)
        
        return applications

    def _extract_keywords(self, content):
        """Extract technical keywords from content"""
        # This is a simplified version - could be enhanced with NLP
        keywords = []
        tech_keywords = [
            'AI', 'IoT', '5G', '半導體', '生技', '綠能',
            '智慧製造', '數位轉型', '創新', '研發'
        ]
        
        for keyword in tech_keywords:
            if keyword in content:
                keywords.append(keyword)
        
        return keywords

    def _extract_service_type(self, response):
        """Extract service type"""
        service_types = [
            '技術服務', '檢測驗證', '人才培育', '育成輔導',
            '技術移轉', '產業合作', '顧問諮詢'
        ]
        
        for service in service_types:
            if service in response.text:
                return service
        return ""

    def _extract_target_industry(self, response):
        """Extract target industry"""
        industries = [
            '半導體', '電子', '機械', '生技醫療', '化工',
            '紡織', '食品', '綠能', '資服', '金融'
        ]
        
        for industry in industries:
            if industry in response.text:
                return industry
        return ""

    def _extract_collaboration_type(self, response):
        """Extract collaboration type"""
        collab_types = [
            '委託研究', '合作開發', '技術移轉', '人才交流',
            '共同研發', '產學合作'
        ]
        
        for collab in collab_types:
            if collab in response.text:
                return collab
        return ""
