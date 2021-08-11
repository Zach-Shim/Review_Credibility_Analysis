# Python Imports 
import scrapy
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from datetime import datetime
import pandas as pd

# scraping imports
from bs4 import BeautifulSoup
from lxml import etree
import lxml.html
from lxml.cssselect import CSSSelector
import requests

# to ignore SSL certificate errors
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#from ...scraping.scraping.spiders.product_spider import ProductSpider
#from ...scraping.scraping.spiders.link_spider import LinkSpider
#from ...scraping.scraping.spiders.review_spider import ReviewSpider

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms
from .file_to_database import FileToDatabase




class Command(BaseCommand):
    help = 'Scrape Amazon data'

    # adds an argument to **kwards in the handle function
    def add_arguments(self, parser):
        parser.add_argument('asin', type=str, help='Indicates the asin of the product we want to analyze')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['asin']
        scraper = ScrapeAmazon()
        scraper.scrape(asin)
        

class ScrapeAmazon():

    def scrape(self, asin):
        print("Start " + str(datetime.now()))

        # scrape and push data
        if Product.objects.filter(asin=asin).exists():
            return True
            
        url = "https://www.amazon.com/dp/" + asin
        try:
            runner = CrawlerRunner()
            runner.crawl(ProductSpider, url=url) 
            #runner.crawl(ReviewSpider, url=url)
            d = runner.join()
            d.addBoth(lambda _: reactor.stop())
            reactor.run(0)
        except Exception as e:
            print(e)
            print("End " + str(datetime.now()))
            print("error")



    # random proxy generator
    def proxy_generator(self):
        response = requests.get(url="https://spys.me/proxy.txt", headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        proxy_table = str(soup).split('\n')
        proxy_table = proxy_table[9:-3]
        
        proxies = []
        for proxy in proxy_table:
            start_index = proxy.find(':')
            end_index = proxy.find(' ')
            proxies.append("https://" + proxy[:start_index] + proxy[start_index+1:end_index])

        with open(os.getcwd() + "/catalog/scraping/scraping/proxy_list.txt", 'w') as f:
            for item in proxies:
                f.write("%s\n" % item)
        return proxies


