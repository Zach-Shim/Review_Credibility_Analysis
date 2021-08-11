# Python Imports 
import ast
from amazoncaptcha import AmazonCaptcha
from datetime import datetime
import pandas as pd
from random import choice
import requests
import time

# scraping imports
from bs4 import BeautifulSoup
from lxml import etree
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

# proxy handlers
from urllib.request import ProxyHandler, build_opener, install_opener, Request, urlopen
from stem import Signal
from stem.control import Controller

# selenium libraries
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selectorlib import Extractor
import requests
import time
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller


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

        # data
        self.asin = ""
        self.dataframes = dict()
        self.error_msg = ""

        # parsing
        self.tree = None
        self.url = ""
        
        # retry proxy
        self.sleep_time = 5
        self.max_tries = 5

        # request tuning
        self.ip_rotator = 5
        self.max_pages = 20

        # request params
        self.proxy = ""
        self.headers['user-agent'] = ua.random



    def scrape(self, asin):
        print("Start " + str(datetime.now()))

        # initialize variables
        self.asin = asin
        self.url = "https://www.amazon.com/dp/" + self.asin
        self.proxy = self.proxy_generator()

        # preliminary checks
        if not self.proxy:
            return False         
        if Product.objects.filter(asin=asin).exists():
            return True
        
        # scrape and push data
        product_success = self.scrape_product_data()
        review_success = self.scrape_review_data()
        print("End " + str(datetime.now()))

        if product_success and review_success:
            return self.push_data(self.dataframes)
        else:
            return False





    def scrape_product_data(self):
        # request page
        if self.request_wrapper(self.url) is not True:
            return False

        # get product title
        try:
            product_title = self.tree.xpath("//*[@id='productTitle']/text()")[0]
            product_title = (str(product_title).split(',')[0]).strip()
            print(product_title)
        except Exception as e:
            print(e)
            self.error_msg = "Error scraping product title"
            return False

        # get categories 
        try:
            category = self.tree.xpath("//*[@id='wayfinding-breadcrumbs_feature_div']/ul/li[1]/span/a/text()")[0]
            category = str(category).strip()
            print(category)
        except Exception as e:
            print(e)
            self.error_msg = "Error scraping review ratings"
            return False

        # build product dataframe from scraped data
        product_df = pd.DataFrame([[self.asin, product_title, category, self.url]], columns=['asin', 'title', 'category', 'url'])
        self.dataframes['product'] = product_df

        # move to first review page
        element = CSSSelector("a.a-link-emphasis.a-text-bold")(self.tree)
        extension = element[0].attrib['href']
        self.url = "https://www.amazon.com" + str(extension)
        print(self.url)
        
        time.sleep(1)
        return True



    def scrape_review_data(self):
        pages = 0
        next_page = True

        unix_review_times = []
        review_ratings = []
        review_texts = []
        reviewer_names = []
        
        while next_page and pages < self.max_pages:
            # request page
            if self.request_wrapper(self.url) is not True:
                return False

            times = self.tree.xpath("//div[@class='a-section celwidget']//span[contains(@class,'review-date')]/text()")
            ratings = self.tree.xpath("//div[@class='a-section celwidget']//div[2][contains(@class,'a-row')]//i[contains(@class,'a-icon-star')]//span//text()")
            texts = self.tree.xpath("string(//span[contains(@class,'review-text')])")
            names = self.tree.xpath("//div[@class='a-section celwidget']//div[1]//div[contains(@class,'a-profile-content')]//span[@class='a-profile-name']/text()")

            for date, rating, review, reviewer in zip(times, ratings, texts, names):
                # get unix review times
                date = date.replace(',', '').split(' ')[-3:]
                date = int(time.mktime(datetime.strptime('/'.join(date), '%B/%d/%Y').timetuple()))
                unix_review_times.append(date)

                # get ratings
                review_ratings.append(str(rating)[0])

                # get reviews
                review_texts.append(review.replace("\n", "").strip())

                # get reviewer names
                reviewer_names.append(reviewer)

            # determine if you have hit the last page of reviews
            time.sleep(1)
            try:
                extension = self.tree.xpath("//div[@class='a-form-actions a-spacing-top-extra-large']//span//div//ul//li[2]//a")
                if not extension:
                    next_page = False
                    continue
                extension = extension[0].attrib['href']
                self.url = "https://www.amazon.com" + str(extension)
                print(self.url)
                pages += 1
            except Exception as e:
                print(e)
                self.error_msg = "Error finding link to next review page"
                return False


        # build review dataframe from scraped data
        review_df = pd.DataFrame({
            'asin': [self.asin for x in range(0, len(review_ratings))],
            'reviewerID': ([0] * len(review_ratings)),
            'overall': review_ratings,
            'reviewText': review_texts,
            'unixReviewTime': unix_review_times,
        })

        # build user dataframe from scraped data
        user_df = pd.DataFrame({
            'reviewerName': reviewer_names
        })

        self.dataframes["review"] = review_df
        self.dataframes["user"] = user_df
        return True



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
            self.error_msg = "Error pushing user info to database"
            return False

        # push product
        try:
            ftd.set_table_name('product')
            ftd.set_entry_name(product_df['category'][0])
            product_fixed_df = ftd._serialize_to_product(product_df)
            ftd.df_to_database('product', product_fixed_df)
        except Exception as e:
            print(e)
            self.error_msg = "Error pushing product info to database"
            return False

        # push review
        try:
            ftd.set_table_name('review')
            review_fixed_df = ftd._serialize_to_review(review_df)
            ftd.df_to_database('review', review_fixed_df)
        except Exception as e:
            print(e)
            self.error_msg = "Error pushing review to database"
            return False

        print("End\n" + str(datetime.now()))
        return True



    # wrapper around request package to make it resilient
    def request_wrapper(self, url):
        while True:
            # request page
            try:
                # amazon blocks requests that does not come from browser, therefore need to mention user-agent
                time.sleep(1)
                response = requests.get(url=url, headers=self.headers, proxies={'http': 'http://127.0.0.1:8118'})
            except Exception as e:
                print(e)
                self.error_msg = "Invalid URL"
                return False
            
            # checking the response code
            if (response.status_code != 200):
                self.error_msg = "Invalid URL"
                return False

            # checking whether capcha is bypassed or not (status code is 200 in case it displays the capcha image)
            if "api-services-support@amazon.com" in response.text or "To discuss automated access to Amazon data please contact api-services-support@amazon.com." in response.text:
                if self.max_tries == 0:
                    self.error_msg = "Unable to bypass CAPTCHA. Please refresh page and try again."
                    return False
                else:
                    print("Attempting to bypass CAPTCHA")
                    self.ua = ua.random
                    self.proxy = self.proxy_generator() 
                    time.sleep(self.sleep_time)
                    self.max_tries -= 1
                    continue
            else:
                break
                    
        # request was actually succuessful (wow)
        self.max_try = 5
        self.tree = lxml.html.fromstring(response.content)
        time.sleep(1)
        return True


    # attempt to solve amazon captcha
    def check_captcha(self):
        if "api-services-support@amazon.com" in self.driver.page_source:
            captcha_image_url = self.driver.find_element_by_xpath("//img[contains(@src, 'captcha')]")
            print(captcha_image_url)
            captcha = AmazonCaptcha.fromlink(captcha_image_url.get_attribute('src'))
            captcha_image_url.send_keys(captcha.solve())

            submit_button = self.driver.find_element_by_xpath("//button[contains(@type, 'submit')]")
            self.driver.click(submit_button)
            
            if "api-services-support@amazon.com" in self.driver.page_source:
                return False
        return True



    def proxy_generator(self):
        tor_handler = TorHandler()
        
        ip = tor_handler.open_url('http://icanhazip.com/')
        print('My first IP: {}'.format(ip))
        
        # Cycle through the specified number of IP addresses via TOR
        old_ip = ip
        cycles = 0
        tor_handler.renew_connection()
    
        # Loop until the 'new' IP address is different than the 'old' IP address; It may take the TOR network some time to effect a different IP address
        while ip == old_ip and cycles < 30:
            cycles += 1
            print('{} cycles elapsed awaiting a different IP address.'.format(cycles))
            ip = tor_handler.open_url('http://icanhazip.com/')

        # if system is unable to find new ip, try the same one again, else return new ip from tor proxy
        if cycles > 30:
            return self.proxy
        else:
            print('My new IP: {}'.format(ip))
            ip = ip[:-2]
            return "http://" + ip + ":8118"
            


    def get_error(self):
        return self.error_msg



class TorHandler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}

    def open_url(self, url):
        # communicate with TOR via a local proxy (privoxy)
        def _set_url_proxy():
            proxy_support = ProxyHandler({'http': '127.0.0.1:8118'})
            opener = build_opener(proxy_support)
            install_opener(opener)

        _set_url_proxy()
        request = Request(url, None, self.headers)
        return urlopen(request).read().decode('utf-8')

    @staticmethod
    def renew_connection():
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='my_password')
            controller.signal(Signal.NEWNYM)
            controller.close()
