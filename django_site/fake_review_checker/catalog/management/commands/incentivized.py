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
        parser.add_argument('product_ASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['product_ASIN']
        incentivized = Incentivized()
        incentivized.find_keywords()
        incentivized.detect(asin)
        
        '''
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        plot = incentivized.plot({"figure": fig, "axis": ax1}, asin)
        #plot.show()
        #plot["figure"].show()
        '''



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

        self.incentivized_review_times = []
        self.incentivized_scores = []
        # invoking the constructor of the parent class  
        #super(Incentivized, self).__init__()  



    def find_keywords(self):
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



    def detect(self, product_ASIN):
        # search each review in product_ASIN for incentivized keywords; incentivizedList is used for review_anomaly
        self.words_re = re.compile("|".join(self.completeKeyPhraseList))
        queries_to_update = []
        for review in Review.objects.filter(asin=product_ASIN).values('id', 'reviewText'):
            if self.words_re.search(review['reviewText']):
                queries_to_update.append(review['id'])
        self._update_db(queries_to_update)

        return self.calculate(product_ASIN)



    # accepts a list of review id's to update
    def _update_db(self, queries_to_update):
        print("\nPushing to database " + str(datetime.datetime.now()) + " start")
        for review in queries_to_update:
            obj = Review.objects.filter(id=review).values('unixReviewTime', 'overall')
            print(obj)
            self.incentivized_review_times.append(obj[0]['unixReviewTime'])
            self.incentivized_scores.append(obj[0]['overall'])
            obj.update(incentivized=1)
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")



    def plot(self, subplot, product_ASIN):
        # error checking for empty graph
        info = self.get_info(product_ASIN)
        if (len(info["unixReviewTimes"]) == 0 or len(info["scores"]) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return "Empty Plot"

        # Calculate an even number of bins based on range of unixReviewTimes x months
        self.bins = self.getBins(product_ASIN)
        self.fake_review_info = info

        self.method = 'count'
        self.graph_info = {"title": "Incentivized Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        #return self.plotAxis(self.bins, subplot, product_ASIN)

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

        dp = graph_frame.plot(x='timestamp', y='value', title=self.graph_info['title'], kind='line', ax=subplot["axis"])
        dp.set_ylabel(y_axis)
        dp.set_xlabel(x_axis)

        return dp



    def get_info(self, product_ASIN):
        unixReviewTimes = []
        scores = []
        for review in Review.objects.filter(asin=product_ASIN, incentivized=1):
            unixReviewTimes.append(review.unixReviewTime)
            scores.append(review.overall)
        return {"unixReviewTimes": unixReviewTimes, "scores": scores}



    def calculate(self, product_ASIN):
        # calculate incentivized score = (total number of incentivized reviews) / (total number of reviews for asin)
        incentivized = Review.objects.filter(asin=product_ASIN, incentivized=1).count()
        total_reviews = Review.objects.filter(asin=product_ASIN).count()
        incentivized_score = round(incentivized / total_reviews * 100, 2)
        Product.objects.filter(asin=product_ASIN).update(incentivizedRatio=(incentivized_score))
        return incentivized_score



    def get_bins(self, product_ASIN):
        reviews = Review.objects.filter(asin=product_ASIN, incentivized=1)
        return self.get_date_range(reviews)