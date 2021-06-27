# Python Imports
import datetime
import numpy as np
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

        self.method = method
        self.graph_info = graph_info

        self.graph_frames = dict()
        self.bins = []
        


    def detect(self, product_ASIN):
        print("detect parent class")



    def generate_frame(self, algorithm):
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
        self.graph_frames[algorithm] = pd.DataFrame(graph_series)



    def plot_axes(self, subplot):
        # Graph the values (fake score x time intervals)
        title = self.graph_info['title'] 
        y_axis = self.graph_info['y_axis'] 
        x_axis = self.graph_info['x_axis'] 

        for frame in self.graph_frames:
            dp = frame.plot(x='timestamp', y='value', title=self.graph_info['title'], kind='line', ax=subplots["axis"])
            dp.set_ylabel(y_axis)
            dp.set_xlabel(x_axis)
            return dp



    def empty_graph(self):
        unix_review_times = self.fake_review_info["review_times"]
        scores = self.fake_review_info["review_scores"]

        # error checking for empty graph
        if (len(unix_review_times) == 0 or len(scores) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return



    def compress_bins(self, review_count, bin_timestamps):
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        for i in range(len(review_count)-1, len(bin_timestamps)-1):
            bin_timestamps.pop()



    def set_info(self, product_ASIN):
        print("getInfo parent class")



    def calculate(self, product_ASIN):
        print("calculate parent class")



    def get_bins(self, product_ASIN):
        print("getBins parent class")



    def get_date_range(self, reviews):
        # get posting date range (earliest post - most recent post)
        most_recent_date = reviews.aggregate(Min('unixReviewTime'))
        farthest_date = reviews.aggregate(Max('unixReviewTime'))
        review_range = datetime.datetime.fromtimestamp(farthest_date['unixReviewTime__max']) - datetime.datetime.fromtimestamp(most_recent_date['unixReviewTime__min'])
        
        # calculate review range
        review_day_range = review_range.days
        bucket_count = math.ceil(review_range.days / 30)
        print("Product has reviews ranging " + str(review_day_range) + " days. Bucket count " + str(bucket_count))
        
        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        bins = np.linspace(most_recent_date['unixReviewTime__min'], farthest_date['unixReviewTime__max'], bucket_count)
        return bins
    