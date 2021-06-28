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
        incentivized.detect(asin)
        
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        incentivized.plot(ax1, asin)


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
        self.find_keywords()

        self.series = []
        
        # invoking the constructor of the parent class  
        graph_info = {"method": "count", "title": "Incentivized Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        super(Incentivized, self).__init__(graph_info)  



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
            obj = Review.objects.filter(id=review).update(incentivized=1)
            '''
            obj = Review.objects.filter(id=review).values('unixReviewTime', 'overall')
            print(obj)
            self.incentivized_review_times.append(obj[0]['unixReviewTime'])
            self.incentivized_scores.append(obj[0]['overall'])
            obj.update(incentivized=1)
            '''
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")



    def plot(self, subplot, product_ASIN):
        # Get unixReviewTimes and scores of all fake reviews
        self.set_bins(product_ASIN)
        self.set_info(product_ASIN)
        if self.empty_graph(subplot):
            return

        self.series = self.generate_frame()
        self.plot_frame(subplot, self.series)
        plt.show()
        return 



    def calculate(self, product_ASIN):
        # calculate incentivized score = (total number of incentivized reviews) / (total number of reviews for asin)
        incentivized = Review.objects.filter(asin=product_ASIN, incentivized=1).count()
        total_reviews = Review.objects.filter(asin=product_ASIN).count()
        incentivized_score = round(incentivized / total_reviews * 100, 2)
        Product.objects.filter(asin=product_ASIN).update(incentivizedRatio=(incentivized_score))
        return incentivized_score



    def set_info(self, product_ASIN):
        unix_review_times = []
        scores = []
        for review in Review.objects.filter(asin=product_ASIN, incentivized=1):
            unix_review_times.append(review.unixReviewTime)
            scores.append(review.overall)
        self.fake_review_info = {"review_times": unix_review_times, "review_scores": scores}
