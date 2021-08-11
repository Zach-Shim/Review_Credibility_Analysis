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
    
    def __init__(self, graph_info):
        self.fake_review_info = dict()
        self.graph_info = graph_info
        self.product_ASIN = ""
        self.review_day_range = 0
    
        # plotting info
        self.df = pd.DataFrame()

        self.error_msg = ""



    def detect(self, product_ASIN):
        pass



    def generate_frame(self):
        print("generating frame")
        # Get unixReviewTimes and scores of all fake reviews
        unix_review_times = self.fake_review_info["review_times"]
        scores = self.fake_review_info["review_scores"]

        bins = self.get_bins()

        # Place these metrics into even bins of values
        value, bin_edges, binnumber = stats.binned_statistic(np.array(unix_review_times,dtype='float64'), np.array(scores,dtype='float64'), statistic=self.graph_info['method'], bins=bins)
        value = value[np.isfinite(value)]

        # Get the timed intervals of each bin; convert timestamp string to datetime, then to unix timestamp integer
        bin_timestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in bins]
        value = self.compress_bins(value, bin_timestamps)

        # Create data frame that will be translated to a subplot
        graph_series = {"timestamp": bin_timestamps, "value": value}
        graph_frame = pd.DataFrame(graph_series)

        return graph_frame



    def plot(self, subplot):
        # Get unixReviewTimes and scores of all fake reviews
        self.set_info()
        if self.empty_graph(subplot):
            return False

        self.df = self.generate_frame()
        self.plot_frame(subplot, self.df)
        return True



    def plot_frame(self, subplot, frame):
        # Graph the values (fake score x time intervals)
        title = self.graph_info['title'] 
        y_axis = self.graph_info['y_axis'] 
        x_axis = self.graph_info['x_axis'] 

        try:
            print("current frame:\n", frame)
            dp = frame.plot(x='timestamp', y='value', title=title, kind='line', ax=subplot)
            dp.set_ylabel(y_axis)
            dp.set_xlabel(x_axis)
        except:
            self.error_msg = "Unable to plot frame"
            return False

        return True



    def empty_graph(self, subplot):
        try:
            unix_review_times = self.fake_review_info["review_times"]
            scores = self.fake_review_info["review_scores"]
        except:
            self.error_msg = "No data to analyze"
            return True

        # error checking for empty graph
        if (len(unix_review_times) == 0 or len(scores) == 0):
            plt.delaxes(subplot)
            return True
        
        return False



    def compress_bins(self, review_count, bin_timestamps):
        '''
        print("review count before: " + str(len(review_count)))
        print("review_count")
        for i in range(0, len(review_count)):
            print(str(review_count[i]))
        print("bintime count before: " + str(len((bin_timestamps))))
        '''
        
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        rcl = len(review_count)
        btsl = len(bin_timestamps)

        new_review_count = []
        if "Anomalies" in self.graph_info['title']:
            i = 0
            while i < rcl:
                if review_count[i] > 0:
                    new_review_count.append(review_count[i])
                i += 1
            review_count = new_review_count
            rcl = len(new_review_count)
        if rcl < btsl:
            while rcl < btsl:
                bin_timestamps.pop()
                rcl += 1
        
        ''' 
        print("review count after: " + str(len(review_count)))
        print("review_count")
        for i in range(0, len(review_count)):
            print(str(review_count[i]))
        print("bintime count after: " + str(len((bin_timestamps))))
        '''
        
        return review_count



    def calculate(self, fake_reviews, total):
        pass



    def get_bins(self):
        reviews = Review.objects.filter(asin=self.product_ASIN)

        # get posting date range (earliest post - most recent post)
        most_recent_date = reviews.aggregate(Min('unixReviewTime'))
        farthest_date = reviews.aggregate(Max('unixReviewTime'))
        review_range = datetime.datetime.fromtimestamp(farthest_date['unixReviewTime__max']) - datetime.datetime.fromtimestamp(most_recent_date['unixReviewTime__min'])

        # calculate review range
        self.review_day_range = review_range.days
        bucket_count = math.ceil(review_range.days / 30)
        print("Product has reviews ranging " + str(self.review_day_range) + " days. Bucket count " + str(bucket_count))
        
        # Returns num of evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        return np.linspace(most_recent_date['unixReviewTime__min'], farthest_date['unixReviewTime__max'], bucket_count)
       
    

    def set_info(self, reviews):
        try:
            review_ids = []
            unix_review_times = []
            scores = []
            for review in reviews.values('reviewID', 'unixReviewTime', 'overall').order_by('unixReviewTime'):
                review_ids.append(review['reviewID'])
                unix_review_times.append(review['unixReviewTime'])
                scores.append(review['overall'])
            self.fake_review_info = {"review_ids": review_ids, "review_times": unix_review_times, "review_scores": scores}
        except:
            return False
            


    def get_day_range(self):
        return self.review_day_range