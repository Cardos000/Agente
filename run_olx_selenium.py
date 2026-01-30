import scrapy
from scrapy.crawler import CrawlerProcess
from olx_selenium_spider import OlxSeleniumSpider

if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(OlxSeleniumSpider)
    process.start()
