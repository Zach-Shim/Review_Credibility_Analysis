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
        rating_anomaly = RatingAnomaly()   
        print(rating_anomaly.detect(asin))

        fig, (ax1) = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        rating_anomaly.plot(ax1)
        plt.show()



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class RatingAnomaly(Anomaly):

    def __init__(self):
        # invoking the constructor of the parent class  
        super(RatingAnomaly, self).__init__({"method": "mean", "title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"})  

    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        Product.objects.filter(asin=self.product_ASIN).update(ratingAnomalyRate=round(fake_reviews / total * 100, 2))

