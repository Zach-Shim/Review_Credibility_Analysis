# Importing packages
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import time
import math
from tqdm.auto import tqdm
from random import choice
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


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


# random user-agent
from fake_useragent import UserAgent
ua = UserAgent()



class Command(BaseCommand):
    help = 'Scrape Amazon data'

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        scraper = Test(amazon_site="amazon.com", product_asin="B07X6V2FR3", sleep_time=5)
        print(scraper.scrape())

        

class Test():
    def __init__(self, amazon_site, product_asin, sleep_time=1):
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

        # url
        self.url = "https://www." + amazon_site + "/dp/" + product_asin
        self.sleep_time = sleep_time
        self.reviews_dict = {"date_info":[], "name":[], "title":[], "content":[], "rating":[]}
        self.proxies = self.proxy_generator()        
        self.max_try = 10
        self.headers['user-agent'] = ua.random
        self.proxy = choice(self.proxies)
        

 
    # MAIN FUNCTION
    def scrape(self):
        print ("Started!")

        self.page_scraper()
        time.sleep(self.sleep_time)

        print ("Completed!")

        # returning df
        return pd.DataFrame(self.reviews_dict)

    
    # page scrapper
    def helper(self, content, tag, parameter_key, parameter_value):
        attribute_lst = []
        attributes = content.find_all(tag, {parameter_key: parameter_value})
        for attribute in attributes:
            attribute_lst.append(attribute.contents[0])
        return attribute_lst



    def page_scraper(self):
        try:
            response = self.request_wrapper(self.url)

            # parsing content
            soup = BeautifulSoup(response.text, 'html.parser', verify=False)
            ## reviews section
            reviews = soup.findAll("div", {"class":"a-section review aok-relative"})
            ## parsing reviews section
            reviews = BeautifulSoup('<br/>'.join([str(tag) for tag in reviews]), 'html.parser')

            ## 1. title
            titles = reviews.find_all("a", class_="review-title")
            title_lst = []
            for title in titles:
                title_lst.append(title.find_all("span")[0].contents[0])

            ## 2. name
            name_lst = self.helper(reviews, "span", "class", "a-profile-name")

            ## 3. rating
            ratings = reviews.find_all("i", {"data-hook":"review-star-rating"})
            rating_lst = []
            for rating in ratings:
                rating_lst.append(rating.find_all("span")[0].contents[0])

            ## 4. date
            date_lst = self.helper(reviews, "span", "data-hook", "review-date")   

            ## 5. content
            contents = reviews.find_all("span", {"data-hook":"review-body"})
            content_lst = []
            for content in contents:
                text_ = content.find_all("span")[0].get_text("\n").strip()
                text_ = ". ".join(text_.splitlines())
                text_ = re.sub(' +', ' ', text_)
                content_lst.append(text_)

            # adding to the main list
            self.reviews_dict['date_info'].extend(date_lst)
            self.reviews_dict['name'].extend(name_lst)
            self.reviews_dict['title'].extend(title_lst)
            self.reviews_dict['content'].extend(content_lst)
            self.reviews_dict['rating'].extend(rating_lst)

        except:
            print ("Not able to scrape page {} (CAPTCHA is not bypassed)".format(page), flush=True)
    
    
    # wrapper around request package to make it resilient
    def request_wrapper(self, url):
        
        while (True):
            # amazon blocks requests that does not come from browser, therefore need to mention user-agent
            response = requests.get(url, verify=False, headers=self.headers, proxies=self.proxy)

            # checking the response code
            if (response.status_code != 200):
                print("error, unable to fetch initial site")
                raise Exception(response.raise_for_status())
            
            # checking whether capcha is bypassed or not (status code is 200 in case it displays the capcha image)
            if "api-services-support@amazon.com" in response.text:
                
                if (self.max_try == 0):
                    raise Exception("CAPTCHA is not bypassed")
                else:
                    time.sleep(self.sleep_time)
                    self.max_try -= 1
                    self.headers['user-agent'] = ua.random
                    self.proxy = choice(self.proxies)
                    continue
                
            self.max_try = 5
            break
            
        return response
    


    # random proxy generator
    def proxy_generator(self):
        proxies = []
        try:
            response = requests.get("https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&filterUpTime=100&protocols=https")
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

    