# Python Imports 
from amazoncaptcha import AmazonCaptcha
from datetime import datetime
import pandas as pd
import requests
import time
from random import randint
import math

# scraping imports
from lxml import etree
import lxml.html
from lxml.cssselect import CSSSelector

# proxy handlers
from urllib.request import ProxyHandler, build_opener, install_opener, Request, urlopen
from stem import Signal
from stem.control import Controller

# to ignore SSL certificate errors
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# random user-agent
from fake_useragent import UserAgent
ua = UserAgent()

# concurrent scraping
import concurrent.futures

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

    MAX_THREADS = 30
    REVIEWS_PER_PAGE = 10

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
        self.error_msg = ""
        self.asin = ""
        self.url = ""

        # parsing
        self.tree = None
        self.links = []
        self.max_pages = 0

        # pushing to database
        self.product_info = dict()
        self.unix_review_times = []
        self.review_ratings = []
        self.review_texts = []
        self.reviewer_names = []

        # request params
        self.proxy = ""
        self.headers['user-agent'] = ua.random
        self.max_tries = 3



    def scrape(self, asin):
        print("Start " + str(datetime.now()))

        # no need to scrape if its already in the database
        if Product.objects.filter(asin=asin).exists():
            return True
        
        # initialize variables
        self.asin = asin
        self.url = "https://www.amazon.com/dp/" + self.asin
        self.proxy = self.proxy_generator()

        # preliminary checks
        if not self.proxy:
            return False         

        # scrape and push data
        if not self.scrape_product_data():
            self.error_msg = "Unable to retrieve product data"
            print(self.error_msg)
            return False

        if not self.scrape_link_data():
            self.error_msg = "Unable to retrieve Amazon links"
            print(self.error_msg)
            return False

        threads = min(Scrape.MAX_THREADS, len(self.links))
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.scrape_review_data, self.links)
        
        print("End " + str(datetime.now()))
        
        if self.error_msg != "" or not self.unix_review_times or not self.review_ratings or not self.review_texts or not self.reviewer_names:
            self.error_msg = "Unable to retrieve review data"
            print(self.error_msg)
            return False
        else:
            return self.push_data()
            


    def scrape_product_data(self):
        time.sleep(1)
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
        self.product_info = { 'asin': self.asin, 'title': product_title, 'category': category, 'url': self.url }

        # move to first review page
        element = CSSSelector("a.a-link-emphasis.a-text-bold")(self.tree)
        extension = element[0].attrib['href']
        self.url = "https://www.amazon.com" + str(extension)

        # get the total number of reviews
        num_of_reviews = int((self.tree.xpath("//*[@id='acrCustomerReviewText']/text()")[0].split(' ')[0]).replace(',', ''))
        if num_of_reviews < 10:
            self.error_msg = "Not enough reviews to analyze"
            print(self.error_msg)
            return False

        # either scrape the first ten pages or the amount of pages according to the num of reviews
        self.max_pages = min(int(math.floor(num_of_reviews / Scrape.REVIEWS_PER_PAGE)), 9)
        self.max_tries += 20
        return True



    def scrape_link_data(self):
        pages = 0
        next_page = True

        try:
            extension = self.url.split('/')[3]
            self.links = [("https://www.amazon.com/" + extension + "/product-reviews/B001K4OPY2/ref=cm_cr_arp_d_paging_btm_" + str(page_num) + "?ie=UTF8&pageNumber=" + str(page_num) + "&reviewerType=all_reviews") for page_num in range(2, self.max_pages)]
            self.links.append("https://www.amazon.com/" + extension + "/product-reviews/B001K4OPY2/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews")
            
            print("First 20 review page links:")
            for link in self.links:
                print(link)
        except Exception as e:
            print(e)
            return False

        return True



    def scrape_review_data(self, url):
        # request page
        time.sleep(randint(1,20))
        if self.request_wrapper(url) is not True:
            self.error_msg = "Invalid URL"
            print(self.error_msg)
            return False

        texts = self.tree.xpath("//span[contains(@class,'review-text')]")
        times = self.tree.xpath("//div[@class='a-section celwidget']//span[contains(@class,'review-date')]/text()")
        ratings = self.tree.xpath("//div[@class='a-section celwidget']//div[2][contains(@class,'a-row')]//i[contains(@class,'a-icon-star')]//span//text()")
        names = self.tree.xpath("//div[@class='a-section celwidget']//div[1]//div[contains(@class,'a-profile-content')]//span[@class='a-profile-name']/text()")

        for date, rating, review, reviewer in zip(times, ratings, texts, names):
            # get reviews
            review = review.text_content()
            review = review.replace("\n", "").strip()
            if review in self.review_texts:
                continue
            else:
                self.review_texts.append(review.replace("\n", "").strip())
            
            # get unix review times
            date = date.replace(',', '').split(' ')[-3:]
            date = int(time.mktime(datetime.strptime('/'.join(date), '%B/%d/%Y').timetuple()))
            self.unix_review_times.append(date)

            # get ratings
            self.review_ratings.append(str(rating)[0])

            # get reviewer names
            self.reviewer_names.append(reviewer)

        return True



    def push_data(self):
        ftd = FileToDatabase()
        
        # create user dataframe
        product_df = pd.DataFrame([self.product_info], columns=self.product_info.keys())

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
 


        # build user dataframe from scraped data
        user_df = pd.DataFrame({
            'reviewerName': self.reviewer_names
        })

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



        # build review dataframe from scraped data
        review_df = pd.DataFrame({
            'asin': [self.asin for x in range(0, len(self.review_ratings))],
            'reviewerID': ([0] * len(self.review_ratings)),
            'overall': self.review_ratings,
            'reviewText': self.review_texts,
            'unixReviewTime': self.unix_review_times,
        })

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
                if self.max_tries <= 0:
                    self.error_msg = "Unable to bypass CAPTCHA. Please refresh page and try again."
                    return False
                else:
                    # random IP and user agent
                    print("Attempting to bypass CAPTCHA")
                    #time.sleep(randint(1,5))
                    self.headers['user-agent'] = ua.random
                    self.proxy = self.proxy_generator() 
                    self.max_tries -= 1
                    print("My new user agent: ", self.headers['user-agent'])
                    print("Tries left: ", self.max_tries)
                    continue
            else:
                break
                    
        # request was actually succuessful (wow)
        print("Successfully connected to ", url)
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
