# Python Imports
from collections import defaultdict
from pyculiarity import detect_ts, detect_vec
import numpy as np
import pandas as pd
import scipy.stats as stats

import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review
        Also used as terminal command: python manage.py anomaly (asin)
    Parameters:
        A valid product ASIN given as input in the command line
'''
class Command(BaseCommand):
    help = 'Get product review anomaly scores'

    # adds an argument to **kwards in the handle function
    def add_arguments(self, parser):
        parser.add_argument('asin', type=str, nargs='?', help='Indicates the asin of the product we are currently analyzing')
        parser.add_argument('-rating', '--rating', action='store_true', help='Calculate anomalies from ratings')
        parser.add_argument('-rall', '--rating_all', action='store_true', help='Calculate anomalies from ratings')
        parser.add_argument('-review', '--review', action='store_true', help='Calculate anomalies from reviews')
        parser.add_argument('-revall', '--review_all', action='store_true', help='Calculate anomalies from reviews')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        rating_anomaly = RatingAnomaly()
        review_anomaly = ReviewAnomaly()
        if kwargs['asin']:
            asin = kwargs['asin']
            if kwargs['rating']:
                print(rating_anomaly.detect(asin))
            elif kwargs['review']:
                print(review_anomaly.detect(asin)) 
        else:
            if kwargs['rating_all']:
                print(rating_anomaly.detect_all())
            elif kwargs['review_all']:
                print(review_anomaly.detect_all())   

        fig, (ax1) = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        rating_anomaly.plot(ax1)
        #plt.show()



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self, graph_info):
        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__(graph_info)  



    # returns reviews in bins of 30-day time df
    def detect_anomalies(self, product_ASIN):
        self.product_ASIN = product_ASIN
        self.set_info(Review.objects.filter(asin=self.product_ASIN))

        # Calculate an even number of bins based on range of unix_review_times x months
        self.df = self.generate_frame()
        if self.df.empty:
            return None
        #print(self.df)

        # convert timestamp to unix timestamp integer
        self.df['timestamp'] = self.df['timestamp'].view(np.int64) 
        self.fake_review_info['review_times'] = self.df['timestamp'].to_list()

        # calculate anomalies in rating value distribution
        detected_anomalies = defaultdict(dict)
        try:
            detected_anomalies = detect_ts(self.df, max_anoms=0.02, alpha=0.001, direction='both')
        except Exception as e:
            detected_anomalies['anoms']['anoms'] = []

        '''
        anomaly_ids = []
        for anomaly in detected_anomalies['anoms']['anoms']:
            for review_id, review_time, review_rating in zip(self.fake_review_info['review_ids'], self.fake_review_info['review_times'], self.fake_review_info['review_scores']):
                print(anomaly[0], int(anomaly[1]), review_id, review_time, review_rating)
                if review_time == anomaly[0] and review_rating == int(anomaly[1]):
                    anomaly_ids.append(review_id)
                    print("success")
        '''
        
        # format the unix timestamp integer back to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

        # return number of anomalies
        return len(detected_anomalies['anoms']['anoms'])



    # overloaded plot method, because we had to build the dataframes in detect in order to analyze the data (so no need to do it again)
    def plot(self, subplot):
        if self.empty_graph(subplot):
            return False

        if self.plot_frame(subplot, self.df):
            return True
        else:
            return False



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class RatingAnomaly(Anomaly):

    def __init__(self):
        # invoking the constructor of the parent class  
        super(RatingAnomaly, self).__init__({"method": "mean", "title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"})  
        self.rating_anomalies = 0

    def detect(self, product_ASIN):
        self.rating_anomalies = self.detect_anomalies(product_ASIN)
        if self.rating_anomalies:
            return self.calculate(self.rating_anomalies, Review.objects.filter(asin=self.product_ASIN).count())
        else:
            return False

    def detect_all(self):
        for product in Product.objects.values('asin'):
            self.detect(product['asin'])

    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        anomaly_rate = round(fake_reviews / total * 100, 3)
        Product.objects.filter(asin=self.product_ASIN).update(ratingAnomalyRate=anomaly_rate)
        return anomaly_rate




'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class ReviewAnomaly(Anomaly):

    def __init__(self):
        # invoking the constructor of the parent class  
        super(ReviewAnomaly, self).__init__({"method": "count", "title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"})  
        self.review_anomalies = 0

    def detect(self, product_ASIN):
        self.review_anomalies = self.detect_anomalies(product_ASIN)
        if self.review_anomalies:
            return self.calculate(self.review_anomalies, Review.objects.filter(asin=self.product_ASIN).count())
        else:
            return False

    def detect_all(self):
        for product in Product.objects.values('asin'):
            self.detect(product['asin'])

    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        anomaly_rate = round(fake_reviews / total * 100, 3)
        Product.objects.filter(asin=self.product_ASIN).update(reviewAnomalyRate=anomaly_rate)
        return anomaly_rate

    def train(self):
        self.product_ASIN = product_ASIN
        self.set_info(Review.objects.filter(asin=self.product_ASIN))

        # Calculate an even number of bins based on range of unix_review_times x months
        self.df = self.generate_frame()
        if self.df.empty:
            return None