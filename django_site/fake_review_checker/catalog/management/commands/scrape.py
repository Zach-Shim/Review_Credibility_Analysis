# Python Imports 
from bs4 import BeautifulSoup
from collections import OrderedDict 
from datetime import datetime
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selectorlib import Extractor
import requests
import time
from webdriver_manager.chrome import ChromeDriverManager

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms
from .file_to_database import FileToDatabase

# Global Directory Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__json_location__ = __current_dir__[:-20] + "/datasets/dynamic_data/"



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

        self.max_pages = 5
        self.asin = ""



    def scrape(self, asin):
        self.asin = asin
        url = "https://www.amazon.com/dp/" + asin
        if Product.objects.filter(url=url).exists():
            return False
        else:
            dataframes = self.get_data(url)
            self.push_data(dataframes)
            return True
    


    def push_data(self, dataframes):
        ftd = FileToDatabase()
        
        user_df = dataframes['user']
        product_df = dataframes['product']
        review_df = dataframes['review']

        # push user
        ftd.set_table_name('user')
        user_df['reviewerID'] = ftd._add_user_id(user_df)
        user_fixed_df = ftd._serialize_to_user(user_df)
        ftd.df_to_database('user', user_fixed_df)

        # push product
        print(product_df)
        ftd.set_table_name('product')
        ftd.set_entry_name(product_df['category'][0])
        product_fixed_df = ftd._serialize_to_product(product_df)
        ftd.df_to_database('user', product_fixed_df)

        # push review
        ftd.set_table_name('review')
        review_fixed_df = ftd._serialize_to_review(review_df)
        ftd.df_to_database('review', review_fixed_df)



    def get_data(self, url):
        op = webdriver.ChromeOptions()
        op.add_argument('headless')
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=op)
        driver.get(url)
        driver.refresh()

        '''
            Get Product Info
        '''
        # get product title
        product_title = driver.find_element_by_id("productTitle").text
        product_title = (product_title.split(',')[0]).strip()

        # get categories 
        category = driver.find_element_by_xpath("//div[@id='nav-subnav']//a[1]//span").text

        # move to next page
        driver.find_element_by_css_selector("a.a-link-emphasis.a-text-bold").click()

        '''
            Get Review and User Info
        '''
        pages = 0
        unix_review_times = []
        review_ratings = []
        review_texts = []
        reviewer_names = []
        while True and pages < self.max_pages:
            driver.refresh()
            # get unix review times
            for date in driver.find_elements_by_xpath("//div[@class='a-section celwidget']//span[contains(@class,'review-date')]"):
                date = (date.text).split(' ')[-3:]
                date[1] = date[1][0:len(date[1])-1]
                date = '/'.join(date)
                date = int(time.mktime(datetime.strptime(date, '%B/%d/%Y').timetuple()))
                unix_review_times.append(date)

            # get review ratings
            for rating in driver.find_elements_by_xpath("//div[@class='a-section celwidget']//div[2][@class='a-row']//a[1][@class='a-link-normal']//i[contains(@class,'a-icon-star')]"):
                rating_attributes = rating.get_attribute('class').split()
                rating = rating_attributes[2][-1]
                review_ratings.append(rating)

            # get review texts
            for review in driver.find_elements_by_xpath("//span[contains(@class,'review-text')]//span"):
                review_texts.append(review.text)

            # get reviewer names
            for reviewer in driver.find_elements_by_xpath("//div[@class='a-section celwidget']//div[1]//a//div[2]//span[@class='a-profile-name']"):
                reviewer_names.append(reviewer.text)

            # determine if you have hit the last page of reviews
            try:
                next_page = driver.find_element_by_xpath("//div[@class='a-form-actions a-spacing-top-extra-large']//span//div//ul//li[2]//a")
                next_page.click()
                pages += 1
            except:
                breakpoint()
                break

        driver.close()

        asin_list = [asin for asin in range(0, len(review_ratings))]
        reviewerID_list = [r_id for r_id in range(0, len(review_ratings))]
        review_df = pd.DataFrame({
            'asin': asin_list,
            'reviewerID': reviewerID_list,
            'overall': review_ratings,
            'reviewText': review_texts,
            'unixReviewTime': unix_review_times
        })

        user_df = pd.DataFrame({
            'reviewerName': reviewer_names
        })

        product_df = pd.DataFrame([[self.asin, product_title, category]], columns=['asin', 'title', 'category'])

        return {"review": review_df, "user": user_df, "product": product_df}

        '''
        # compress into single dictionary and push to json file
        outfile = open(__json_location__ + product_title.replace(" ", "") + '.json','w')
        print("names: ", len(reviewer_names))
        print("rating: ", len(review_ratings))
        print("texts: ", len(review_texts))
        print("times: ", len(unix_review_times))
        for name, rating, text, unix_time in zip(reviewer_names, review_ratings, review_texts, unix_review_times):
            review = {"reviewerName": name, "overall": rating, "reviewText": text, "unixReviewTime": unix_time}
            json.dump(review, outfile)
            outfile.write('\n')
        '''
        