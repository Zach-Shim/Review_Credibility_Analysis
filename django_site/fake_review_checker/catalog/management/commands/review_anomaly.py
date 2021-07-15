# Python Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import scipy.stats as stats

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .anomaly import Anomaly


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
        parser.add_argument('product_ASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = kwargs['product_ASIN']
        rev_anomaly = ReviewAnomaly()   
        print(rev_anomaly.detect(asin))

        fig, (ax1) = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        rev_anomaly.plot(ax1)
        plt.show()



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class ReviewAnomaly(Anomaly):

    def __init__(self):
        review_anomalies = []

        # invoking the constructor of the parent class  
        super(ReviewAnomaly, self).__init__({"method": "count", "title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"})  

    def detect(self, product_ASIN):
        self.review_anomalies = self.detect_anomalies(product_ASIN)
        return self.calculate(self.review_anomalies, Review.objects.filter(asin=self.product_ASIN).count())

    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        anomaly_rate = round(fake_reviews / total * 100, 2)
        Product.objects.filter(asin=self.product_ASIN).update(reviewAnomalyRate=anomaly_rate)
        return anomaly_rate


