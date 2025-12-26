# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DataValidationPipeline:
    """Validate and clean scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validate required fields
        required_fields = ['title', 'content', 'url', 'source']
        for field in required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")
        
        # Clean and validate content
        content = adapter.get('content', '')
        if len(content.strip()) < 50:
            raise DropItem("Content too short (less than 50 characters)")
        
        # Check for footer-only content
        if self._is_footer_only_content(content):
            raise DropItem("Content contains only footer/navigation information")
        
        # Clean content
        cleaned_content = self._clean_content(content)
        if len(cleaned_content.strip()) < 30:
            raise DropItem("Content too short after cleaning")
            
        adapter['content'] = cleaned_content
        adapter['title'] = self._clean_title(adapter.get('title', ''))
        
        # Ensure crawled_at is set
        if not adapter.get('crawled_at'):
            adapter['crawled_at'] = datetime.now().isoformat()
        
        # Generate composite hash for better deduplication
        # Use both content and URL to avoid false positives
        url = adapter.get('url', '')
        title = adapter.get('title', '')
        
        # Create composite string for hashing
        composite_content = f"{content}|{url}|{title}"
        content_hash = hashlib.md5(composite_content.encode('utf-8')).hexdigest()
        
        # Also store individual content hash for analysis
        pure_content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        adapter['content_hash'] = content_hash
        adapter['pure_content_hash'] = pure_content_hash
        
        return item
    
    def _clean_content(self, content):
        """Clean and normalize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common noise patterns including JavaScript warnings and code
        noise_patterns = [
            r'『您的瀏覽器不支援JavaScript功能，若網頁功能無法正常使用時，請開啟瀏覽器JavaScript狀態』\s*',
            r'Your browser does not support JavaScript.*?please enable JavaScript\s*',
            r'請開啟瀏覽器JavaScript功能.*?\s*',
            r'//\s*\(function\s*\([^)]*\)\s*\{.*?\}\)\s*\([^)]*\)\s*;?\s*',  # GTM JavaScript code
            r'function\s*\([^)]*\)\s*\{[^}]*gtm[^}]*\}',  # GTM function blocks
            r'Cookie使用同意書.*?了解更多',
            r'廣告.*?關閉',
            r'訂閱電子報.*?立即訂閱',
            r'分享到.*?Facebook',
            r'Copyright.*?All rights reserved',
            r'版權所有.*?工研院',
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content.strip()
    
    def _clean_title(self, title):
        """Clean and normalize title"""
        if not title:
            return ""
        
        # Remove JavaScript warnings from title
        title = re.sub(r'『您的瀏覽器不支援JavaScript功能.*?』\s*', '', title)
        
        # Remove common title suffixes
        title = re.sub(r'\s*[-|]\s*(工研院|ITRI|新聞|News).*$', '', title)
        title = re.sub(r'\s+', ' ', title)
        
        return title.strip()
    
    def _is_footer_only_content(self, content):
        """Check if content contains only footer/navigation information"""
        if not content:
            return True
            
        content_lower = content.lower()
        
        # Footer indicators
        footer_indicators = [
            '法律聲明',
            '採購資訊', 
            '工研院圖書館',
            '專業連結',
            '常見問答',
            '聯絡我們',
            '© 工業技術研究院',
            '權利所有',
            '客服專線',
            '0800-45-8899',
            '新竹縣竹東鎮中興路四段195號'
        ]
        
        # Count footer indicators
        footer_count = sum(1 for indicator in footer_indicators if indicator.lower() in content_lower)
        
        # If more than 50% are footer indicators and content is relatively short
        if footer_count >= 4 and len(content) < 500:
            return True
            
        # Check for navigation-only content
        nav_indicators = [
            '網站導覽', '選單按鈕', '跳到主要內容', '搜尋', '輸入關鍵字',
            '熱門搜尋', 'facebook圖示', 'youtube圖示', 'IG圖示'
        ]
        
        nav_count = sum(1 for indicator in nav_indicators if indicator.lower() in content_lower)
        if nav_count >= 2 and len(content) < 300:
            return True
            
        return False


class DuplicationFilterPipeline:
    """Filter out duplicate items based on content hash"""
    
    def __init__(self):
        self.seen_hashes = set()
        self.duplicate_count = 0
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        content_hash = adapter.get('content_hash')
        
        if content_hash in self.seen_hashes:
            self.duplicate_count += 1
            spider.logger.info(f"Duplicate item filtered: {adapter.get('title', 'Unknown')[:50]}...")
            raise DropItem("Duplicate item")
        
        self.seen_hashes.add(content_hash)
        return item
    
    def close_spider(self, spider):
        spider.logger.info(f"Filtered {self.duplicate_count} duplicate items")


class ITRIContentEnhancementPipeline:
    """Enhance ITRI-specific content with additional metadata"""
    
    def __init__(self):
        # ITRI-specific keywords for categorization
        self.research_areas = {
            '資通訊': ['ICT', '資通訊', '通訊', '網路', '5G', '6G', '物聯網', 'IoT'],
            '電子': ['電子', '半導體', '晶片', 'IC', '電路', '感測器'],
            '機械': ['機械', '自動化', '機器人', '精密', '製造'],
            '材料': ['材料', '奈米', '複合材料', '金屬', '陶瓷', '高分子'],
            '化工': ['化工', '化學', '觸媒', '程序', '反應'],
            '生醫': ['生醫', '醫療', '生物技術', '藥物', '診斷', '治療'],
            '綠能': ['綠能', '太陽能', '風能', '儲能', '電池', '節能'],
            '光電': ['光電', '雷射', '顯示', 'LED', '光學', '影像'],
        }
        
        self.technology_types = {
            'AI': ['人工智慧', 'AI', '機器學習', '深度學習', '神經網路'],
            '大數據': ['大數據', '數據分析', '資料科學', 'Big Data'],
            '區塊鏈': ['區塊鏈', 'Blockchain', '分散式帳本'],
            '量子': ['量子', '量子計算', '量子通訊'],
            '自動化': ['自動化', '智慧製造', '工業4.0', 'Industry 4.0'],
        }
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Enhance with research area classification
        research_area = self._classify_research_area(adapter.get('content', ''))
        if research_area:
            adapter['research_area'] = research_area
        
        # Enhance with technology type classification
        tech_type = self._classify_technology_type(adapter.get('content', ''))
        if tech_type:
            adapter['technology_type'] = tech_type
        
        # Extract and enhance keywords
        enhanced_keywords = self._extract_enhanced_keywords(adapter.get('content', ''))
        if enhanced_keywords:
            existing_tags = adapter.get('tags', [])
            if isinstance(existing_tags, list):
                adapter['tags'] = list(set(existing_tags + enhanced_keywords))
            else:
                adapter['tags'] = enhanced_keywords
        
        # Calculate content quality score
        quality_score = self._calculate_quality_score(adapter)
        adapter['quality_score'] = quality_score
        
        return item
    
    def _classify_research_area(self, content):
        """Classify content into ITRI research areas"""
        content_lower = content.lower()
        
        for area, keywords in self.research_areas.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return area
        
        return None
    
    def _classify_technology_type(self, content):
        """Classify content by technology type"""
        content_lower = content.lower()
        
        for tech_type, keywords in self.technology_types.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return tech_type
        
        return None
    
    def _extract_enhanced_keywords(self, content):
        """Extract enhanced keywords using ITRI domain knowledge"""
        keywords = []
        content_lower = content.lower()
        
        # All possible keywords from research areas and technology types
        all_keywords = []
        for area_keywords in self.research_areas.values():
            all_keywords.extend(area_keywords)
        for tech_keywords in self.technology_types.values():
            all_keywords.extend(tech_keywords)
        
        # Additional ITRI-specific terms
        itri_terms = [
            '產業升級', '技術移轉', '創新育成', '人才培育',
            '國際合作', '專利', '智財', '標準制定',
            '驗證測試', '技術服務', '顧問諮詢'
        ]
        all_keywords.extend(itri_terms)
        
        for keyword in all_keywords:
            if keyword.lower() in content_lower:
                keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_quality_score(self, adapter):
        """Calculate content quality score based on multiple factors"""
        score = 0.5  # Base score
        
        content = adapter.get('content', '')
        title = adapter.get('title', '')
        
        # Length factor
        if len(content) > 200:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1
        
        # Title quality
        if len(title) > 10:
            score += 0.05
        
        # ITRI relevance
        itri_keywords = ['工研院', 'ITRI', '工業技術研究院']
        for keyword in itri_keywords:
            if keyword in (title + content):
                score += 0.1
                break
        
        # Technical content indicators
        tech_indicators = ['技術', '研究', '開發', '創新', '專利']
        tech_count = sum(1 for indicator in tech_indicators if indicator in content)
        score += min(0.1, tech_count * 0.02)
        
        # Structured content (has categories, tags, etc.)
        if adapter.get('category'):
            score += 0.05
        if adapter.get('tags') and len(adapter.get('tags', [])) > 0:
            score += 0.05
        
        return min(1.0, max(0.0, score))


class JsonExportPipeline:
    """Export items to JSON files organized by source and date with periodic saves"""
    
    def __init__(self, output_dir='crawled_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different sources
        self.source_dirs = {}
        self.items_by_source = {}
        
        # Statistics
        self.stats = {
            'total_items': 0,
            'items_by_source': {},
            'items_by_type': {},
        }
        
        # Memory management - periodic save settings
        self.save_interval = 30  # Save every 30 items
        self.last_save_count = 0
    
    def open_spider(self, spider):
        """Initialize when spider opens"""
        spider.logger.info(f"JsonExportPipeline: Output directory: {self.output_dir}")
        
        # Create timestamp for this crawl session
        self.crawl_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create session directory
        self.session_dir = self.output_dir / f"crawl_{self.crawl_timestamp}"
        self.session_dir.mkdir(exist_ok=True)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        source = adapter.get('source', 'unknown')
        
        # Initialize source tracking
        if source not in self.items_by_source:
            self.items_by_source[source] = []
            self.stats['items_by_source'][source] = 0
        
        # Convert item to dict
        item_dict = dict(adapter)
        
        # Add to source collection
        self.items_by_source[source].append(item_dict)
        
        # Update statistics
        self.stats['total_items'] += 1
        self.stats['items_by_source'][source] += 1
        
        content_type = adapter.get('content_type', 'unknown')
        self.stats['items_by_type'][content_type] = self.stats['items_by_type'].get(content_type, 0) + 1
        
        # Periodic save to prevent memory overflow
        if self.stats['total_items'] - self.last_save_count >= self.save_interval:
            self._periodic_save(spider)
            self.last_save_count = self.stats['total_items']
            
        # Print progress every 10 items for real-time feedback
        if self.stats['total_items'] % 10 == 0:
            print(f"⚡ 進度更新: {self.stats['total_items']} 項目已完成 | 下次批次保存: {self.save_interval - (self.stats['total_items'] - self.last_save_count)} 項目後")
        
        return item
    
    def close_spider(self, spider):
        """Save all collected items when spider closes"""
        
        # Save items by source
        for source, items in self.items_by_source.items():
            if items:
                source_file = self.session_dir / f"{source}_articles.json"
                with open(source_file, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                spider.logger.info(f"Saved {len(items)} items from {source} to {source_file}")
        
        # Save combined data
        all_items = []
        for items in self.items_by_source.values():
            all_items.extend(items)
        
        if all_items:
            combined_file = self.session_dir / "all_articles_combined.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)
            spider.logger.info(f"Saved {len(all_items)} total items to {combined_file}")
        
        # Save crawl statistics
        stats_file = self.session_dir / "crawl_statistics.json"
        crawl_stats = {
            'crawl_timestamp': self.crawl_timestamp,
            'spider_name': spider.name,
            'statistics': self.stats,
            'summary': {
                'total_articles': self.stats['total_items'],
                'sources_crawled': len(self.stats['items_by_source']),
                'content_types': list(self.stats['items_by_type'].keys()),
            }
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(crawl_stats, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"Crawl completed: {self.stats['total_items']} items from {len(self.stats['items_by_source'])} sources")
        spider.logger.info(f"Results saved to: {self.session_dir}")

    def _periodic_save(self, spider):
        """Periodically save data to prevent memory overflow"""
        spider.logger.info(f"🔄 Periodic save triggered at {self.stats['total_items']} items")
        
        # Print to terminal for real-time feedback
        print(f"\n📊 [BATCH SAVE] 已完成 {self.stats['total_items']} 個項目的爬取")
        print(f"💾 正在保存批次數據到: {self.session_dir}")
        
        # Save current data
        for source, items in self.items_by_source.items():
            if items:
                # Append to existing file or create new one
                source_file = self.session_dir / f"{source}_articles.json"
                
                existing_data = []
                if source_file.exists():
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        existing_data = []
                
                # Merge with existing data
                all_data = existing_data + items
                
                # Save merged data
                with open(source_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                
                spider.logger.info(f"💾 Saved {len(items)} new items to {source_file.name} (total: {len(all_data)})")
                print(f"✅ 已保存 {len(items)} 個新項目到 {source_file.name} (累計: {len(all_data)} 項)")
        
        # Save updated statistics
        stats_file = self.session_dir / "crawl_statistics.json"
        crawl_stats = {
            'crawl_timestamp': self.crawl_timestamp,
            'spider_name': spider.name,
            'statistics': self.stats,
            'summary': {
                'total_articles': self.stats['total_items'],
                'sources_crawled': len(self.stats['items_by_source']),
                'content_types': list(self.stats['items_by_type'].keys()),
            },
            'last_periodic_save': datetime.now().isoformat()
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(crawl_stats, f, ensure_ascii=False, indent=2)
        
        # Clear memory - keep only recent items
        for source in self.items_by_source:
            self.items_by_source[source] = []
        
        print(f"🧹 記憶體已清理，繼續爬取...\n")
        
        spider.logger.info(f"🧹 Memory cleared after periodic save")


class DateFilterPipeline:
    """Filter items based on publication date"""
    
    def __init__(self, min_date=None, max_date=None):
        """
        Initialize date filter
        
        Args:
            min_date (str): Minimum date in YYYY-MM-DD format (inclusive)
            max_date (str): Maximum date in YYYY-MM-DD format (inclusive)
        """
        self.min_date = min_date
        self.max_date = max_date
        
    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline from crawler settings"""
        return cls(
            min_date=crawler.settings.get('DATE_FILTER_MIN'),
            max_date=crawler.settings.get('DATE_FILTER_MAX')
        )
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Skip filtering if no date filters are set
        if not self.min_date and not self.max_date:
            return item
            
        published_date = adapter.get('published_date', '')
        
        # If no published date, use crawled_at date
        if not published_date:
            crawled_at = adapter.get('crawled_at', '')
            if crawled_at:
                # Extract date part from ISO datetime
                published_date = crawled_at.split('T')[0]
        
        # If still no date, let it pass (don't filter unknown dates)
        if not published_date:
            spider.logger.warning(f"No date found for item: {adapter.get('title', 'N/A')[:50]}...")
            return item
        
        # Parse and validate date
        try:
            from datetime import datetime
            item_date = datetime.strptime(published_date, '%Y-%m-%d')
            
            # Check minimum date
            if self.min_date:
                min_dt = datetime.strptime(self.min_date, '%Y-%m-%d')
                if item_date < min_dt:
                    spider.logger.info(f"Dropped (too old): {adapter.get('title', 'N/A')[:50]}... ({published_date})")
                    raise DropItem(f"Item date {published_date} is before minimum date {self.min_date}")
            
            # Check maximum date
            if self.max_date:
                max_dt = datetime.strptime(self.max_date, '%Y-%m-%d')
                if item_date > max_dt:
                    spider.logger.info(f"Dropped (too new): {adapter.get('title', 'N/A')[:50]}... ({published_date})")
                    raise DropItem(f"Item date {published_date} is after maximum date {self.max_date}")
            
            spider.logger.debug(f"Date filter passed: {adapter.get('title', 'N/A')[:50]}... ({published_date})")
            return item
            
        except ValueError as e:
            spider.logger.warning(f"Invalid date format '{published_date}' for item: {adapter.get('title', 'N/A')[:50]}...")
            return item  # Let items with invalid dates pass through


class ItriScrapyCrawlerPipeline:
    """Legacy pipeline - kept for compatibility"""
    def process_item(self, item, spider):
        return item
