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
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self, graph_info):
        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__(graph_info)  



    # returns reviews in bins of 30-day time series
    def detect_anomalies(self, product_ASIN):
        self.product_ASIN = product_ASIN
        self.set_info()

        # Calculate an even number of bins based on range of unix_review_times x months
        self.series = self.generate_frame()
        print(self.series)

        # calculate anomalies in rating value distribution
        detected_anomalies = dict()
        try:
            detected_anomalies = detect_ts(self.series, max_anoms=0.02, direction='both')
            return len(detected_anomalies['anoms']['anoms'])
        except:
            return 0
        
        print("error")
        return 0


    # overloaded plot method, because we had to build the dataframes in detect in order to analyze the data
    def plot(self, subplot):
        if self.empty_graph(subplot):
            return
        self.plot_frame(subplot, self.series)



    def set_info(self):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=self.product_ASIN)
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