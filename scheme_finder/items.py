import scrapy


class SchemeFinderItem(scrapy.Item):
    slug = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    tags = scrapy.Field()
    state = scrapy.Field()
    category = scrapy.Field()
    description = scrapy.Field()
    age = scrapy.Field()
    benefits = scrapy.Field()
    exclusions = scrapy.Field()
    process = scrapy.Field()
    eligibility = scrapy.Field()
    documents_required = scrapy.Field()
