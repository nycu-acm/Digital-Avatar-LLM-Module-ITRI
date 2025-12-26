#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI Comprehensive Data Crawler 2025
Advanced crawler for collecting all ITRI 工研院 related information from multiple sources.
Designed for dataset_202512 with enhanced data quality and structure.
"""

import os
import sys
import requests
import urllib3
import json
import re
import time
import hashlib
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('itri_crawler_2025.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CrawledContent:
    """Structure for crawled content"""
    source: str
    url: str
    title: str
    content: str
    language: str
    content_type: str
    metadata: Dict[str, Any]
    crawled_at: str
    content_hash: str

class ITRIComprehensiveCrawler2025:
    def __init__(self, output_dir: str = "dataset_202512"):
        """Initialize the comprehensive ITRI crawler"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.data_dirs = {
            'wikipedia': self.output_dir / 'wikipedia_data',
            'official_website': self.output_dir / 'official_website_data', 
            'virtual_museum': self.output_dir / 'virtual_museum_data',
            'news': self.output_dir / 'news_data',
            'research': self.output_dir / 'research_data',
            'sdgs': self.output_dir / 'sdgs_data',
            'social_media': self.output_dir / 'social_media_data',
            'raw_html': self.output_dir / 'raw_html',
            'processed': self.output_dir / 'processed'
        }
        
        for dir_path in self.data_dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Session configuration
        self.session = requests.Session()
        # Add SSL certificate verification handling for problematic websites
        self.session.verify = False  # Disable SSL verification for sites with cert issues
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Crawling configuration
        self.config = {
            'max_retries': 3,
            'timeout': 120,  # 2 minutes timeout
            'delay_between_requests': 1.0,
            'concurrent_workers': 5,
            'max_content_length': 10 * 1024 * 1024  # 10MB limit
        }
        
        # Data sources configuration
        self.data_sources = {
            'wikipedia': {
                'zh-tw': 'https://zh.wikipedia.org/zh-tw/工業技術研究院',
                'en': 'https://en.wikipedia.org/wiki/Industrial_Technology_Research_Institute'
            },
            'official_website': {
                'base_url': 'https://www.itri.org.tw',
                'key_pages': [
                    '/index.aspx',
                    '/chi/Content/Messagess/contents.aspx?SiteID=1&MmmID=1036233376112763651&MGID=1036667243556261540',
                    '/chi/Content/Messagess/contents.aspx?SiteID=1&MmmID=1036233376112763651&MGID=1036667243556261541',
                    '/eng/index.aspx',
                    '/chi/about/',
                    '/eng/about/',
                    '/chi/research/',
                    '/eng/research/',
                    '/chi/news/',
                    '/eng/news/'
                ]
            },
            'virtual_museum': {
                'istaging_base': 'https://livetour.istaging.com/f61aa0a8-c677-4232-901d-c1fda7ffb785',
                'group_id': '6e760cfc-cfa4-4b4f-b227-0ca674b18638',
                'locales': ['us', 'zh-tw'],
                'max_scenes': 15
            },
            'news_sources': [
                'https://www.itri.org.tw/chi/news/',
                'https://www.itri.org.tw/eng/news/',
                'https://technews.tw/tag/itri/',
                'https://www.digitimes.com.tw/search/?keyword=工研院'
            ]
        }
        
        # Initialize crawled content storage
        self.crawled_content: List[CrawledContent] = []
        self.url_cache = set()
        
        logger.info(f"ITRI Comprehensive Crawler 2025 initialized. Output directory: {self.output_dir}")

    def crawl_all_sources(self) -> Dict[str, Any]:
        """Crawl all ITRI data sources comprehensively"""
        logger.info("🚀 Starting comprehensive ITRI data crawling...")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'sources_crawled': {},
            'total_content_items': 0,
            'errors': [],
            'summary': {}
        }
        
        try:
            # 1. Crawl Wikipedia sources
            logger.info("📚 Crawling Wikipedia sources...")
            wiki_results = self._crawl_wikipedia_sources()
            results['sources_crawled']['wikipedia'] = wiki_results
            
            # 2. Crawl official website
            logger.info("🏢 Crawling official ITRI website...")
            official_results = self._crawl_official_website()
            results['sources_crawled']['official_website'] = official_results
            
            # 3. Crawl virtual museum
            logger.info("🏛️ Crawling ITRI virtual museum...")
            museum_results = self._crawl_virtual_museum()
            results['sources_crawled']['virtual_museum'] = museum_results
            
            # 4. Crawl news sources
            logger.info("📰 Crawling news sources...")
            news_results = self._crawl_news_sources()
            results['sources_crawled']['news'] = news_results
            
            # 5. Process and structure all data
            logger.info("⚙️ Processing and structuring data...")
            self._process_and_structure_data()
            
            # 6. Generate comprehensive dataset
            logger.info("📊 Generating comprehensive dataset...")
            dataset_info = self._generate_comprehensive_dataset()
            results['dataset_info'] = dataset_info
            
            results['total_content_items'] = len(self.crawled_content)
            results['end_time'] = datetime.now().isoformat()
            
            # Save crawling results
            self._save_crawling_results(results)
            
            logger.info(f"✅ Crawling completed! Total items: {len(self.crawled_content)}")
            
        except Exception as e:
            logger.error(f"❌ Error during crawling: {e}")
            results['errors'].append(str(e))
            
        return results

    def _crawl_wikipedia_sources(self) -> Dict[str, Any]:
        """Crawl Wikipedia sources for ITRI information"""
        wiki_results = {'pages_crawled': 0, 'content_items': 0, 'errors': []}
        
        for lang, url in self.data_sources['wikipedia'].items():
            try:
                logger.info(f"Crawling Wikipedia ({lang}): {url}")
                content = self._fetch_and_parse_wikipedia(url, lang)
                
                if content:
                    # Save raw content
                    self._save_raw_content(content, 'wikipedia', f'wikipedia_{lang}')
                    
                    # Process and structure
                    structured_content = self._structure_wikipedia_content(content, lang)
                    self.crawled_content.extend(structured_content)
                    
                    wiki_results['pages_crawled'] += 1
                    wiki_results['content_items'] += len(structured_content)
                    
                    logger.info(f"✅ Wikipedia ({lang}) crawled successfully: {len(structured_content)} items")
                
                time.sleep(self.config['delay_between_requests'])
                
            except Exception as e:
                error_msg = f"Error crawling Wikipedia ({lang}): {e}"
                logger.error(error_msg)
                wiki_results['errors'].append(error_msg)
        
        return wiki_results

    def _fetch_and_parse_wikipedia(self, url: str, lang: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse Wikipedia page content"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract comprehensive Wikipedia content
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                return None
            
            data = {
                'url': url,
                'language': lang,
                'title': soup.find('h1', {'id': 'firstHeading'}).get_text(strip=True) if soup.find('h1', {'id': 'firstHeading'}) else 'ITRI',
                'metadata': {
                    'organization_name': '工業技術研究院 (Industrial Technology Research Institute)',
                    'english_name': 'Industrial Technology Research Institute',
                    'abbreviation': 'ITRI',
                    'crawled_at': datetime.now().isoformat(),
                    'source_url': url,
                    'language': lang
                },
                'infobox_data': {},
                'sections': {},
                'tables': {},
                'lists': {},
                'references': [],
                'external_links': [],
                'categories': [],
                'raw_text': ""
            }
            
            # Extract infobox
            self._extract_wikipedia_infobox(soup, data)
            
            # Extract all sections
            self._extract_wikipedia_sections(content_div, data)
            
            # Extract tables
            self._extract_wikipedia_tables(content_div, data)
            
            # Extract lists
            self._extract_wikipedia_lists(content_div, data)
            
            # Extract references and links
            self._extract_wikipedia_references(soup, data)
            
            # Extract categories
            self._extract_wikipedia_categories(soup, data)
            
            # Extract raw text
            data['raw_text'] = content_div.get_text(separator='\n', strip=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia page {url}: {e}")
            return None

    def _extract_wikipedia_infobox(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract infobox data from Wikipedia"""
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data['infobox_data'][key] = value

    def _extract_wikipedia_sections(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract all sections from Wikipedia content"""
        current_section = None
        current_content = []
        
        for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'ul', 'ol']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section
                if current_section and current_content:
                    data['sections'][current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = element.get_text(strip=True)
                current_content = []
                
            elif element.name in ['p', 'div', 'ul', 'ol']:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short content
                    current_content.append(text)
        
        # Save last section
        if current_section and current_content:
            data['sections'][current_section] = '\n'.join(current_content)

    def _extract_wikipedia_tables(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract tables from Wikipedia content"""
        tables = content_div.find_all('table')
        for i, table in enumerate(tables):
            if 'infobox' not in table.get('class', []):
                rows = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                
                if rows:
                    data['tables'][f'table_{i+1}'] = {'rows': rows}

    def _extract_wikipedia_lists(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract lists from Wikipedia content"""
        lists = content_div.find_all(['ul', 'ol'])
        for i, list_elem in enumerate(lists):
            items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
            if items:
                data['lists'][f'list_{i+1}'] = items

    def _extract_wikipedia_references(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract references and external links"""
        # References
        ref_section = soup.find('div', {'class': 'mw-references-wrap'})
        if ref_section:
            refs = ref_section.find_all('li')
            data['references'] = [ref.get_text(strip=True) for ref in refs]
        
        # External links
        ext_links_section = soup.find('span', {'id': '外部連結'}) or soup.find('span', {'id': 'External_links'})
        if ext_links_section:
            parent = ext_links_section.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem and next_elem.name == 'ul':
                    links = next_elem.find_all('a', href=True)
                    data['external_links'] = [{'text': link.get_text(strip=True), 'url': link['href']} for link in links]

    def _extract_wikipedia_categories(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract categories from Wikipedia"""
        cat_links = soup.find('div', {'id': 'mw-normal-catlinks'})
        if cat_links:
            categories = cat_links.find_all('a')
            data['categories'] = [cat.get_text(strip=True) for cat in categories if cat.get_text(strip=True)]

    def _structure_wikipedia_content(self, content: Dict[str, Any], lang: str) -> List[CrawledContent]:
        """Structure Wikipedia content into CrawledContent objects"""
        structured_items = []
        
        # Main article content
        main_content = CrawledContent(
            source='wikipedia',
            url=content['url'],
            title=content['title'],
            content=content['raw_text'],
            language=lang,
            content_type='article',
            metadata=content['metadata'],
            crawled_at=datetime.now().isoformat(),
            content_hash=hashlib.md5(content['raw_text'].encode()).hexdigest()
        )
        structured_items.append(main_content)
        
        # Individual sections
        for section_name, section_content in content['sections'].items():
            if len(section_content.strip()) > 50:  # Only include substantial sections
                section_item = CrawledContent(
                    source='wikipedia',
                    url=content['url'] + f'#{section_name}',
                    title=f"{content['title']} - {section_name}",
                    content=section_content,
                    language=lang,
                    content_type='section',
                    metadata={**content['metadata'], 'section_name': section_name},
                    crawled_at=datetime.now().isoformat(),
                    content_hash=hashlib.md5(section_content.encode()).hexdigest()
                )
                structured_items.append(section_item)
        
        # Infobox as structured data
        if content['infobox_data']:
            infobox_text = '\n'.join([f"{k}: {v}" for k, v in content['infobox_data'].items()])
            infobox_item = CrawledContent(
                source='wikipedia',
                url=content['url'] + '#infobox',
                title=f"{content['title']} - 基本資訊",
                content=infobox_text,
                language=lang,
                content_type='infobox',
                metadata={**content['metadata'], 'data_type': 'structured'},
                crawled_at=datetime.now().isoformat(),
                content_hash=hashlib.md5(infobox_text.encode()).hexdigest()
            )
            structured_items.append(infobox_item)
        
        return structured_items

    def _crawl_official_website(self) -> Dict[str, Any]:
        """Crawl official ITRI website"""
        official_results = {'pages_crawled': 0, 'content_items': 0, 'errors': []}
        
        base_url = self.data_sources['official_website']['base_url']
        key_pages = self.data_sources['official_website']['key_pages']
        
        for page_path in key_pages:
            try:
                full_url = urljoin(base_url, page_path)
                logger.info(f"Crawling official website: {full_url}")
                
                content = self._fetch_and_parse_official_page(full_url)
                
                if content:
                    # Save raw content
                    page_name = page_path.replace('/', '_').replace('.aspx', '').strip('_')
                    self._save_raw_content(content, 'official_website', f'official_{page_name}')
                    
                    # Structure content
                    structured_content = self._structure_official_content(content)
                    self.crawled_content.extend(structured_content)
                    
                    official_results['pages_crawled'] += 1
                    official_results['content_items'] += len(structured_content)
                    
                    logger.info(f"✅ Official page crawled: {len(structured_content)} items")
                
                time.sleep(self.config['delay_between_requests'])
                
            except Exception as e:
                error_msg = f"Error crawling official page {page_path}: {e}"
                logger.error(error_msg)
                official_results['errors'].append(error_msg)
        
        return official_results

    def _fetch_and_parse_official_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse official ITRI website page"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else url.split('/')[-1]
            
            # Extract main content
            main_content = ""
            content_selectors = [
                'div.content',
                'div#content', 
                'main',
                'article',
                'div.main-content',
                'div.page-content'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    main_content = content_div.get_text(separator='\n', strip=True)
                    break
            
            if not main_content:
                # Fallback: get all text from body
                body = soup.find('body')
                if body:
                    main_content = body.get_text(separator='\n', strip=True)
            
            # Extract navigation and links
            navigation = []
            for link in soup.find_all('a', href=True):
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if text and href:
                    navigation.append({
                        'text': text,
                        'href': href,
                        'title': link.get('title', '')
                    })
            
            # Extract sections based on headings
            sections = {}
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if heading_text:
                    # Get content until next heading
                    content = []
                    next_element = heading.find_next_sibling()
                    
                    while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        if next_element.name in ['p', 'div', 'span', 'li']:
                            text = next_element.get_text(strip=True)
                            if text:
                                content.append(text)
                        next_element = next_element.find_next_sibling()
                    
                    if content:
                        sections[heading_text] = '\n'.join(content)
            
            # Detect language
            language = 'zh-tw' if re.search(r'[\u4e00-\u9fff]', main_content) else 'en'
            
            return {
                'url': url,
                'title': title,
                'main_content': main_content,
                'sections': sections,
                'navigation': navigation,
                'language': language,
                'metadata': {
                    'source': 'official_website',
                    'crawled_at': datetime.now().isoformat(),
                    'content_length': len(main_content)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching official page {url}: {e}")
            return None

    def _structure_official_content(self, content: Dict[str, Any]) -> List[CrawledContent]:
        """Structure official website content into CrawledContent objects"""
        structured_items = []
        
        # Main page content
        if content['main_content']:
            main_item = CrawledContent(
                source='official_website',
                url=content['url'],
                title=content['title'],
                content=content['main_content'],
                language=content['language'],
                content_type='webpage',
                metadata=content['metadata'],
                crawled_at=datetime.now().isoformat(),
                content_hash=hashlib.md5(content['main_content'].encode()).hexdigest()
            )
            structured_items.append(main_item)
        
        # Individual sections
        for section_name, section_content in content['sections'].items():
            if len(section_content.strip()) > 50:
                section_item = CrawledContent(
                    source='official_website',
                    url=content['url'] + f'#{section_name}',
                    title=f"{content['title']} - {section_name}",
                    content=section_content,
                    language=content['language'],
                    content_type='section',
                    metadata={**content['metadata'], 'section_name': section_name},
                    crawled_at=datetime.now().isoformat(),
                    content_hash=hashlib.md5(section_content.encode()).hexdigest()
                )
                structured_items.append(section_item)
        
        return structured_items

    def _crawl_virtual_museum(self) -> Dict[str, Any]:
        """Crawl ITRI virtual museum from iStaging platform"""
        museum_results = {'scenes_crawled': 0, 'content_items': 0, 'errors': []}
        
        base_url = self.data_sources['virtual_museum']['istaging_base']
        group_id = self.data_sources['virtual_museum']['group_id']
        locales = self.data_sources['virtual_museum']['locales']
        max_scenes = self.data_sources['virtual_museum']['max_scenes']
        
        for locale in locales:
            for scene_idx in range(1, max_scenes + 1):
                try:
                    url = f"{base_url}?group={group_id}&locale={locale}&index={scene_idx}"
                    logger.info(f"Crawling virtual museum scene {scene_idx} ({locale})")
                    
                    content = self._fetch_and_parse_museum_scene(url, scene_idx, locale)
                    
                    if content:
                        # Save raw content
                        scene_name = f'scene_{scene_idx}_{locale}'
                        self._save_raw_content(content, 'virtual_museum', scene_name)
                        
                        # Structure content
                        structured_content = self._structure_museum_content(content)
                        self.crawled_content.extend(structured_content)
                        
                        museum_results['scenes_crawled'] += 1
                        museum_results['content_items'] += len(structured_content)
                        
                        logger.info(f"✅ Museum scene {scene_idx} ({locale}) crawled: {len(structured_content)} items")
                    
                    time.sleep(self.config['delay_between_requests'])
                    
                except Exception as e:
                    error_msg = f"Error crawling museum scene {scene_idx} ({locale}): {e}"
                    logger.error(error_msg)
                    museum_results['errors'].append(error_msg)
        
        return museum_results

    def _fetch_and_parse_museum_scene(self, url: str, scene_idx: int, locale: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse virtual museum scene"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            
            # Check if scene exists (404 or empty response means no more scenes)
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract scene information
            scene_data = {
                'url': url,
                'scene_index': scene_idx,
                'locale': locale,
                'title': f"ITRI Virtual Museum - Scene {scene_idx}",
                'content': '',
                'metadata': {
                    'source': 'virtual_museum',
                    'scene_index': scene_idx,
                    'locale': locale,
                    'crawled_at': datetime.now().isoformat()
                }
            }
            
            # Extract all text content
            # Remove scripts and styles first
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            # Get all text content
            all_text = soup.get_text(separator='\n', strip=True)
            scene_data['content'] = all_text
            
            # Try to extract structured data from JavaScript or JSON-LD
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = script.get_text()
                if 'scene' in script_content.lower() or 'tour' in script_content.lower():
                    # Try to extract JSON data
                    json_matches = re.findall(r'\{[^{}]*\}', script_content)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict) and any(key in data for key in ['title', 'description', 'content']):
                                scene_data['metadata']['structured_data'] = data
                                break
                        except json.JSONDecodeError:
                            continue
            
            return scene_data
            
        except Exception as e:
            logger.error(f"Error fetching museum scene {url}: {e}")
            return None

    def _structure_museum_content(self, content: Dict[str, Any]) -> List[CrawledContent]:
        """Structure virtual museum content into CrawledContent objects"""
        structured_items = []
        
        if content['content']:
            museum_item = CrawledContent(
                source='virtual_museum',
                url=content['url'],
                title=content['title'],
                content=content['content'],
                language=content['locale'].replace('us', 'en'),
                content_type='virtual_tour',
                metadata=content['metadata'],
                crawled_at=datetime.now().isoformat(),
                content_hash=hashlib.md5(content['content'].encode()).hexdigest()
            )
            structured_items.append(museum_item)
        
        return structured_items

    def _crawl_news_sources(self) -> Dict[str, Any]:
        """Crawl news sources for ITRI information"""
        news_results = {'sources_crawled': 0, 'content_items': 0, 'errors': []}
        
        # For now, we'll implement basic news crawling
        # This can be expanded to include RSS feeds, news APIs, etc.
        
        for news_url in self.data_sources['news_sources']:
            try:
                logger.info(f"Crawling news source: {news_url}")
                
                content = self._fetch_and_parse_news_page(news_url)
                
                if content:
                    # Save raw content
                    source_name = urlparse(news_url).netloc.replace('.', '_')
                    self._save_raw_content(content, 'news', f'news_{source_name}')
                    
                    # Structure content
                    structured_content = self._structure_news_content(content)
                    self.crawled_content.extend(structured_content)
                    
                    news_results['sources_crawled'] += 1
                    news_results['content_items'] += len(structured_content)
                    
                    logger.info(f"✅ News source crawled: {len(structured_content)} items")
                
                time.sleep(self.config['delay_between_requests'])
                
            except Exception as e:
                error_msg = f"Error crawling news source {news_url}: {e}"
                logger.error(error_msg)
                news_results['errors'].append(error_msg)
        
        return news_results

    def _fetch_and_parse_news_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse news page"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else url
            
            # Extract main content
            main_content = soup.get_text(separator='\n', strip=True)
            
            # Detect language
            language = 'zh-tw' if re.search(r'[\u4e00-\u9fff]', main_content) else 'en'
            
            return {
                'url': url,
                'title': title,
                'content': main_content,
                'language': language,
                'metadata': {
                    'source': 'news',
                    'crawled_at': datetime.now().isoformat(),
                    'content_length': len(main_content)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching news page {url}: {e}")
            return None

    def _structure_news_content(self, content: Dict[str, Any]) -> List[CrawledContent]:
        """Structure news content into CrawledContent objects"""
        structured_items = []
        
        if content['content']:
            news_item = CrawledContent(
                source='news',
                url=content['url'],
                title=content['title'],
                content=content['content'],
                language=content['language'],
                content_type='news',
                metadata=content['metadata'],
                crawled_at=datetime.now().isoformat(),
                content_hash=hashlib.md5(content['content'].encode()).hexdigest()
            )
            structured_items.append(news_item)
        
        return structured_items

    def _save_raw_content(self, content: Dict[str, Any], source_type: str, filename: str):
        """Save raw content to files"""
        try:
            # Save as JSON
            json_path = self.data_dirs['raw_html'] / f"{filename}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            # Save main content as text
            if 'content' in content:
                text_path = self.data_dirs['raw_html'] / f"{filename}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(content['content'])
            elif 'main_content' in content:
                text_path = self.data_dirs['raw_html'] / f"{filename}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(content['main_content'])
            
        except Exception as e:
            logger.error(f"Error saving raw content for {filename}: {e}")

    def _process_and_structure_data(self):
        """Process and structure all crawled data"""
        logger.info("Processing and structuring crawled data...")
        
        # Group content by source and language
        grouped_content = {}
        for item in self.crawled_content:
            key = f"{item.source}_{item.language}"
            if key not in grouped_content:
                grouped_content[key] = []
            grouped_content[key].append(item)
        
        # Save grouped content
        for group_key, items in grouped_content.items():
            group_data = {
                'metadata': {
                    'group': group_key,
                    'total_items': len(items),
                    'processed_at': datetime.now().isoformat()
                },
                'items': [asdict(item) for item in items]
            }
            
            group_file = self.data_dirs['processed'] / f"{group_key}.json"
            with open(group_file, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processed {len(grouped_content)} content groups")

    def _generate_comprehensive_dataset(self) -> Dict[str, Any]:
        """Generate comprehensive dataset for RAG system"""
        logger.info("Generating comprehensive dataset...")
        
        # Create comprehensive dataset structure
        dataset = {
            'metadata': {
                'dataset_name': 'ITRI_Comprehensive_Dataset_2025',
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'total_content_items': len(self.crawled_content),
                'sources': list(set(item.source for item in self.crawled_content)),
                'languages': list(set(item.language for item in self.crawled_content)),
                'content_types': list(set(item.content_type for item in self.crawled_content))
            },
            'content_summary': {},
            'quality_metrics': {},
            'rag_ready_data': []
        }
        
        # Generate content summary
        for source in dataset['metadata']['sources']:
            source_items = [item for item in self.crawled_content if item.source == source]
            dataset['content_summary'][source] = {
                'total_items': len(source_items),
                'languages': list(set(item.language for item in source_items)),
                'content_types': list(set(item.content_type for item in source_items)),
                'total_characters': sum(len(item.content) for item in source_items)
            }
        
        # Generate RAG-ready data
        for item in self.crawled_content:
            # Filter out very short or very long content
            if 100 <= len(item.content) <= 10000:
                rag_item = {
                    'id': item.content_hash,
                    'source': item.source,
                    'url': item.url,
                    'title': item.title,
                    'content': item.content,
                    'language': item.language,
                    'content_type': item.content_type,
                    'metadata': item.metadata,
                    'crawled_at': item.crawled_at
                }
                dataset['rag_ready_data'].append(rag_item)
        
        # Calculate quality metrics
        dataset['quality_metrics'] = {
            'total_raw_items': len(self.crawled_content),
            'rag_ready_items': len(dataset['rag_ready_data']),
            'quality_ratio': len(dataset['rag_ready_data']) / len(self.crawled_content) if self.crawled_content else 0,
            'avg_content_length': sum(len(item.content) for item in self.crawled_content) / len(self.crawled_content) if self.crawled_content else 0,
            'unique_sources': len(set(item.source for item in self.crawled_content)),
            'language_distribution': {
                lang: len([item for item in self.crawled_content if item.language == lang])
                for lang in set(item.language for item in self.crawled_content)
            }
        }
        
        # Save comprehensive dataset
        dataset_file = self.output_dir / 'itri_comprehensive_dataset_2025.json'
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        # Save RAG-ready data separately
        rag_file = self.output_dir / 'itri_rag_ready_data_2025.json'
        with open(rag_file, 'w', encoding='utf-8') as f:
            json.dump(dataset['rag_ready_data'], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated comprehensive dataset with {len(dataset['rag_ready_data'])} RAG-ready items")
        
        return dataset

    def _save_crawling_results(self, results: Dict[str, Any]):
        """Save crawling results and statistics"""
        results_file = self.output_dir / 'crawling_results_2025.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Generate summary report
        summary_report = f"""
# ITRI Comprehensive Data Crawling Report 2025

## Summary
- **Start Time**: {results.get('start_time', 'N/A')}
- **End Time**: {results.get('end_time', 'N/A')}
- **Total Content Items**: {results.get('total_content_items', 0)}

## Sources Crawled
"""
        
        for source, source_results in results.get('sources_crawled', {}).items():
            summary_report += f"\n### {source.title()}\n"
            summary_report += f"- Pages/Items Crawled: {source_results.get('pages_crawled', 0) or source_results.get('scenes_crawled', 0) or source_results.get('sources_crawled', 0)}\n"
            summary_report += f"- Content Items Generated: {source_results.get('content_items', 0)}\n"
            if source_results.get('errors'):
                summary_report += f"- Errors: {len(source_results['errors'])}\n"
        
        if results.get('errors'):
            summary_report += f"\n## Errors\n"
            for error in results['errors']:
                summary_report += f"- {error}\n"
        
        summary_file = self.output_dir / 'crawling_summary_2025.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        logger.info(f"Crawling results saved to {results_file}")
        logger.info(f"Summary report saved to {summary_file}")

def main():
    """Main function to run the comprehensive ITRI crawler"""
    print("🚀 ITRI Comprehensive Data Crawler 2025")
    print("=" * 50)
    
    # Initialize crawler
    crawler = ITRIComprehensiveCrawler2025("dataset_202512")
    
    # Start crawling
    results = crawler.crawl_all_sources()
    
    print("\n" + "=" * 50)
    print("✅ Crawling completed!")
    print(f"📊 Total content items: {results.get('total_content_items', 0)}")
    print(f"📁 Output directory: dataset_202512")
    print("=" * 50)

if __name__ == "__main__":
    main()
