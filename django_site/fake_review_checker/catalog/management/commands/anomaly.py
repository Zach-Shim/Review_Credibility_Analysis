# Python Imports
import datetime
import math
import pandas as pd
import webbrowser

import numpy as np
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import scipy.stats as stats

from pyculiarity import detect_ts, detect_vec
from collections import defaultdict

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.db.models import Max, Min, Avg

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
        parser.add_argument('product_ASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['product_ASIN']
        r_anomaly = Anomaly()
        r_anomaly.detect(asin)     
        series = []
        print(r_anomaly.detect(asin))

        '''
        fig, ax1, ax2 = plt.subplots(ncols=2, figsize=(11, 7))
        axes = (ax1, ax2)
        fig.subplots_adjust(wspace=0.4)

        r_anomaly.plot({"figure": fig, "axis": axes[0]}, asin)
        fig.show()

        r_anomaly.plot({"figure": fig, "axis": axes[1]}, asin)
        fig.show()
        '''

'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self):
        self.rating_value_anomalies = defaultdict(dict)
        self.review_count_anomalies = defaultdict(dict)

        # invoking the constructor of the parent class  
        #super(Incentivized, self).__init__()  


    # returns reviews in bins of 30-day time series
    def detect(self, product_ASIN):
        self.product_ASIN = product_ASIN
        self.get_bins(product_ASIN)
        self.fake_review_info = self.get_info(product_ASIN)   
        
        return self.detect_helper(product_ASIN)



    def detect_helper(self, product_ASIN):
        # Get unixReviewTimes and scores of all fake reviews
        unix_review_times = self.fake_review_info["review_times"]
        scores = self.fake_review_info["review_scores"]

        # error checking for empty graph
        if (len(unix_review_times) == 0 or len(scores) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return

        series = []
        series.append(self.plot_review_anomalies(product_ASIN))
        series.append(self.plot_rating_anomalies(product_ASIN))
        return series



    def plot(self, subplot, product_ASIN):
        # Get unix_review_times and scores of all fake reviews
        info = self.getInfo(product_ASIN)
        unix_review_times = info["review_times"]
        scores = info["review_scores"]

        # error checking for empty graph
        if (len(unix_review_times) == 0 or len(scores) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return

        series = []
        self.bins = self.get_bins(product_ASIN)
        self.fake_review_info = info
        series.append(self.plot_review_anomalies(subplot, product_ASIN))
        series.append(self.plot_rating_anomalies(subplot, product_ASIN))
        return series
        


    def plot_review_anomalies(self, product_ASIN, subplot = None):
        # Calculate an even number of bins based on range of unix_review_times x months        
        self.method = 'mean'
        self.graph_info = {"title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"}
        self.plot_axes(subplot)
        str(self.calculate(product_ASIN))



    def plot_rating_anomalies(self, product_ASIN, subplot = None):
        # Calculate an even number of bins based on range of unixReviewTimes x months 
        self.method = 'count'
        self.graph_info = {"title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"}
        self.plot_axes(subplot)
        return self.calculate(product_ASIN)



    def get_info(self, product_ASIN):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=product_ASIN)
        review_times_int = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        review_scores = [review['overall'] for review in reviews.values('overall').order_by('overall')]
        return {"review_times": review_times_int, "review_scores": review_scores}




    def calculate(self, product_ASIN):
        total_reviews = Review.objects.filter(asin=product_ASIN).count()

        if(self.method == 'mean'):
            # calculate anomalies in rating value distribution
            try:
                self.review_count_anomalies = detect_ts(self.graph_frame, max_anoms=0.02, direction='both')
            except:
                self.review_count_anomalies['anoms']['anoms'] = []
            
            review_anomalies = len(self.review_count_anomalies['anoms']['anoms'])
            review_anomaly_score = round(review_anomalies / total_reviews * 100, 2)
            Product.objects.filter(asin=product_ASIN).update(reviewAnomalyRate=review_anomaly_score)
            return review_anomaly_score

        if(self.method == 'count'):
            # calculate anomalies in review value distribution
            try:
                self.rating_value_anomalies = detect_ts(self.graph_frame, max_anoms=0.02, direction='both')
            except:
                self.rating_value_anomalies['anoms']['anoms'] = []
            
            rating_anomalies = len(self.rating_value_anomalies['anoms']['anoms'])
            rating_anomaly_score = round(rating_anomalies / total_reviews * 100, 2)
            Product.objects.filter(asin=product_ASIN).update(ratingAnomalyRate=rating_anomaly_score)
            return rating_anomaly_score



    def get_bins(self, product_ASIN):
        reviews = Review.objects.filter(asin=product_ASIN)
        self.bins = self.get_date_range(reviews)
        return

