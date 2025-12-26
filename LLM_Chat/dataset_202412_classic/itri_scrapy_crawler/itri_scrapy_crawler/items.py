# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ITRIArticleItem(scrapy.Item):
    """Item for ITRI article content"""
    id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    language = scrapy.Field()
    content_type = scrapy.Field()
    author = scrapy.Field()
    published_date = scrapy.Field()
    crawled_at = scrapy.Field()
    tags = scrapy.Field()
    category = scrapy.Field()
    summary = scrapy.Field()
    images = scrapy.Field()
    
    # Enhanced fields (added by pipelines)
    research_area = scrapy.Field()  # Research area classification
    technology_type = scrapy.Field()  # Technology type classification
    
    # Metadata fields (standardized across all items)
    domain = scrapy.Field()
    path = scrapy.Field()
    content_length = scrapy.Field()
    content_quality = scrapy.Field()
    content_hash = scrapy.Field()  # Composite hash for deduplication (content+url+title)
    pure_content_hash = scrapy.Field()  # Pure content hash for analysis
    quality_score = scrapy.Field()  # Calculated by enhancement pipeline


class ITRINewsItem(scrapy.Item):
    """Item for ITRI news and press releases"""
    id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    language = scrapy.Field()
    content_type = scrapy.Field()  # 修復缺少的欄位
    published_date = scrapy.Field()
    crawled_at = scrapy.Field()
    category = scrapy.Field()
    summary = scrapy.Field()
    tags = scrapy.Field()
    images = scrapy.Field()
    
    # News specific fields
    news_type = scrapy.Field()  # press_release, research_news, etc.
    department = scrapy.Field()
    contact_info = scrapy.Field()
    
    # Enhanced fields (added by pipelines)
    research_area = scrapy.Field()  # Research area classification
    technology_type = scrapy.Field()  # Technology type classification
    
    # Metadata fields (standardized across all items)
    author = scrapy.Field()
    domain = scrapy.Field()
    path = scrapy.Field()
    content_length = scrapy.Field()
    content_quality = scrapy.Field()
    content_hash = scrapy.Field()  # Composite hash for deduplication (content+url+title)
    pure_content_hash = scrapy.Field()  # Pure content hash for analysis
    quality_score = scrapy.Field()  # Calculated by enhancement pipeline


class ITRIResearchItem(scrapy.Item):
    """Item for ITRI research and technology information"""
    id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    language = scrapy.Field()
    content_type = scrapy.Field()  # 修復缺少的欄位
    crawled_at = scrapy.Field()
    category = scrapy.Field()
    summary = scrapy.Field()
    tags = scrapy.Field()
    images = scrapy.Field()
    published_date = scrapy.Field()
    
    # Research specific fields
    research_area = scrapy.Field()
    technology_type = scrapy.Field()
    applications = scrapy.Field()
    keywords = scrapy.Field()
    research_team = scrapy.Field()
    publications = scrapy.Field()
    patents = scrapy.Field()
    
    # Metadata fields (standardized across all items)
    author = scrapy.Field()
    domain = scrapy.Field()
    path = scrapy.Field()
    content_length = scrapy.Field()
    content_quality = scrapy.Field()
    content_hash = scrapy.Field()  # Composite hash for deduplication (content+url+title)
    pure_content_hash = scrapy.Field()  # Pure content hash for analysis
    quality_score = scrapy.Field()  # Calculated by enhancement pipeline


class ITRIServiceItem(scrapy.Item):
    """Item for ITRI services and industry collaboration"""
    id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    language = scrapy.Field()
    content_type = scrapy.Field()  # 修復缺少的欄位
    crawled_at = scrapy.Field()
    category = scrapy.Field()
    summary = scrapy.Field()
    tags = scrapy.Field()
    images = scrapy.Field()
    published_date = scrapy.Field()
    
    # Service specific fields
    service_type = scrapy.Field()
    target_industry = scrapy.Field()
    collaboration_type = scrapy.Field()
    contact_department = scrapy.Field()
    
    # Enhanced fields (added by pipelines)
    research_area = scrapy.Field()  # Research area classification
    technology_type = scrapy.Field()  # Technology type classification
    
    # Metadata fields (standardized across all items)
    author = scrapy.Field()
    domain = scrapy.Field()
    path = scrapy.Field()
    content_length = scrapy.Field()
    content_quality = scrapy.Field()
    content_hash = scrapy.Field()  # Composite hash for deduplication (content+url+title)
    pure_content_hash = scrapy.Field()  # Pure content hash for analysis
    quality_score = scrapy.Field()  # Calculated by enhancement pipeline