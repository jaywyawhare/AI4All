BOT_NAME = 'scheme_scraper'

SPIDER_MODULES = ['scheme_scraper.spiders']
NEWSPIDER_MODULE = 'scheme_scraper.spiders'

# Crawl responsibly by identifying yourself
USER_AGENT = 'Mozilla/5.0 (compatible; SchemeScraperBot/1.0)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performing at the same time
CONCURRENT_REQUESTS = 1

# Configure item pipelines
ITEM_PIPELINES = {}

FEED_EXPORT_ENCODING = 'utf-8'
