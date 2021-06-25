# Python Imports
import datetime
import math
import pandas as pd
import webbrowser

import numpy as np
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
        r_anomaly = Anomaly(asin)
        r_anomaly.detect(asin)        



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self, productASIN):
        self.reviewDayRange = 0
        self.bucketCount = 0
        self.reviewsInfo = {}

        self.bins = []
        self.metricSeries = pd.DataFrame()

        self.ratingValueAnomalies = defaultdict(dict)
        self.ratingCountAnomalies = defaultdict(dict)

        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__(productASIN)  


    # returns reviews in bins of 30-day time series
    def detect(self, productASIN):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=productASIN)
        reviewTimes = [datetime.datetime.fromtimestamp(review['unixReviewTime']).strftime("%m/%d/%Y") for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewTimesInt = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewScores = [review['overall'] for review in reviews.values('overall').order_by('overall')]
        self.reviewsInfo = {"reviewTimesInt": reviewTimesInt, "reviewScores": reviewScores}

        print(reviewTimesInt)
        # function computes the mean binned statistical value for the given data (similar to histogram function)
        averageRating, bin_edges, binnumber = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='mean', bins=self.bins)
        averageRating = averageRating[np.isfinite(averageRating)]
        print(averageRating)

        # function computes the count of the given data (similar to histogram function)
        reviewsCount, bin_edges1, binnumber1 = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='count', bins=self.bins)
        reviewsCount = reviewsCount[np.isfinite(reviewsCount)]
        print(reviewsCount)

        binsTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in self.bins]
        self.compressBins(reviewsCount, binsTimestamps)
        reviewsCount = reviewsCount[reviewsCount != 0]
        print('binTimestamps: ' + str(len(binsTimestamps)))

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
        


    def compressBins(self, reviewsCount, binsTimestamps):
        # if number of initial bins exceeds review count and average rating bins, minimize bins length until it is equal in size of review count and average rating
        i = j = 0
        n = len(reviewsCount)
        while i < n:
            if reviewsCount[i] == 0:
                del binsTimestamps[j]
                i = i + 1
            else:
                j = j + 1
                i = i + 1
        del binsTimestamps[-1]



    def calculate(self, series, total):
        # calculate anomalies in review value distribution
        try:
            self.ratingValueAnomalies = detect_ts(series, max_anoms=0.02, direction='both')
        except:
            self.ratingValueAnomalies['anoms']['anoms'] = []

        anomalies = len(self.ratingValueAnomalies['anoms'].anoms)
        return round((anomalies / total) * 100, 2) 



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



    def getReviewInfo(self):
        self.reviewsInfo


    '''
    def getDateRange(self):
        return self.reviewDayRange



    def getBucketCount(self):
        return self.bucketCount
    '''