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
    
    def __init__(self):
        self.fake_review_info = dict()
        self.graph_info = dict()
    
        self.bins = []
        self.method = ""


    def detect(self, productASIN):
        print("detect parent class")



    def plot_axes(self, bins, subplots, method, productASIN):
        # Get unixReviewTimes and scores of all fake reviews
        unix_review_times = self.fake_review_info["unixReviewTimes"]
        scores = self.fake_review_info["scores"]

        # Place these metrics into even bins of values
        review_count, bin_edges, binnumber = stats.binned_statistic(unix_review_times, scores, statistic=method, bins=self.bins)
        review_count = review_count[np.isfinite(review_count)]

        # Get the timed intervals of each bin
        bin_timestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in self.bins]
        self.compress_bins(review_count, bin_timestamps)

        # Create data frame that will be translated to a subplot
        graph_series = {"timestamp": bin_timestamps, "value": review_count}
        graph_frame = pd.DataFrame(graph_frame)

        # Graph the values (fake score x time intervals)
        title = self.title + " Review Counts"
        y_axis = "Number of Reviews"
        x_axis = "Time"

        dp = graph_frame.plot(x='timestamp', y='value', title=self.graph_info['title'], kind='line', ax=subplots["axis"])
        dp.set_ylabel(y_axis)
        dp.set_xlabel(x_axis)

        return dp




    def compress_bins(self, review_count, bin_timestamps):
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        i = j = 0
        n = len(review_count)
        while i < n:
            if review_count[i] == 0:
                del bin_timestamps[j]
                i = i + 1
            else:
                j = j + 1
                i = i + 1
        del bin_timestamps[-1]




    def get_info(self, product_ASIN):
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
    