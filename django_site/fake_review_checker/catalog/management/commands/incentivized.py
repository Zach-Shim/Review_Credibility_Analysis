# Python Imports 
from nltk.corpus import wordnet
import nltk
import re
from collections import defaultdict

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

# Relative Imports
from ...models import User, Product, Review



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
        incentivized.detectKeywords()
        incentivized.calculate(asin)



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's incentivized score
    Parameters:
        A valid product ASIN
'''
class Incentivized:

    def __init__(self):

        self.keyWords =["honest", "discount", "review", "feedback", "exchange", "discount", "coupon"]
        self.keyPhraseList = ["honest feedback", "honest review", "in exchange", "discount", "coupon"]
        self.completeKeyPhraseList = []
        self.antonyms = []
        self.words_re = ""

    def detectKeywords(self):
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

    def calculate(self, productASIN):
        # query total number of reviews for current product, then query all reviews where the incentivzed score != 0
        reviews = Review.objects.all().filter(asin=productASIN)
        totalReviews = reviews.count()
        
        # search each review for incentivized keywords; incentivizedList is used for review_anomaly
        self.words_re = re.compile("|".join(self.completeKeyPhraseList))
        incentivizedList = [[], []]
        incentivizedReviews = 0
        for review in reviews:
            if self.words_re.search(review.reviewText):
                incentivizedList[0].append(review.unixReviewTime)
                incentivizedList[1].append(True)
                incentivizedReviews += 1

        # calculate incentivized score
        Product.objects.filter(asin=productASIN).update(incentivizedRatio=(incentivizedReviews/totalReviews))

        return incentivizedList
