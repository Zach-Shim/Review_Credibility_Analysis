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
        parser.add_argument('productASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['productASIN']
        r_anomaly = Anomaly()
        r_anomaly.detect(asin)        

        fig, ax1, ax2 = plt.subplots(ncols=2, figsize=(11, 7))
        axes = (ax1, ax2)
        fig.subplots_adjust(wspace=0.4)

        r_anomaly.plot({"figure": fig, "axis": axes[0]}, asin)
        fig.show()

        r_anomaly.plot({"figure": fig, "axis": axes[1]}, asin)
        fig.show()


'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self):
        self.reviewDayRange = 0
        self.bucketCount = 0

        self.series = []
        self.metricSeries = pd.DataFrame()

        self.ratingValueAnomalies = defaultdict(dict)
        self.ratingCountAnomalies = defaultdict(dict)

        # invoking the constructor of the parent class  
        #super(Incentivized, self).__init__()  


    # returns reviews in bins of 30-day time series
    def detect(self, productASIN):
        self.getBins(productASIN)
        self.fakeReviewInfo = self.getInfo(productASIN)   

        reviews = Review.objects.filter(asin=productASIN)
        unixReviewTimes = self.fakeReviewInfo["unixReviewTimes"]
        scores = self.fakeReviewInfo["scores"]

        # function computes the count of the given data (similar to histogram function)
        reviewsCount, bin_edges1, binnumber1 = stats.binned_statistic(unixReviewTimes, scores, statistic='count', bins=self.bins)
        reviewsCount = reviewsCount[np.isfinite(reviewsCount)]
        #print(reviewsCount)

        # function computes the mean binned statistical value for the given data (similar to histogram function)
        averageRating, bin_edges, binnumber = stats.binned_statistic(self.fakeReviewInfo["unixReviewTimes"], self.fakeReviewInfo["scores"], statistic='mean', bins=self.bins)
        averageRating = averageRating[np.isfinite(averageRating)]
        #print(averageRating)

        binsTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in self.bins]
        self.compressBins(reviewsCount, binsTimestamps)
        reviewsCount = reviewsCount[reviewsCount != 0]
        #print('binTimestamps: ' + str(len(binsTimestamps)))

        # make a time series data frame and calculate anomalies in rating sitrbutions
        averageRatingValues = {"timestamp": binsTimestamps, "value": averageRating}
        averageRatingSeries = pd.DataFrame(averageRatingValues)
        anomalyScore = self.calculate(averageRatingSeries, reviews.count())
        Product.objects.filter(asin=productASIN).update(ratingAnomalyRate=anomalyScore)

        # make a review count data frame and calculate anomaly rate in review counts (timing)
        reviewCountsValues = {"timestamp": binsTimestamps, "value": reviewsCount}
        reviewCountsSeries = pd.DataFrame(reviewCountsValues)
        anomalyScore = self.calculate(reviewCountsSeries, reviews.count())
        Product.objects.filter(asin=productASIN).update(reviewAnomalyRate=anomalyScore)

        self.series = {"averageRatingSeries": averageRatingSeries, "reviewCountsSeries": reviewCountsSeries}



    def plot(self, subplot, productASIN):
        # Get unixReviewTimes and scores of all fake reviews
        info = self.getInfo(productASIN)
        unixReviewTimes = info["unixReviewTimes"]
        scores = info["scores"]

        # error checking for empty graph
        if (len(unixReviewTimes) == 0 or len(scores) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return

        series = []
        self.bins = self.getBins(productASIN)
        self.fakeReviewInfo = info
        series.append(self.plot_review_anomalies(subplot, productASIN))
        series.append(self.plot_rating_anomalies(subplot, productASIN))
        return series



    def plot_review_anomalies(self, subplot, productASIN):
        # Calculate an even number of bins based on range of unixReviewTimes x months        
        self.method = 'mean'
        self.graphInfo = {"title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"}
        return self.plotAxis(self.bins, subplot, productASIN)



    def plot_rating_anomalies(self, subplot, productASIN):
        # Calculate an even number of bins based on range of unixReviewTimes x months 
        self.method = 'count'
        self.graphInfo = {"title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"}
        return self.plotAxis(self.bins, subplot, productASIN)



    def getInfo(self, productASIN):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=productASIN)
        reviewTimes = [datetime.datetime.fromtimestamp(review['unixReviewTime']).strftime("%m/%d/%Y") for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewTimesInt = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewScores = [review['overall'] for review in reviews.values('overall').order_by('overall')]
        return {"reviewTimesInt": reviewTimesInt, "reviewScores": reviewScores}




    def calculate(self, productASIN):
        anomalyValues = {"reviewValueAnomalies": 0, "ratingValueAnamolies": 0}

        # calculate anomalies in review value distribution
        try:
            anomalyValues['reviewValueAnomalies'] = detect_ts(self.series["averageRatingSeries"], max_anoms=0.02, direction='both')
        except:
            self.ratingValueAnomalies['anoms']['anoms'] = []

        # calculate anomalies in rating value distribution
        try:
            anomalyValues['reviewValueAnomalies'] = detect_ts(self.series["reviewCountsSeries"], max_anoms=0.02, direction='both')
        except:
            self.ratingValueAnomalies['anoms']['anoms'] = []

        return anomalyValues



    def getValueAnomalies(self):
        return self.ratingValueAnomalies



    def getSeries(self):
        return self.series



    def getBins(self, productASIN):
        # get posting date range (earliest post - most recent post)
        mostRecentDate = Review.objects.filter(asin=productASIN).aggregate(Min('unixReviewTime'))
        farthestDate = Review.objects.filter(asin=productASIN).aggregate(Max('unixReviewTime'))
        reviewRange = datetime.datetime.fromtimestamp(farthestDate['unixReviewTime__max']) - datetime.datetime.fromtimestamp(mostRecentDate['unixReviewTime__min'])
        
        # calculate review range
        reviewDayRange = reviewRange.days
        bucketCount = math.ceil(reviewRange.days / 30)
        print("It has reviews ranging " + str(reviewDayRange) + " days. Bucket count " + str(bucketCount))
        
        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        self.bins = np.linspace(mostRecentDate['unixReviewTime__min'], farthestDate['unixReviewTime__max'], bucketCount)


