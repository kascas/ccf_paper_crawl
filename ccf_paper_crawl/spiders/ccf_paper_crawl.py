import scrapy
from ccf_paper_crawl.items import PaperInfo
import threading
import re


class CCFPaperSpider(scrapy.Spider):
    name = "ccf_paper_crawl"
    allowed_domains = ['dblp.uni-trier.de', 'dblp.org']
    ccf_total, ccf_task, ccf_url_dict = 0, list(), dict()
    ccf_ignore = []
    spider_state = False
    paper_count = 0
    lock1, lock2 = threading.Lock(), threading.Lock()

    def start_requests(self):
        while len(CCFPaperSpider.ccf_task) > 0:
            for t in CCFPaperSpider.ccf_task:
                url = CCFPaperSpider.ccf_url_dict[t[0] + t[-1]]
                if re.match('http(s)?://dblp.*', url) is None:
                    CCFPaperSpider.ccf_task.remove(t)
                    CCFPaperSpider.ccf_ignore.append(t)
                    print("IGNORE: {} ({})".format(t[0], t[1]))
                    continue
                if t[2] == 'Journal':
                    yield scrapy.Request(url=url, callback=self.parse_j, meta={'info': t}, dont_filter=True)
                elif t[2] == 'Conference':
                    yield scrapy.Request(url=url, callback=self.parse_c, meta={'info': t}, dont_filter=True)
        CCFPaperSpider.spider_state = True

    def parse_c(self, response):
        entries = response.xpath("//ul[@class='publ-list']//nav[@class='publ']")
        for entry in entries:
            home_url = entry.xpath(".//li[1]/div[@class='head']/a/@href").extract_first()
            if home_url is None:
                continue
            yield scrapy.Request(home_url, callback=self.parse_item, meta=response.meta)

    def parse_j(self, response):
        entries = response.xpath("//div[@id='main']/ul//li")
        for entry in entries:
            home_url = entry.xpath("./a/@href").extract_first()
            if home_url is None:
                continue
            yield scrapy.Request(home_url, callback=self.parse_item, meta=response.meta)

    def parse_item(self, response):
        entries = response.xpath("//div[@id='main']/ul/li[@class!='no-pub']")
        src, src_abbr, types, level, classes = response.meta['info']
        for entry in entries:
            item = PaperInfo()
            item['src'], item['src_abbr'], item['types'], item['level'], item['classes'] = src, src_abbr, types, level, classes
            date = entry.xpath(".//meta[@itemprop='datePublished']/@content").extract_first()
            if date != None:
                item['year'] = int(date.strip().replace('\n', ' '))
            else:
                item['year'] = -1
            title = entry.xpath(".//span[@class='title']//text()").extract_first()
            if title != None:
                item['title'] = title.strip().replace('\n', ' ')
            else:
                item['title'] = ''
            url = entry.xpath(".//nav[@class='publ']//li[1]/div[@class='head']/a[1]/@href").extract_first()
            if url != None:
                item['url'] = url.strip()
            else:
                item['url'] = ''
            CCFPaperSpider.lock1.acquire()
            CCFPaperSpider.paper_count += 1
            CCFPaperSpider.lock1.release()
            yield item
