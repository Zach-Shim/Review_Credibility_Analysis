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
        self.fakeReviewInfo = dict()
        self.graphInfo = dict()
    
        self.bins = []
        self.method = ""


    def detect(self, productASIN):
        print("detect parent class")



    def plotAxis(self, bins, subplots, method, productASIN):
        # Get unixReviewTimes and scores of all fake reviews
        unixReviewTimes = self.fakeReviewInfo["unixReviewTimes"]
        scores = self.fakeReviewInfo["scores"]

        # Place these metrics into even bins of values
        reviewsCount, bin_edges, binnumber = stats.binned_statistic(unixReviewTimes, scores, statistic=method, bins=self.bins)
        reviewsCount = reviewsCount[np.isfinite(reviewsCount)]

        # Get the timed intervals of each bin
        binTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in self.bins]
        self.compressBins(reviewsCount, binTimestamps)

        # Create data frame that will be translated to a subplot
        graph_series = {"timestamp": binTimestamps, "value": reviewsCount}
        graph_frame = pd.DataFrame(graph_frame)

        # Graph the values (fake score x time intervals)
        title = self.title + " Review Counts"
        y_axis = "Number of Reviews"
        x_axis = "Time"

        dp = graph_frame.plot(x='timestamp', y='value', title=self.graphInfo['title'], kind='line', ax=subplots["axis"])
        dp.set_ylabel(y_axis)
        dp.set_xlabel(x_axis)

        return dp




    def compressBins(self, reviewsCount, binTimestamps):
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        i = j = 0
        n = len(reviewsCount)
        while i < n:
            if reviewsCount[i] == 0:
                del binTimestamps[j]
                i = i + 1
            else:
                j = j + 1
                i = i + 1
        del binTimestamps[-1]




    def getInfo(self, productASIN):
        print("getInfo parent class")



    def calculate(self, productASIN):
        print("calculate parent class")



    def getBins(self, productASIN):
        print("getBins parent class")



    def getDateRange(self, reviews):
        # get posting date range (earliest post - most recent post)
        mostRecentDate = reviews.aggregate(Min('unixReviewTime'))
        farthestDate = reviews.aggregate(Max('unixReviewTime'))
        reviewRange = datetime.datetime.fromtimestamp(farthestDate['unixReviewTime__max']) - datetime.datetime.fromtimestamp(mostRecentDate['unixReviewTime__min'])
        
        # calculate review range
        reviewDayRange = reviewRange.days
        bucketCount = math.ceil(reviewRange.days / 30)
        print("Product has reviews ranging " + str(reviewDayRange) + " days. Bucket count " + str(bucketCount))
        
        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        bins = np.linspace(mostRecentDate['unixReviewTime__min'], farthestDate['unixReviewTime__max'], bucketCount)
        return bins
    