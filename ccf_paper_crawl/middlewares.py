# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import csv
import json
import os
import shutil
from scrapy import signals
import pandas as pd
import scrapy

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from ccf_paper_crawl.spiders.ccf_paper_crawl import CCFPaperSpider


class RestoreSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
        if os.path.exists('./restore/variables.json'):
            with open('./restore/variables.json', 'r')as f:
                variables = json.load(f)
                CCFPaperSpider.ccf_total, CCFPaperSpider.ccf_task, CCFPaperSpider.ccf_url_dict, CCFPaperSpider.ccf_ignore, CCFPaperSpider.paper_count, CCFPaperSpider.spider_state = variables['ccf_total'], variables['ccf_task'], variables['ccf_url_dict'], variables['ccf_ignore'], variables['paper_count'], variables['spider_state']
        else:
            with open('./source/conference.csv', 'r', encoding='utf-8')as fc, open('./source/journal.csv', 'r', encoding='utf-8')as fj:
                c_reader, j_reader = csv.reader(fc, delimiter='\t'), csv.reader(fj, delimiter='\t')
                for c in c_reader:
                    if c == []:
                        continue
                    task = [c[2], c[1], c[3], c[4], c[0]]
                    CCFPaperSpider.ccf_task.append(task)
                    CCFPaperSpider.ccf_url_dict[c[2] + c[0]] = c[-1]
                for j in j_reader:
                    if j == []:
                        continue
                    task = [j[2], j[1], j[3], j[4], j[0]]
                    CCFPaperSpider.ccf_task.append(task)
                    CCFPaperSpider.ccf_url_dict[j[2] + j[0]] = j[-1]
                CCFPaperSpider.ccf_total = len(CCFPaperSpider.ccf_task)
            if os.path.exists('./output'):
                shutil.rmtree('./output')

    def spider_closed(self, spider):
        if CCFPaperSpider.spider_state:
            print('\n\n\n--------------------\n[ Total Papers: {} ]\n--------------------'.format(CCFPaperSpider.paper_count))
            if not os.path.exists('./output'):
                os.makedirs('./output')
            shutil.copy('tmp.sqlite', './output/database.sqlite')
            os.remove('tmp.sqlite')
            pd.DataFrame(CCFPaperSpider.ccf_ignore).to_csv('./output/ignore.csv', sep='\t', header=None, index=False)
            shutil.rmtree('./restore')
        else:
            variables_dict = {
                'ccf_total': CCFPaperSpider.ccf_total,
                'ccf_task': CCFPaperSpider.ccf_task,
                'ccf_url_dict': CCFPaperSpider.ccf_url_dict,
                'ccf_ignore': CCFPaperSpider.ccf_ignore,
                'paper_count': CCFPaperSpider.paper_count,
                'spider_state': CCFPaperSpider.spider_state
            }
            with open('./restore/variables.json', 'w') as f:
                json.dump(variables_dict, f)
            # pd.DataFrame(CCFPaperSpider.ccf_task).to_csv('./output/record.csv', sep='\t', header=None, index=False)
            print("\n=== Current progress is saved in './restore' ===")


"""
class CcfPaperCrawlDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
"""
