import scrapy
from ccf_paper_crawl.items import PaperInfo
import csv
import threading
import re
import pandas as pd


class CCFPaperSpider(scrapy.Spider):
    name = "ccf_paper_crawl"
    allowed_domains = ['dblp.uni-trier.de', 'dblp.org']
    ccf_total, ccf_task, ccf_url_dict = 0, list(), dict()
    ccf_ignore=[]
    paper_count = 0
    lock1, lock2 = threading.Lock(), threading.Lock()

    def start_requests(self):
        with open('./source/conference.csv', 'r', encoding='utf-8')as fc, open('./source/journal.csv', 'r', encoding='utf-8')as fj:
            c_reader, j_reader = csv.reader(fc, delimiter='\t'), csv.reader(fj, delimiter='\t')
            for c in c_reader:
                task = [c[2], c[1], c[3], c[4], c[0]]
                CCFPaperSpider.ccf_task.append(task)
                CCFPaperSpider.ccf_url_dict[c[2] + c[0]] = c[-1]
            for j in j_reader:
                task = [j[2], j[1], j[3], j[4], j[0]]
                CCFPaperSpider.ccf_task.append(task)
                CCFPaperSpider.ccf_url_dict[j[2] + j[0]] = j[-1]

        CCFPaperSpider.ccf_total = len(CCFPaperSpider.ccf_task)
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
        print('\n\n\n--------------------\n[ Total Papers: {} ]\n--------------------'.format(CCFPaperSpider.paper_count))
        pd.DataFrame(CCFPaperSpider.ccf_ignore).to_csv('./output/ignore.csv', sep='\t', header=None, index=False)

    def record(self):
        pd.DataFrame(CCFPaperSpider.ccf_task).to_csv('./output/record.csv', sep='\t', header=None, index=False)

    def parse_c(self, response):
        entries = response.xpath("//ul[@class='publ-list']//nav[@class='publ']")
        for entry in entries:
            home_url = entry.xpath(".//li[1]/div[@class='head']/a/@href").extract_first()
            if home_url is None:
                continue
            self.record()
            yield scrapy.Request(home_url, callback=self.parse_item, meta=response.meta)

    def parse_j(self, response):
        entries = response.xpath("//div[@id='main']/ul//li")
        for entry in entries:
            home_url = entry.xpath("./a/@href").extract_first()
            if home_url is None:
                continue
            self.record()
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
