import scrapy
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, quote_plus
from ..items import ITRINewsItem


class ItriNewsSpider(scrapy.Spider):
    name = "itri_news"
    allowed_domains = [
        "news.google.com", "technews.tw", "ithome.com.tw", 
        "digitimes.com.tw", "ctee.com.tw", "udn.com",
        "chinatimes.com", "ltn.com.tw", "cna.com.tw",
        "storm.mg", "inside.com.tw", "meet.bnext.com.tw"
    ]
    
    # Search terms for ITRI-related news
    search_terms = [
        "工研院", "ITRI", "工業技術研究院",
        "工研院+AI", "工研院+半導體", "工研院+生醫",
        "工研院+綠能", "工研院+5G", "工研院+物聯網",
        "ITRI+innovation", "ITRI+technology", "ITRI+research"
    ]
    
    def start_requests(self):
        """Generate initial requests for news sources"""
        
        # Google News searches for ITRI
        for term in self.search_terms:
            google_news_url = f"https://news.google.com/rss/search?q={quote_plus(term)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            yield scrapy.Request(
                url=google_news_url,
                callback=self.parse_google_news_rss,
                meta={'search_term': term}
            )
        
        # Direct news site searches
        news_sites = [
            {
                'base_url': 'https://technews.tw',
                'search_path': '/search/{term}/',
                'name': 'TechNews'
            },
            {
                'base_url': 'https://www.ithome.com.tw',
                'search_path': '/search?q={term}',
                'name': 'iThome'
            },
            {
                'base_url': 'https://www.digitimes.com.tw',
                'search_path': '/search/?keyword={term}',
                'name': 'DIGITIMES'
            }
        ]
        
        for site in news_sites:
            for term in ['工研院', 'ITRI']:
                search_url = site['base_url'] + site['search_path'].format(term=quote_plus(term))
                yield scrapy.Request(
                    url=search_url,
                    callback=self.parse_news_site,
                    meta={'site_name': site['name'], 'search_term': term}
                )

    # Custom settings for news crawling
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 6,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        }
    }

    def __init__(self, *args, **kwargs):
        super(ItriNewsSpider, self).__init__(*args, **kwargs)
        self.crawled_urls = set()
        self.news_count = 0
        self.max_news_per_source = 20  # Limit per source to avoid overwhelming

    def parse_google_news_rss(self, response):
        """Parse Google News RSS feed"""
        self.logger.info(f'🔍 Parsing Google News RSS: {response.meta["search_term"]}')
        
        # Extract RSS items
        items = response.css('item')
        
        for item in items[:self.max_news_per_source]:
            title = item.css('title::text').get()
            link = item.css('link::text').get()
            pub_date = item.css('pubDate::text').get()
            description = item.css('description::text').get()
            
            if link and self._is_itri_related(title + " " + (description or "")):
                # Clean Google News redirect URL
                clean_url = self._clean_google_news_url(link)
                
                if clean_url and clean_url not in self.crawled_urls:
                    self.crawled_urls.add(clean_url)
                    yield scrapy.Request(
                        url=clean_url,
                        callback=self.parse_news_article,
                        meta={
                            'title': title,
                            'published_date': pub_date,
                            'source': 'google_news',
                            'search_term': response.meta['search_term']
                        }
                    )

    def parse_news_site(self, response):
        """Parse news site search results"""
        site_name = response.meta['site_name']
        self.logger.info(f'🔍 Parsing {site_name} search results')
        
        # Generic selectors for news articles
        article_selectors = [
            'a[href*="/news/"]::attr(href)',
            'a[href*="/article/"]::attr(href)',
            'a[href*="/story/"]::attr(href)',
            '.news-item a::attr(href)',
            '.article-item a::attr(href)',
            '.post-title a::attr(href)',
            'h2 a::attr(href)', 'h3 a::attr(href)'
        ]
        
        found_links = []
        for selector in article_selectors:
            links = response.css(selector).getall()
            found_links.extend(links)
        
        # Process found article links
        for link in found_links[:self.max_news_per_source]:
            if link:
                absolute_url = urljoin(response.url, link)
                
                if (self._is_valid_news_url(absolute_url) and 
                    absolute_url not in self.crawled_urls):
                    
                    self.crawled_urls.add(absolute_url)
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.parse_news_article,
                        meta={
                            'source': site_name.lower(),
                            'search_term': response.meta['search_term']
                        }
                    )

    def parse_news_article(self, response):
        """Parse individual news articles"""
        # Skip if not ITRI-related after full content check
        title = self._extract_title(response)
        content = self._extract_content(response)
        
        if not self._is_itri_related(title + " " + content):
            return
            
        # Skip if content is too short
        if not content or len(content.strip()) < 100:
            return

        # Create news item
        item = ITRINewsItem()
        item['id'] = self._generate_id(response.url)
        item['title'] = title
        item['content'] = content
        item['url'] = response.url
        item['source'] = response.meta.get('source', 'unknown')
        item['language'] = self._detect_language(content)
        item['crawled_at'] = datetime.now().isoformat()
        item['category'] = self._extract_category(response)
        item['summary'] = self._generate_summary(content)
        item['tags'] = self._extract_tags(title, content)
        item['published_date'] = self._extract_published_date(response)
        
        # News-specific fields
        item['news_type'] = self._determine_news_type(title, content)
        item['department'] = self._extract_department(content)
        item['contact_info'] = self._extract_contact_info(content)

        self.news_count += 1
        self.logger.info(f'✅ Extracted news: {title[:50]}... (#{self.news_count})')
        
        yield item

    def _clean_google_news_url(self, google_url):
        """Clean Google News redirect URL to get actual article URL"""
        if 'news.google.com' in google_url and 'url=' in google_url:
            # Extract the actual URL from Google News redirect
            import urllib.parse
            parsed = urllib.parse.urlparse(google_url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'url' in params:
                return params['url'][0]
        return google_url

    def _is_valid_news_url(self, url):
        """Check if URL is a valid news article URL"""
        # Skip certain file types and non-article pages
        skip_patterns = [
            r'\.(pdf|doc|docx|jpg|jpeg|png|gif|css|js)$',
            r'/(tag|category|author|search)/',
            r'/page/\d+',
            r'#comment',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
                
        # Must be from allowed domains
        domain = urlparse(url).netloc
        return any(allowed_domain in domain for allowed_domain in self.allowed_domains)

    def _is_itri_related(self, text):
        """Check if text content is related to ITRI"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Primary ITRI keywords
        primary_keywords = [
            '工研院', 'itri', '工業技術研究院',
            'industrial technology research institute'
        ]
        
        # Check for primary keywords
        for keyword in primary_keywords:
            if keyword in text_lower:
                return True
                
        return False

    def _extract_title(self, response):
        """Extract article title"""
        # Try multiple title selectors
        title_selectors = [
            'h1::text',
            '.article-title::text',
            '.post-title::text',
            '.news-title::text',
            'title::text',
            '.entry-title::text'
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                title = title.strip()
                # Clean up common title suffixes
                title = re.sub(r'\s*[-|]\s*.+$', '', title)
                return title
        
        return response.url.split('/')[-1]

    def _extract_content(self, response):
        """Extract main article content"""
        # Try multiple content selectors
        content_selectors = [
            '.article-content',
            '.post-content',
            '.news-content',
            '.entry-content',
            '.content',
            'article',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_elements = response.css(selector)
            if content_elements:
                # Get text content, preserve paragraphs
                paragraphs = content_elements.css('p::text').getall()
                if paragraphs:
                    content = ' '.join([p.strip() for p in paragraphs if p.strip()])
                    content = re.sub(r'\s+', ' ', content).strip()
                    if len(content) > 50:
                        return content
        
        # Fallback: get all paragraph text
        paragraphs = response.css('p::text').getall()
        content = ' '.join([p.strip() for p in paragraphs if len(p.strip()) > 10])
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

    def _extract_published_date(self, response):
        """Extract published date"""
        # Try multiple date selectors
        date_selectors = [
            'time::attr(datetime)',
            'time::text',
            '.publish-date::text',
            '.post-date::text',
            '.news-date::text',
            '[class*="date"]::text',
            'meta[property="article:published_time"]::attr(content)'
        ]
        
        for selector in date_selectors:
            date_text = response.css(selector).get()
            if date_text:
                return date_text.strip()
        
        # Try to extract from URL or content
        url_date_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', response.url)
        if url_date_match:
            year, month, day = url_date_match.groups()
            return f"{year}-{month:0>2}-{day:0>2}"
        
        return ""

    def _extract_category(self, response):
        """Extract news category"""
        # Try breadcrumb or category indicators
        category_selectors = [
            '.breadcrumb a::text',
            '.category::text',
            '.tag::text',
            'nav a::text'
        ]
        
        for selector in category_selectors:
            categories = response.css(selector).getall()
            if categories:
                # Look for tech-related categories
                for cat in categories:
                    cat_lower = cat.lower()
                    if any(keyword in cat_lower for keyword in ['科技', '技術', '創新', 'tech', 'innovation']):
                        return cat.strip()
                return categories[0].strip()
        
        return 'technology'

    def _extract_tags(self, title, content):
        """Extract relevant tags from title and content"""
        tags = []
        
        # ITRI-related keywords
        itri_keywords = [
            '人工智慧', 'AI', '機器學習', '深度學習',
            '半導體', '電子', '資通訊', 'ICT',
            '生醫', '醫療', '健康照護',
            '綠能', '再生能源', '節能',
            '智慧製造', '工業4.0', '物聯網', 'IoT',
            '5G', '區塊鏈', '創新', '研發',
            '技術轉移', '產業合作', '新創'
        ]
        
        text_to_check = (title + " " + content).lower()
        for keyword in itri_keywords:
            if keyword.lower() in text_to_check:
                tags.append(keyword)
        
        return tags

    def _generate_summary(self, content, max_length=200):
        """Generate article summary"""
        # Take first meaningful sentences
        sentences = re.split(r'[。！？.!?]', content)
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15:  # Skip very short sentences
                if len(summary + sentence) < max_length:
                    summary += sentence + "。"
                else:
                    break
        return summary.strip()

    def _determine_news_type(self, title, content):
        """Determine type of news"""
        title_content = (title + " " + content).lower()
        
        if any(keyword in title_content for keyword in ['新聞稿', 'press release', '發布']):
            return 'press_release'
        elif any(keyword in title_content for keyword in ['研究', 'research', '技術', 'technology']):
            return 'research_news'
        elif any(keyword in title_content for keyword in ['合作', 'collaboration', '簽約', 'partnership']):
            return 'partnership_news'
        elif any(keyword in title_content for keyword in ['獎項', 'award', '得獎', '榮獲']):
            return 'award_news'
        else:
            return 'general_news'

    def _extract_department(self, content):
        """Extract ITRI department mentioned in news"""
        # Look for department patterns
        dept_patterns = [
            r'([\u4e00-\u9fff]+中心)',
            r'([\u4e00-\u9fff]+所)',
            r'([\u4e00-\u9fff]+部)',
            r'([\u4e00-\u9fff]+組)'
        ]
        
        for pattern in dept_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ""

    def _extract_contact_info(self, content):
        """Extract contact information from news"""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, content)
        if emails:
            contact_info['email'] = emails[0]
            
        # Phone pattern (Taiwan format)
        phone_pattern = r'(\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4})'
        phones = re.findall(phone_pattern, content)
        if phones:
            contact_info['phone'] = phones[0]
            
        return contact_info

    def _detect_language(self, text):
        """Simple language detection"""
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh-tw'
        elif re.search(r'[a-zA-Z]', text):
            return 'en'
        return 'unknown'

    def _generate_id(self, url):
        """Generate unique ID for news content"""
        return f"news_{hash(url) % 1000000:06d}"
