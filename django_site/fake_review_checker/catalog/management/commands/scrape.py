# Python Imports 
'''
from bs4 import BeautifulSoup
from collections import OrderedDict 
from datetime import datetime
import json
import lxml
from lxml import html
import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selectorlib import Extractor
import time
from webdriver_manager.chrome import ChromeDriverManager

from lxml import etree
import requests
import lxml.html
from lxml.cssselect import CSSSelector
'''
# Importing packages
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import math
from tqdm.auto import tqdm
from random import choice
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lxml import etree
import requests
import lxml.html
from lxml.cssselect import CSSSelector

# to ignore SSL certificate errors
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# random user-agent
from fake_useragent import UserAgent
ua = UserAgent()

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
        scraper = Scrape()
        print(scraper.scrape(asin))

        

class Scrape():
    def __init__(self):
        self.headers = {
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.amazon.com/',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

        self.max_pages = 40
        self.asin = ""
        self.dataframes = dict()

        # url
        self.sleep_time = 5
        self.proxies = self.proxy_generator()        
        self.max_tries = 10
        self.headers['user-agent'] = ua.random
        self.proxy = choice(self.proxies)


    def scrape(self, asin):
        print("Start\n" + str(datetime.now()))

        self.asin = asin
        if Product.objects.filter(asin=asin).exists():
            return True
        else:
            success = self.scrape_data()
            if success:
                return self.push_data(self.dataframes)
            else:
                return False
    


    def push_data(self, dataframes):
        ftd = FileToDatabase()
        
        user_df = self.dataframes['user']
        product_df = self.dataframes['product']
        review_df = self.dataframes['review']

        # push user
        try:
            ftd.set_table_name('user')
            user_df['reviewerID'] = ftd._add_user_id(user_df)
            user_fixed_df = ftd._serialize_to_user(user_df)
            ftd.df_to_database('user', user_fixed_df)
        except Exception as e:
            print(e)
            print("Error pushing user info to database")
            return False

        # push product
        try:
            ftd.set_table_name('product')
            ftd.set_entry_name(product_df['category'][0])
            product_fixed_df = ftd._serialize_to_product(product_df)
            ftd.df_to_database('product', product_fixed_df)
        except Exception as e:
            print(e)
            print("Error pushing product info to database")
            return False

        # push review
        try:
            ftd.set_table_name('review')
            review_fixed_df = ftd._serialize_to_review(review_df)
            ftd.df_to_database('review', review_fixed_df)
        except Exception as e:
            print(e)
            print("Error pushing review to database")
            return False

        print("End\n" + str(datetime.now()))
        return True



    def scrape_data(self):
        url = "https://www.amazon.com/dp/" + self.asin

        # request page
        tree = None
        try:
            tree = self.request_wrapper(url)
        except Exception as e:
            print(e)
            print("Invalid URL")
            return False


        # get product title
        try:
            product_title = tree.xpath("//*[@id='productTitle']/text()")[0]
            product_title = (str(product_title).split(',')[0]).strip()
            print(product_title)
        except Exception as e:
            print(e)
            print("Error scraping product title")
            return False

        # get categories 
        try:
            category = tree.xpath("//*[@id='wayfinding-breadcrumbs_feature_div']/ul/li[1]/span/a/text()")[0]
            category = str(category).strip()
            print(category)
        except Exception as e:
            print(e)
            print("Error scraping review ratings")
            return False

        # build product dataframe from scraped data
        product_df = pd.DataFrame([[self.asin, product_title, category]], columns=['asin', 'title', 'category'])
        self.dataframes['product'] = product_df



        # move to first review page
        element = CSSSelector("a.a-link-emphasis.a-text-bold")(tree)
        extension = element[0].attrib['href']
        url = "https://www.amazon.com" + str(extension)
        print(url)



        pages = 0
        next_page = True

        unix_review_times = []
        review_ratings = []
        review_texts = []
        reviewer_names = []

        while next_page and pages < self.max_pages:
            # refresh page
            tree = None
            try:
                tree = self.request_wrapper(url)
            except Exception as e:
                print(e)
                print("Invalid URL")
                return False


            # get unix review times
            try:
                for date in tree.xpath("//div[@class='a-section celwidget']//span[contains(@class,'review-date')]/text()"):
                    date = str(date).split(' ')[-3:]
                    date[1] = date[1][0:len(date[1])-1]
                    date = '/'.join(date)
                    date = int(time.mktime(datetime.strptime(date, '%B/%d/%Y').timetuple()))
                    unix_review_times.append(date)
            except Exception as e:
                print(e)
                print("Error scraping review times")
                return False

            # get review ratings
            try:
                for rating in tree.xpath("//div[@class='a-section celwidget']//div[2][contains(@class,'a-row')]//i[contains(@class,'a-icon-star')]"):
                    rating = str(rating)[0]
                    review_ratings.append(rating)
            except Exception as e:
                print(e)
                print("Error scraping review ratings")
                return False
            
            # get review texts
            try:
                for review in tree.xpath("//span[contains(@class,'review-text')]"):
                    text = ""
                    for child in list(review.iter()):
                        for element in child:
                            child_text = str(element.text_content()).strip()
                            child_text.replace("\n", "")
                            if "Read more" in child_text:
                                break
                            else:
                                text += child_text
                    review_texts.append(text)
            except Exception as e:
                print(e)
                print("Error scraping review texts")
                return False

            # get reviewer names
            try:
                for reviewer in tree.xpath("//div[@class='a-section celwidget']//div[1]//div[contains(@class,'a-profile-content')]//span[@class='a-profile-name']/text()"):
                    reviewer_names.append(reviewer)
            except Exception as e:
                print(e)
                print("Error scraping reviewer names")
                return False

            # determine if you have hit the last page of reviews
            try:
                extension = tree.xpath("//div[@class='a-form-actions a-spacing-top-extra-large']//span//div//ul//li[2]//a")
                if not extension:
                    next_page = False
                    continue
                extension = extension[0].attrib['href']
                url = "https://www.amazon.com" + str(extension)
                print(url)
                pages += 1
            except Exception as e:
                print(e)
                print("Error finding link to next review page")
                return False

        print("unix review times ", len(unix_review_times))
        print("review ratings ", len(review_ratings))
        print("review texts ", len(review_texts))
        print("reviewer names ", len(reviewer_names))
        print(reviewer_names[-1])

        '''
            Build dataframes
        '''
        # build review dataframe from scraped data
        asin_list = [self.asin for x in range(0, len(review_ratings))]
        reviewerID_list = [r_id for r_id in range(0, len(review_ratings))]
        review_df = pd.DataFrame({
            'asin': asin_list,
            'reviewerID': reviewerID_list,
            'overall': review_ratings,
            'reviewText': review_texts,
            'unixReviewTime': unix_review_times
        })

        # build user dataframe from scraped data
        user_df = pd.DataFrame({
            'reviewerName': reviewer_names
        })

        self.dataframes["review"] = review_df
        self.dataframes["user"] = user_df
        return True



    # wrapper around request package to make it resilient
    def request_wrapper(self, url):
        while True:
            while True:
                # amazon blocks requests that does not come from browser, therefore need to mention user-agent
                response = requests.get(url, headers=self.headers, proxies=self.proxy)

                # checking the response code
                if (response.status_code != 200):
                    raise Exception(response.raise_for_status())
                
                # checking whether capcha is bypassed or not (status code is 200 in case it displays the capcha image)
                if "api-services-support@amazon.com" in response.text:
                    if self.max_tries == 0:
                        print("Unable to bypass CAPTCHA")
                        return False
                    else:
                        print("Attempting to bypass CAPTCHA")
                        time.sleep(self.sleep_time)
                        self.max_tries -= 1
                        self.ua = ua.random
                        self.proxy = choice(self.proxies)
                        continue
                        
                self.max_try = 5
                return lxml.html.fromstring(response.content)



    # random proxy generator
    def proxy_generator(self):
        proxies = []
        try:
            response = requests.get("https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&speed=fast&protocols=https&anonymityLevel=elite")
            soup = BeautifulSoup(response.text, 'html.parser')
            proxies_table = str(soup).split(',')
            #matches = re.findall('ip', proxies_tables)
            ips = [x for x in proxies_table if re.search('ip', x)]
            ports = [x for x in proxies_table if re.search('port', x)]
            for ip, port in zip(ips, ports):
                proxies.append({
                    'ip': ip[6:-1],
                    'port': port[8:-1]
                })

            proxies_list = [{'http':'http://'+proxy['ip']+':'+proxy['port']} for proxy in proxies]
            return proxies_list
        except Exception as e:
            print(e)
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            raise ValueError("Unable to process proxies")
