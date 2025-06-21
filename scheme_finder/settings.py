BOT_NAME = "scheme_finder"

SPIDER_MODULES = ["scheme_finder.spiders"]
NEWSPIDER_MODULE = "scheme_finder.spiders"

ROBOTSTXT_OBEY = False

ITEM_PIPELINES = {
    "scheme_finder.pipelines.SchemeFinderPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"
