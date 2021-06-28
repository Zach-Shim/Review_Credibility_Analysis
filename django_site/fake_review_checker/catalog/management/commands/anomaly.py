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
        print(r_anomaly.detect(asin))

        fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)

        r_anomaly.plot([ax1, ax2], asin)



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self):

        self.series = dict()
        self.rating_value_anomalies = defaultdict(dict)
        self.review_count_anomalies = defaultdict(dict)

        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__()  



    # returns reviews in bins of 30-day time series
    def detect(self, product_ASIN):
        print("detect")
        self.set_bins(product_ASIN)
        self.set_info(product_ASIN)
        return self.detect_helper(product_ASIN)



    def detect_helper(self, product_ASIN):
        review_val = self.detect_review_anomalies(product_ASIN)
        rating_val = self.detect_rating_anomalies(product_ASIN)
        return [review_val, rating_val]
        


    def detect_review_anomalies(self, product_ASIN):
        # Calculate an even number of bins based on range of unix_review_times x months        
        self.graph_info = {"method": "count", "title": "Review Count Anomalies"}
        self.series['review_anomaly'] = self.generate_frame()
        return self.calculate(product_ASIN)



    def detect_rating_anomalies(self, product_ASIN):
        # Calculate an even number of bins based on range of unixReviewTimes x months 
        self.graph_info = {"method": "mean", "title": "Average Rating Anomalies"}
        self.series['rating_anomaly'] = self.generate_frame()
        return self.calculate(product_ASIN)



    def plot(self, subplot, product_ASIN):
        if self.empty_graph(product_ASIN):
            return
        
        self.graph_info.update({"title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"})
        axis1 = self.plot_frame(subplot[0], self.series['review_anomaly'])
        self.graph_info.update({"title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"})
        axis2 = self.plot_frame(subplot[1], self.series['rating_anomaly'])
        plt.show()
        return [axis1, axis2]



    def calculate(self, product_ASIN):
        total_reviews = Review.objects.filter(asin=product_ASIN).count()

        if(self.graph_info['method'] == 'count'):
            # calculate anomalies in rating value distribution
            try:
                self.review_count_anomalies = detect_ts(self.series['review_anomaly'], max_anoms=0.02, direction='both')
            except:
                self.review_count_anomalies['anoms']['anoms'] = []
            
            review_anomalies = len(self.review_count_anomalies['anoms']['anoms'])
            review_anomaly_score = round(review_anomalies / total_reviews * 100, 2)
            Product.objects.filter(asin=product_ASIN).update(reviewAnomalyRate=review_anomaly_score)
            return review_anomaly_score

        if(self.graph_info['method'] == 'mean'):
            # calculate anomalies in review value distribution
            try:
                self.rating_value_anomalies = detect_ts(self.series['rating_anomaly'], max_anoms=0.02, direction='both')
            except:
                self.rating_value_anomalies['anoms']['anoms'] = []
            
            rating_anomalies = len(self.rating_value_anomalies['anoms']['anoms'])
            rating_anomaly_score = round(rating_anomalies / total_reviews * 100, 2)
            Product.objects.filter(asin=product_ASIN).update(ratingAnomalyRate=rating_anomaly_score)
            return rating_anomaly_score



    def set_info(self, product_ASIN):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=product_ASIN)
        review_times_int = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        review_scores = [review['overall'] for review in reviews.values('overall').order_by('unixReviewTime')]
        self.fake_review_info = {"review_times": review_times_int, "review_scores": review_scores}



    def get_rating_color(self):
        num_of_anoms = len(self.rating_value_anomalies['anoms']['anoms'])
        return check_length(num_of_anoms)



    def get_review_color(self):
        num_of_anoms = len(self.review_count_anomalies['anoms']['anoms'])
        return check_length(num_of_anoms)
    


    def check_length(self, num_of_anoms):
        if num_of_anoms == 0:
            return "green"
        elif num_of_anoms == 1:
            return "orange"
        elif num_of_anoms > 1:
            return "red"