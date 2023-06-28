# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
from itemadapter import ItemAdapter
import sqlite3

from ccf_paper_crawl.spiders.ccf_paper_crawl import CCFPaperSpider
import threading

lock = threading.Lock()


class SQLitePipeline:
    def __init__(self) -> None:
        self.connect = sqlite3.connect('./tmp.sqlite')
        # self.connect.execute('DROP TABLE papers;')
        self.connect.execute('''
            CREATE TABLE IF NOT EXISTS papers(
                id          INTEGER PRIMARY KEY AUTOINCREMENT   NOT NULL,
                src         TEXT                                NOT NULL,
                src_abbr    TEXT                                NOT NULL,
                types       TEXT                                NOT NULL,
                level       TEXT                                NOT NULL,
                classes     TEXT                                NOT NULL,
                year        INT                                 NOT NULL,
                title       TEXT                                NOT NULL,
                url         TEXT                                NOT NULL
        );''')
        self.cursor = self.connect.cursor()

    def get_item_info(self, item):
        keys = ['src', 'src_abbr', 'types', 'level', 'classes', 'year', 'title', 'url']
        values = ['' for _ in range(len(keys))]
        values[0], values[5] = 0, 0
        for i in range(len(keys)):
            if item[keys[i]] is not None:
                values[i] = item[keys[i]]
        return tuple(values)

    def process_item(self, item, spider):
        src, src_abbr, types, level, classes, year, title, url = self.get_item_info(item)
        self.cursor.execute(
            "INSERT OR IGNORE INTO papers (src, src_abbr, types, level, classes, year, title, url) values(?, ?, ?, ?, ?, ?, ?, ?);",
            self.get_item_info(item)
        )
        self.connect.commit()

        src, src_abbr, types, level, classes, _, _, url = self.get_item_info(item)
        terminal_width = os.get_terminal_size().columns
        CCFPaperSpider.lock2.acquire()
        task = [src, src_abbr, types, level, classes]
        if task in CCFPaperSpider.ccf_task:
            CCFPaperSpider.ccf_task.remove(task)
        print(' ' * (terminal_width - 1) + '\r' + ('>>> [ {:>3d}/{:>3d} | {:>2d}% | {:>8d}] '.format(CCFPaperSpider.ccf_total - len(CCFPaperSpider.ccf_task), CCFPaperSpider.ccf_total, (CCFPaperSpider.ccf_total - len(CCFPaperSpider.ccf_task)) * 100 // CCFPaperSpider.ccf_total, CCFPaperSpider.paper_count) + ' [' + types[0] + '] <' + level + '> (' + src_abbr + ') ' + src)[:terminal_width - 1], end='\r')
        CCFPaperSpider.lock2.release()

        return item

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        self.connect.close()
