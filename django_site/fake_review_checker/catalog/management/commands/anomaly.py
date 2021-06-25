# Python Imports
import datetime
import math
import pandas as pd
import webbrowser

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt, mpld3
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
from .incentivized import Incentivized



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
        r_anomaly = ReviewAnomaly()
        r_anomaly.detect(asin)        



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class ReviewAnomaly:

    def __init__(self):
        self.reviewDayRange = 0
        self.bucketCount = 0

        self.ratingValueAnomalies = defaultdict(dict)
        self.ratingCountAnomalies = defaultdict(dict)


    # returns reviews in bins of 30-day time series
    def detect(self, productASIN):
        # get posting date range (earliest post - most recent post)
        mostRecentDate = Review.objects.filter(asin=productASIN).aggregate(Min('unixReviewTime'))
        farthestDate = Review.objects.filter(asin=productASIN).aggregate(Max('unixReviewTime'))
        reviewRange = datetime.datetime.fromtimestamp(farthestDate['unixReviewTime__max']) - datetime.datetime.fromtimestamp(mostRecentDate['unixReviewTime__min'])
        
        # save review range
        self.reviewDayRange = reviewRange.days
        self.bucketCount = reviewRange.days / 30
        print("It has reviews ranging " + str(self.reviewDayRange) + " days. Bucket count " + str(self.bucketCount))

        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        bins = np.linspace(mostRecentDate['unixReviewTime__min'], farthestDate['unixReviewTime__max'], math.ceil(self.bucketCount))
        print('bins: ' + str(len(bins)))

        # Calculate sets of review anomaly data for histogram bins
        reviews = Review.objects.filter(asin=productASIN)
        reviewTimes = [datetime.datetime.fromtimestamp(review['unixReviewTime']).strftime("%m/%d/%Y") for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewTimesInt = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewScores = [review['overall'] for review in reviews.values('overall').order_by('overall')]

        # function computes the mean binned statistical value for the given data (similar to histogram function)
        averageRating, bin_edges, binnumber = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='mean', bins=bins)
        averageRating = averageRating[np.isfinite(averageRating)]
        print('averageRating binNumber: ' + str(binnumber))
        print('averageRating binNumber length: ' + str(len(binnumber)))
        print('averageRating: ' + str(len(averageRating)))

        # function computes the count of the given data (similar to histogram function)
        reviewsCount, bin_edges1, binnumber1 = stats.binned_statistic(reviewTimesInt, reviewScores, statistic='count', bins=bins)
        reviewsCount = reviewsCount[np.isfinite(reviewsCount)]

        binsTimestamps = [np.datetime64(datetime.datetime.fromtimestamp(x)) for x in bins]

        # make a time series data frame
        averageRatingValues = {"timestamp": binsTimestamps, "value": averageRating}
        
        #print(binsTimestamps)
        print('binTimestamps: ' + str(len(binsTimestamps)))
        #print(averageRating)
        print('averageRating: ' + str(len(averageRating)))
        

        '''
        averageRatingSeries = pd.DataFrame(averageRatingValues)
        try:
            self.ratingValueAnomalies = detect_ts(averageRatingSeries, max_anoms=0.02, direction='both')
        except:
            self.ratingValueAnomalies['anoms']['anoms'] = []

        # make a review count data frame
        reviewCountsValues = {"timestamp": binsTimestamps, "value": reviewsCount}
        reviewCountsSeries = pd.DataFrame(reviewCountsValues)
        try:
            self.ratingCountAnamolies = detect_ts(reviewCountsSeries, max_anoms=0.02, direction='both')
        except:
            self.ratingCountAnamolies['anoms']['anoms'] = []

        print("self.ratingCountAnamolies['anoms']['anoms']")
        print(self.ratingCountAnamolies['anoms']['anoms'])
        print(reviews.all().count())
        ratingAnamolyRate = self.ratingCountAnamolies['anoms']['anoms'] / reviews.all().count()
        print()
    '''
    def getDateRange(self):
        return self.reviewDayRange
    
    def getBucketCount(self):
        return self.bucketCount
    