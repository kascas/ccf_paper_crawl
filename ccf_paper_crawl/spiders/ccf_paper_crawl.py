import scrapy
from ccf_paper_crawl.items import PaperInfo
import csv
import os
import threading

mutex = threading.Lock()


class CCFPaperSpider(scrapy.Spider):
    name = "ccf_paper_crawl"
    total, finished = 0, set()
    paper_count = 0

    def start_requests(self):
        def get_ccf_content():
            ccf_conference, ccf_journal = [], []
            with open('./source/conference.csv', 'r', encoding='utf-8')as fc, open('./source/journal.csv', 'r', encoding='utf-8')as fj:
                c_reader, j_reader = csv.reader(fc, delimiter='\t'), csv.reader(fj, delimiter='\t')
                for c in c_reader:
                    ccf_conference.append([c[2], c[1], c[3], c[4], c[0], c[6]])
                for j in j_reader:
                    ccf_journal.append([j[2], j[1], j[3], j[4], j[0], j[6]])
            return ccf_conference, ccf_journal

        ccf_conference, ccf_journal = get_ccf_content()
        CCFPaperSpider.total = len(ccf_conference) + len(ccf_journal)
        for j in ccf_journal:
            yield scrapy.Request(url=j[-1], callback=self.parse_j, meta={'info': j[:-1]})
        CCFPaperSpider.paper_count = 0
        for c in ccf_conference:
            yield scrapy.Request(url=c[-1], callback=self.parse_c, meta={'info': c[:-1]})
        print('\n\n\n--------------------\n[ Total Papers: {} ]'.format(CCFPaperSpider.paper_count))

    def parse_c(self, response):
        entries = response.xpath("//ul[@class='publ-list']//nav[@class='publ']")
        for entry in entries:
            home_url = entry.xpath(".//li[1]/div[@class='head']/a/@href").extract_first()
            if home_url is None:
                return
            yield scrapy.Request(home_url, callback=self.parse_item, meta=response.meta)

    def parse_j(self, response):
        entries = response.xpath("//div[@id='main']/ul//li")
        for entry in entries:
            home_url = entry.xpath("./a/@href").extract_first()
            if home_url is None:
                return
            yield scrapy.Request(home_url, callback=self.parse_item, meta=response.meta)

    def parse_item(self, response):
        entries = response.xpath("//div[@id='main']/ul/li[@class!='no-pub']")
        src, src_abbr, types, level, classes = response.meta['info']
        key = src + classes
        terminal_width = os.get_terminal_size().columns
        mutex.acquire()
        CCFPaperSpider.finished.add(key)
        print(' ' * (terminal_width - 1) + '\r' + ('>>> [ {:>3d}/{:>3d} | {:>2d}% | {:>8d}] '.format(len(CCFPaperSpider.finished), CCFPaperSpider.total, len(CCFPaperSpider.finished) * 100 // CCFPaperSpider.total, CCFPaperSpider.paper_count) + ' <' + types[0] + '> ' + '( ' + src_abbr + ' ) ' + src)[:terminal_width - 1], end='\r')
        mutex.release()
        for entry in entries:
            item = PaperInfo()
            date = entry.xpath(".//meta[@itemprop='datePublished']/@content").extract_first()
            item['src'], item['src_abbr'], item['types'], item['level'], item['classes'] = src, src_abbr, types, level, classes
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
            mutex.acquire()
            CCFPaperSpider.paper_count += 1
            mutex.release()
            yield item
