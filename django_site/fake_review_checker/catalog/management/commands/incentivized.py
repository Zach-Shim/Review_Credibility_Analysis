# Python Imports 
from collections import defaultdict
import datetime
import math
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
from nltk.corpus import wordnet
import nltk
import re
import pandas as pd
import scipy.stats as stats

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms


'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review
        Also used as terminal command: python manage.py incentivized (asin)
    Parameters:
        A valid product ASIN given as input in the command line
'''
class Command(BaseCommand):
    help = 'Get product incentivized scores'

    # adds an argument to **kwards in the handle function
    def add_arguments(self, parser):
        parser.add_argument('productASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['productASIN']
        incentivized = Incentivized()
        incentivized.findKeywords()
        incentivized.calculate(asin)
        
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        plot = incentivized.plot({"figure": fig, "axis": ax1}, asin)
        #plot.show()
        #plot["figure"].show()
        #plot["figure"].show()
        



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's incentivized score
    Parameters:
        A valid product ASIN
'''
class Incentivized(DetectionAlgorithms):

    def __init__(self):
        self.keyWords =["honest", "discount", "review", "feedback", "exchange", "discount", "coupon"]
        self.keyPhraseList = ["honest feedback", "honest review", "in exchange", "discount", "coupon"]
        self.words_re = ""
        self.completeKeyPhraseList = []
        self.antonyms = []

        # invoking the constructor of the parent class  
        #super(Incentivized, self).__init__()  



    def findKeywords(self):
        for word in self.keyWords:
            synonyms = []
            for syn in wordnet.synsets(word):
                for l in syn.lemmas():
                    synonyms.append(l.name())
            #print(word +  " = " + str(set(synonyms)))
            for phrase in self.keyPhraseList:
                if word in phrase:
                    for newWord in synonyms:
                        self.completeKeyPhraseList.append(phrase.replace(word, newWord))
        self.completeKeyPhraseList = [w.replace('_', ' ') for w in set(self.completeKeyPhraseList)]
        #print(set(self.completeKeyPhraseList))



    def detect(self, productASIN):
        # query total number of reviews for current product, then query all reviews where the incentivzed score != 0
        reviews = Review.objects.all().filter(asin=productASIN)
        totalReviews = reviews.count()
        
        # search each review for incentivized keywords; incentivizedList is used for review_anomaly
        self.words_re = re.compile("|".join(self.completeKeyPhraseList))
        incentivizedReviews = 0
        for review in reviews:
            if self.words_re.search(review.reviewText):
                incentivizedReviews += 1
                #Review.objects.filter(reviewID=review.reviewID, asin=review.asin, reviewerID=review.reviewerID).update(incentivized=1)

        return getInfo(productASIN)



    def plot(self, subplot, productASIN):

        # error checking for empty graph
        info = self.getInfo(productASIN)
        if (len(info["unixReviewTimes"]) == 0 or len(info["scores"]) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return "Empty Plot"

        # Calculate an even number of bins based on range of unixReviewTimes x months
        self.bins = self.getBins(productASIN)
        self.fakeReviewInfo = info

        self.method = 'count'
        self.graphInfo = {"title": "Incentivized Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        #return self.plotAxis(self.bins, subplot, productASIN)

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

        dp = graph_frame.plot(x='timestamp', y='value', title=self.graphInfo['title'], kind='line', ax=subplot["axis"])
        dp.set_ylabel(y_axis)
        dp.set_xlabel(x_axis)
        
        plt.show()
        return subplot



    def getInfo(self, productASIN):
        unixReviewTimes = []
        scores = []
        for review in Review.objects.filter(asin=productASIN, incentivized=1):
            unixReviewTimes.append(review.unixReviewTime)
            scores.append(review.overall)
        return {"unixReviewTimes": unixReviewTimes, "scores": scores}



    def calculate(self, productASIN):
        # calculate incentivized score = (total number of incentivized reviews) / (total number of reviews for asin)
        incentivized = Review.objects.filter(asin=productASIN, incentivized=1).count()
        totalReviews = Review.objects.filter(asin=productASIN).count()
        incentivizedScore = round(incentivized / totalReviews * 100, 2)
        Product.objects.filter(asin=productASIN).update(incentivizedRatio=(incentivizedScore))
        return incentivizedScore



    def getBins(self, productASIN):
        reviews = Review.objects.filter(asin=productASIN, incentivized=1)
        return self.getDateRange(reviews)