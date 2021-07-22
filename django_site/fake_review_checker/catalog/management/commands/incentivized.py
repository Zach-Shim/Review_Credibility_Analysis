# Python Imports 
import datetime
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
        parser.add_argument('asin', type=str, nargs='?', help='Indicates the asin of the product we are currently analyzing')
        parser.add_argument('-a', '--all', action='store_true', help='Run similarity on all products')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['asin']
        incentivized = Incentivized()
        
        if kwargs['all']:
            # run on entire database (takes a really long time if database is large because it has to cross check data)
            incentivized.detect_all()
        elif kwargs['asin']:
            # run on specific product asin (uncomment this section and commment out above two lines)
            incentivized.detect(asin)
            fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
            fig.subplots_adjust(wspace=0.5)
            incentivized.plot(ax1)
            plt.show()
        else:
            print("Please enter an asin, or enter the -a command")


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
        self.product_ASIN = product_ASIN
        self.detect_helper(Review.objects.filter(asin=self.product_ASIN).values('reviewID', 'reviewText'))

        return self.calculate(len(queries_to_update), Review.objects.filter(asin=self.product_ASIN).count())



    def detect_all(self):
        self.detect_helper(Review.objects.values('reviewID', 'reviewText'))



    def detect_helper(self, reviews):
        review_num = 0
        queries_to_update = []
        self.words_re = re.compile("|".join(self.completeKeyPhraseList))

        for review in reviews:
            if self.words_re.search(review['reviewText']):
                queries_to_update.append(review['reviewID'])

            if review_num % 1000 == 0:
                print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num))

            review_num += 1

        print("\nMatching " + str(datetime.datetime.now()) + " finished")
        self._update_db(queries_to_update)



    # accepts a list of reviewID's to update
    def _update_db(self, queries_to_update):
        print("\nPushing to database " + str(datetime.datetime.now()) + " start")
        for review in queries_to_update:
            obj = Review.objects.filter(reviewID=review).update(incentivized=1)
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")



    def calculate(self, fake_reviews, total):
        # calculate incentivized score = (total number of incentivized reviews) / (total number of reviews for asin)
        incentivized_score = round(fake_reviews / total * 100, 2)
        Product.objects.filter(asin=self.product_ASIN).update(incentivizedRatio=incentivized_score)
        return incentivized_score



    def set_info(self):    
        super(Incentivized, self).set_info(Review.objects.filter(asin=self.product_ASIN, incentivized=1))