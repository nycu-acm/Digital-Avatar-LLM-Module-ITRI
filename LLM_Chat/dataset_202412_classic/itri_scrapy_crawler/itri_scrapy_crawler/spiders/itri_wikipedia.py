import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
from ..items import ITRIArticleItem


class ItriWikipediaSpider(scrapy.Spider):
    name = "itri_wikipedia"
    allowed_domains = ["zh.wikipedia.org", "en.wikipedia.org", "wikipedia.org"]
    
    # ITRI-related Wikipedia pages and search terms
    start_urls = [
        # Direct ITRI pages
        "https://zh.wikipedia.org/wiki/%E5%B7%A5%E6%A5%AD%E6%8A%80%E8%A1%93%E7%A0%94%E7%A9%B6%E9%99%A2",  # 工業技術研究院
        "https://en.wikipedia.org/wiki/Industrial_Technology_Research_Institute",
        
        # Related technology and research pages
        "https://zh.wikipedia.org/wiki/Category:%E5%8F%B0%E7%81%A3%E7%A7%91%E6%8A%80",  # Taiwan technology
        "https://zh.wikipedia.org/wiki/Category:%E5%8F%B0%E7%81%A3%E7%A0%94%E7%A9%B6%E6%A9%9F%E6%A7%8B",  # Taiwan research institutions
        
        # Search-based URLs for ITRI-related content
        "https://zh.wikipedia.org/w/api.php?action=opensearch&search=%E5%B7%A5%E7%A0%94%E9%99%A2&limit=10&format=json",
        "https://zh.wikipedia.org/w/api.php?action=opensearch&search=ITRI&limit=10&format=json",
        "https://zh.wikipedia.org/w/api.php?action=opensearch&search=%E5%B7%A5%E6%A5%AD%E6%8A%80%E8%A1%93&limit=10&format=json",
        "https://en.wikipedia.org/w/api.php?action=opensearch&search=Industrial+Technology+Research&limit=10&format=json",
    ]
    
    # Custom settings for Wikipedia crawling
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,
        'USER_AGENT': 'ITRIScrapyBot/1.0 (https://www.itri.org.tw; research@itri.org.tw)',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        }
    }

    def __init__(self, *args, **kwargs):
        super(ItriWikipediaSpider, self).__init__(*args, **kwargs)
        self.crawled_urls = set()
        self.article_count = 0
        self.search_terms = [
            '工研院', 'ITRI', '工業技術研究院',
            '台灣半導體', '台灣科技', '新竹科學園區',
            '人工智慧台灣', '物聯網台灣', '5G台灣'
        ]

    def parse(self, response):
        """Parse Wikipedia pages and API responses"""
        self.logger.info(f'🔍 Parsing Wikipedia page: {response.url}')
        
        # Handle API search responses
        if 'api.php' in response.url and 'opensearch' in response.url:
            yield from self.parse_search_api(response)
            return
            
        # Handle regular Wikipedia pages
        yield from self.parse_wikipedia_page(response)
        
        # Find related links
        yield from self.find_related_links(response)

    def parse_search_api(self, response):
        """Parse Wikipedia OpenSearch API responses"""
        try:
            data = json.loads(response.text)
            if len(data) >= 4:
                titles = data[1]  # Article titles
                descriptions = data[2]  # Article descriptions  
                urls = data[3]  # Article URLs
                
                for title, desc, url in zip(titles, descriptions, urls):
                    if self._is_itri_related(title + " " + desc):
                        if url not in self.crawled_urls:
                            self.crawled_urls.add(url)
                            yield scrapy.Request(
                                url=url,
                                callback=self.parse_wikipedia_page,
                                meta={'search_term': response.meta.get('search_term', ''),
                                      'from_search': True}
                            )
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse API response from {response.url}")

    def parse_wikipedia_page(self, response):
        """Parse individual Wikipedia articles"""
        # Skip if this is a disambiguation or redirect page
        if self._is_disambiguation_page(response) or self._is_redirect_page(response):
            return
            
        title = self._extract_title(response)
        content = self._extract_content(response)
        
        # Check if content is ITRI-related
        if not self._is_itri_related(title + " " + content):
            return
            
        # Skip if content is too short
        if not content or len(content.strip()) < 100:
            return

        # Create article item
        item = ITRIArticleItem()
        item['id'] = self._generate_id(response.url)
        item['title'] = title
        item['content'] = content
        item['url'] = response.url
        item['source'] = 'wikipedia'
        item['language'] = self._detect_language(response.url, content)
        item['content_type'] = 'encyclopedia'
        item['crawled_at'] = datetime.now().isoformat()
        item['category'] = self._extract_category(response)
        item['tags'] = self._extract_tags(title, content)
        item['summary'] = self._extract_summary(response)
        item['images'] = self._extract_images(response)
        item['published_date'] = self._extract_last_modified(response)
        
        # Wikipedia-specific metadata
        item['author'] = 'Wikipedia Contributors'
        item['domain'] = urlparse(response.url).netloc
        item['path'] = urlparse(response.url).path
        item['content_length'] = len(content)
        item['content_quality'] = self._calculate_quality_score(content)

        self.article_count += 1
        self.logger.info(f'✅ Extracted Wikipedia article: {title[:50]}... (#{self.article_count})')
        
        yield item

    def find_related_links(self, response):
        """Find and follow related Wikipedia links"""
        # Get links from "See also" section
        see_also_links = response.css('#See_also + ul a::attr(href), #參見 + ul a::attr(href)').getall()
        
        # Get links from categories
        category_links = response.css('#mw-normal-catlinks a::attr(href)').getall()
        
        # Get links from infobox and main content (but be selective)
        content_links = response.css('.infobox a::attr(href), .mw-parser-output p a::attr(href)').getall()
        
        all_links = see_also_links + category_links + content_links[:10]  # Limit content links
        
        for link in all_links:
            if link and link.startswith('/wiki/'):
                absolute_url = urljoin(response.url, link)
                
                # Skip certain types of pages
                if self._should_skip_link(link):
                    continue
                    
                if absolute_url not in self.crawled_urls:
                    # Check if the link title suggests ITRI relevance
                    link_title = link.replace('/wiki/', '').replace('_', ' ')
                    if self._is_itri_related(link_title):
                        self.crawled_urls.add(absolute_url)
                        yield scrapy.Request(
                            url=absolute_url,
                            callback=self.parse_wikipedia_page,
                            meta={'from_link': True, 'parent_url': response.url}
                        )

        # Also perform additional searches for related terms
        if not response.meta.get('from_search') and self.article_count < 50:
            for search_term in self.search_terms[:3]:  # Limit searches
                search_url = f"https://zh.wikipedia.org/w/api.php?action=opensearch&search={quote(search_term)}&limit=5&format=json"
                yield scrapy.Request(
                    url=search_url,
                    callback=self.parse_search_api,
                    meta={'search_term': search_term}
                )

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
        
        # Secondary related keywords
        secondary_keywords = [
            '台灣科技', '新竹科學園區', '科技研發',
            '半導體研究', '人工智慧研究', '綠能科技',
            '生醫技術', '智慧製造', '物聯網',
            'taiwan technology', 'hsinchu science park',
            'semiconductor research', 'ai research taiwan'
        ]
        
        # Check for primary keywords (high relevance)
        for keyword in primary_keywords:
            if keyword in text_lower:
                return True
                
        # Check for secondary keywords (need at least 2 matches)
        secondary_matches = sum(1 for keyword in secondary_keywords if keyword in text_lower)
        if secondary_matches >= 2:
            return True
            
        return False

    def _should_skip_link(self, link):
        """Check if a Wikipedia link should be skipped"""
        skip_patterns = [
            r'^/wiki/Category:',
            r'^/wiki/Template:',
            r'^/wiki/Help:',
            r'^/wiki/Wikipedia:',
            r'^/wiki/File:',
            r'^/wiki/Special:',
            r'^/wiki/Talk:',
            r'^/wiki/User:',
        ]
        
        return any(re.match(pattern, link) for pattern in skip_patterns)

    def _is_disambiguation_page(self, response):
        """Check if page is a disambiguation page"""
        return bool(response.css('.disambig, #disambig, .hatnote').get())

    def _is_redirect_page(self, response):
        """Check if page is a redirect"""
        return bool(response.css('.redirectText').get())

    def _extract_title(self, response):
        """Extract article title"""
        title = response.css('h1.firstHeading::text').get()
        if title:
            return title.strip()
        
        # Fallback to page title
        title = response.css('title::text').get()
        if title:
            return title.replace(' - Wikipedia', '').replace(' - 維基百科', '').strip()
            
        return response.url.split('/')[-1].replace('_', ' ')

    def _extract_content(self, response):
        """Extract main article content"""
        # Get content from main parser output, excluding certain sections
        content_parts = []
        
        # Main paragraphs
        paragraphs = response.css('.mw-parser-output > p::text, .mw-parser-output > p *::text').getall()
        content_parts.extend([p.strip() for p in paragraphs if p.strip()])
        
        # Section content (but skip references, external links, etc.)
        sections = response.css('.mw-parser-output h2, .mw-parser-output h3').getall()
        for i, section in enumerate(sections):
            section_title = response.css('.mw-parser-output h2, .mw-parser-output h3')[i].css('::text').get()
            if section_title and not self._is_skip_section(section_title):
                # Get content until next section
                section_content = response.css(f'.mw-parser-output h2:nth-of-type({i+1}) ~ p::text, .mw-parser-output h3:nth-of-type({i+1}) ~ p::text').getall()
                content_parts.extend([p.strip() for p in section_content[:3] if p.strip()])  # Limit per section
        
        content = ' '.join(content_parts)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove citation markers like [1], [2], etc.
        content = re.sub(r'\[\d+\]', '', content)
        
        return content

    def _is_skip_section(self, section_title):
        """Check if a section should be skipped"""
        skip_sections = [
            '參考資料', '外部連結', '參見', '註釋',
            'references', 'external links', 'see also', 'notes',
            'bibliography', 'further reading'
        ]
        
        return any(skip_section.lower() in section_title.lower() for skip_section in skip_sections)

    def _extract_summary(self, response):
        """Extract article summary (usually first paragraph)"""
        first_paragraph = response.css('.mw-parser-output > p::text').get()
        if first_paragraph:
            summary = first_paragraph.strip()
            # Limit summary length
            if len(summary) > 300:
                summary = summary[:300] + "..."
            return summary
        return ""

    def _extract_category(self, response):
        """Extract main category from Wikipedia categories"""
        categories = response.css('#mw-normal-catlinks a::text').getall()
        
        # Look for relevant categories
        relevant_categories = []
        for cat in categories:
            cat_lower = cat.lower()
            if any(keyword in cat_lower for keyword in ['科技', '研究', '台灣', 'technology', 'research', 'taiwan']):
                relevant_categories.append(cat)
        
        return relevant_categories[0] if relevant_categories else (categories[0] if categories else 'general')

    def _extract_tags(self, title, content):
        """Extract relevant tags from title and content"""
        tags = []
        
        # Technology-related keywords
        tech_keywords = [
            '人工智慧', 'AI', '機器學習', '深度學習',
            '半導體', '電子', '資通訊', 'ICT',
            '生醫', '醫療', '健康照護',
            '綠能', '再生能源', '節能',
            '智慧製造', '工業4.0', '物聯網', 'IoT',
            '5G', '區塊鏈', '量子', '奈米',
            'artificial intelligence', 'machine learning',
            'semiconductor', 'biotechnology', 'green energy'
        ]
        
        text_to_check = (title + " " + content).lower()
        for keyword in tech_keywords:
            if keyword.lower() in text_to_check:
                tags.append(keyword)
        
        return tags

    def _extract_images(self, response):
        """Extract relevant images from Wikipedia page"""
        images = []
        
        # Get images from infobox and main content
        img_elements = response.css('.infobox img::attr(src), .mw-parser-output img::attr(src)').getall()
        
        for img_src in img_elements[:3]:  # Limit to first 3 images
            if img_src and not img_src.startswith('data:'):
                # Convert to absolute URL
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = urljoin(response.url, img_src)
                images.append(img_src)
        
        return images

    def _extract_last_modified(self, response):
        """Extract last modified date"""
        # Wikipedia shows last modified in footer
        modified_text = response.css('#footer-info-lastmod::text').get()
        if modified_text:
            return modified_text.strip()
        return ""

    def _detect_language(self, url, content):
        """Detect language based on URL and content"""
        if 'zh.wikipedia.org' in url:
            return 'zh-tw'
        elif 'en.wikipedia.org' in url:
            return 'en'
        else:
            # Simple content-based detection
            if re.search(r'[\u4e00-\u9fff]', content):
                return 'zh-tw'
            return 'en'

    def _generate_id(self, url):
        """Generate unique ID for Wikipedia content"""
        return f"wiki_{hash(url) % 1000000:06d}"

    def _calculate_quality_score(self, content):
        """Calculate content quality score"""
        if not content:
            return 0.0
            
        score = 0.5  # Base score
        
        # Length factor
        if len(content) > 200:
            score += 0.2
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1
            
        # Technical content indicators
        tech_indicators = ['技術', '研究', '開發', '創新', 'technology', 'research', 'development', 'innovation']
        tech_count = sum(1 for indicator in tech_indicators if indicator in content.lower())
        score += min(0.1, tech_count * 0.02)
        
        return min(1.0, score)
