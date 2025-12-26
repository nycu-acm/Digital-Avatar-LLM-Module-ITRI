# Scrapy settings for itri_scrapy_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "itri_scrapy_crawler"

SPIDER_MODULES = ["itri_scrapy_crawler.spiders"]
NEWSPIDER_MODULE = "itri_scrapy_crawler.spiders"

ADDONS = {}

# User agent for ITRI research purposes
USER_AGENT = "ITRI-Research-Bot/1.0 (+https://www.itri.org.tw; research@itri.org.tw)"

# Obey robots.txt rules (can be overridden per spider)
ROBOTSTXT_OBEY = True

# Configure delays and concurrency for respectful crawling
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # 0.5 * to 1.5 * DOWNLOAD_DELAY
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Enable cookies for session management
COOKIES_ENABLED = True

# Request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    "itri_scrapy_crawler.middlewares.ItriScrapyCrawlerSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "itri_scrapy_crawler.middlewares.ItriScrapyCrawlerDownloaderMiddleware": 543,
    # Add retry middleware for better reliability
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    # Add redirect middleware
    "scrapy.downloadermiddlewares.redirect.RedirectMiddleware": 600,
}

# Configure item pipelines - ORDER MATTERS!
ITEM_PIPELINES = {
    # First: Validate and clean data
    "itri_scrapy_crawler.pipelines.DataValidationPipeline": 100,
    
    # Second: Filter duplicates
    "itri_scrapy_crawler.pipelines.DuplicationFilterPipeline": 200,
    
    # Third: Enhance with ITRI-specific metadata
    "itri_scrapy_crawler.pipelines.ITRIContentEnhancementPipeline": 300,
    
    # Fourth: Export to JSON files
    "itri_scrapy_crawler.pipelines.JsonExportPipeline": 400,
}

# Enable and configure the AutoThrottle extension for adaptive delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False  # Set to True for debugging throttling

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Redirect settings
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

# Download timeout
DOWNLOAD_TIMEOUT = 30

# Enable and configure HTTP caching for development/testing
HTTPCACHE_ENABLED = False  # Set to True for development
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [404, 500, 502, 503, 504]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "scrapy_crawler.log"
LOG_ENCODING = "utf-8"

# Memory usage monitoring - more aggressive for large crawls
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 1024   # 1GB limit (reduced for safety)
MEMUSAGE_WARNING_MB = 512  # 512MB warning
MEMUSAGE_CHECK_INTERVAL = 60  # Check every 60 seconds

# Stats collection
STATS_CLASS = "scrapy.statscollectors.MemoryStatsCollector"

# Telnet console (disabled for security)
TELNETCONSOLE_ENABLED = False

# Extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "scrapy.extensions.feedexport.FeedExporter": None,  # Disable problematic FeedExporter
    "scrapy.extensions.memusage.MemoryUsage": 500,
    "scrapy.extensions.logstats.LogStats": 500,
}

# Disable problematic FEEDS - use custom pipeline instead
# FEEDS = {
#     "output/%(name)s_%(time)s.json": {
#         "format": "json", 
#         "encoding": "utf8",
#         "store_empty": False,
#         "item_export_kwargs": {
#             "ensure_ascii": False,
#             "indent": 2,
#         },
#     },
# }

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# Custom settings for ITRI crawling
ITRI_CRAWLER_SETTINGS = {
    # Maximum pages per spider run
    "MAX_PAGES_PER_SPIDER": 100,
    
    # Content quality threshold
    "MIN_CONTENT_LENGTH": 50,
    
    # Language preferences
    "PREFERRED_LANGUAGES": ["zh-tw", "en"],
    
    # Output directory
    "OUTPUT_DIR": "crawled_data",
    
    # Enable content enhancement
    "ENHANCE_CONTENT": True,
}
