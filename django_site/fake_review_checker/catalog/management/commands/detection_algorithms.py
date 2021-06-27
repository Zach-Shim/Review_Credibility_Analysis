# Python Imports
import datetime
import numpy as np
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import math
import pandas as pd
import scipy.stats as stats

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.db.models import Max, Min, Avg

# Relative Imports
from ...models import User, Product, Review

class DetectionAlgorithms:
    
    def __init__(self, method = None, graph_info = None):
        self.fake_review_info = dict()
        self.bins = []
        
        self.method = method
        self.graph_info = graph_info



    def detect(self, product_ASIN):
        print("detect parent class")



    def generate_frame(self):
        print("generating frame")
        # Get unixReviewTimes and scores of all fake reviews
        unix_review_times = self.fake_review_info["review_times"]
        scores = self.fake_review_info["review_scores"]

        # Place these metrics into even bins of values
        review_count, bin_edges, binnumber = stats.binned_statistic(unix_review_times, scores, statistic=self.method, bins=self.bins)
        review_count = review_count[np.isfinite(review_count)]

        # Get the timed intervals of each bin
        bin_timestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in self.bins]
        self.compress_bins(review_count, bin_timestamps)

        # Create data frame that will be translated to a subplot
        graph_series = {"timestamp": bin_timestamps, "value": review_count}
        graph_frame = pd.DataFrame(graph_series)
        return graph_frame


    def plot_axes(self, subplot, frame):
        # Graph the values (fake score x time intervals)
        title = self.graph_info['title'] 
        y_axis = self.graph_info['y_axis'] 
        x_axis = self.graph_info['x_axis'] 

        print("current frame:")
        print(frame)
        dp = frame.plot(x='timestamp', y='value', title=self.graph_info['title'], kind='line', ax=subplot)
        dp.set_ylabel(y_axis)
        dp.set_xlabel(x_axis)



    def empty_graph(self, subplot):
        unix_review_times = self.fake_review_info["review_times"]
        scores = self.fake_review_info["review_scores"]

        # error checking for empty graph
        if (len(unix_review_times) == 0 or len(scores) == 0):
            plt.delaxes(subplot)
            return True
        
        return False



    def compress_bins(self, review_count, bin_timestamps):
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        if(len(bin_timestamps) > len(review_count)):
            for i in range(len(review_count)-1, len(bin_timestamps)-1):
                bin_timestamps.pop()



    def calculate(self, product_ASIN):
        print("calculate parent class")



    def set_info(self, product_ASIN):
        print("getInfo parent class")



    def set_bins(self, product_ASIN):
        reviews = Review.objects.filter(asin=product_ASIN)

        # get posting date range (earliest post - most recent post)
        most_recent_date = reviews.aggregate(Min('unixReviewTime'))
        farthest_date = reviews.aggregate(Max('unixReviewTime'))
        review_range = datetime.datetime.fromtimestamp(farthest_date['unixReviewTime__max']) - datetime.datetime.fromtimestamp(most_recent_date['unixReviewTime__min'])

        # calculate review range
        review_day_range = review_range.days
        bucket_count = math.ceil(review_range.days / 30)
        print("Product has reviews ranging " + str(review_day_range) + " days. Bucket count " + str(bucket_count))
        
        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        self.bins = np.linspace(most_recent_date['unixReviewTime__min'], farthest_date['unixReviewTime__max'], bucket_count)
       
    