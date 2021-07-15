# Python Imports
import matplotlib.pyplot as plt, mpld3
import numpy as np
import sklearn

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms



# Used by django admin on the command line: python manage.py logical_regression
class Command(BaseCommand):
    help = 'Use logical regression to determine spam score'

    def add_arguments(self, parser):
        parser.add_argument('product_ASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        asin = kwargs['asin']
        regression = LogicalRegression()

        # run on specific product asin
        regression.detect(asin)
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        regression.plot(ax1)
        plt.show()

class LogicalRegression(DetectionAlgorithms):
    def __init__(self):
        pass



    def detect(self, product_ASIN):
        pass



    def train(self, product_ASIN):
        sklearn.model_selection.train_test_split(*arrays, **options) 




    def calculate(self, fake_reviews, total):
        pass