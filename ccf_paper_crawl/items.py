# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PaperInfo(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    src = scrapy.Field()
    src_abbr = scrapy.Field()
    types = scrapy.Field()
    level = scrapy.Field()
    classes = scrapy.Field()
    year = scrapy.Field()
    title = scrapy.Field()
    # author = scrapy.Field()
    # abstract = scrapy.Field()
    url=scrapy.Field()

class SrcInfo(scrapy.Item):
    src = scrapy.Field()
    src_abbr = scrapy.Field()
    classes = scrapy.Field()
    url = scrapy.Field()

