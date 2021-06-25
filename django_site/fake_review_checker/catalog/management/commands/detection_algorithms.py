# Python Imports
import datetime
import math
import numpy as np
import pandas as pd

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.db.models import Max, Min, Avg

# Relative Imports
from ...models import User, Product, Review

class DetectionAlgorithms:
    
    def __init__(self, productASIN):
        self.reviewInfo = dict()
        self.__store_reviews(productASIN)
    


    def __store_reviews(self, productASIN):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=productASIN)
        reviewCount = reviews.count()
        reviewTimes = [datetime.datetime.fromtimestamp(review['unixReviewTime']).strftime("%m/%d/%Y") for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewTimesInt = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        reviewScores = [review['overall'] for review in reviews.values('overall').order_by('overall')]
        self.reviewsInfo = {"reviewTimesInt": reviewTimesInt, "reviewScores": reviewScores, "reviewCount": reviewCount}



    def bin(self, productASIN):
        # get posting date range (earliest post - most recent post)
        mostRecentDate = Review.objects.filter(asin=productASIN).aggregate(Min('unixReviewTime'))
        farthestDate = Review.objects.filter(asin=productASIN).aggregate(Max('unixReviewTime'))
        reviewRange = datetime.datetime.fromtimestamp(farthestDate['unixReviewTime__max']) - datetime.datetime.fromtimestamp(mostRecentDate['unixReviewTime__min'])
        
        # calculate review range
        reviewDayRange = reviewRange.days
        bucketCount = math.ceil(reviewRange.days / 30)
        print("It has reviews ranging " + str(reviewDayRange) + " days. Bucket count " + str(bucketCount))
        
        # Returns num evenly spaced samples, calculated over the interval [start, stop]. num = Number of samples to generate
        bins = np.linspace(mostRecentDate['unixReviewTime__min'], farthestDate['unixReviewTime__max'], bucketCount)
        return bins
    
    '''
    def calculate(self):

    def getInfo(self):

    def getSeries(self):
    
    def getBins(self):

    def getBinTimeStamps(self):
    '''
    