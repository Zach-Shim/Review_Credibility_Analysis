# Python Imports
from collections import defaultdict
from pyculiarity import detect_ts, detect_vec
import scipy.stats as stats
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms


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
        r_anomaly = Anomaly()   
        print(r_anomaly.detect(asin))

        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        r_anomaly.plot(ax1)
        plt.show()



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self):
        self.rating_value_anomalies = defaultdict(dict)
        self.review_count_anomalies = defaultdict(dict)

        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__({"method": "count", "title": "Review Count Anomalies", "y_axis": "Number of Reviews", "x_axis": "Time"})



    # returns reviews in bins of 30-day time series
    def detect(self, product_ASIN):
        self.product_ASIN = product_ASIN
        self.set_info()
        review_val = self.detect_review_anomalies()
        #rating_val = self.detect_rating_anomalies()
        #return [review_val, rating_val]
        return review_val



    def detect_review_anomalies(self):
        # Calculate an even number of bins based on range of unix_review_times x months        
        #self.graph_info = {"method": "count", "title": "Review Count Anomalies"}
        self.series = self.generate_frame()
        #print(self.series)

        # calculate anomalies in rating value distribution
        try:
            self.review_count_anomalies = detect_ts(self.series, max_anoms=0.02, direction='both')
            print("here")
            print(self.review_count_anomalies)
        except:
            print("here2")
            self.review_count_anomalies['anoms']['anoms'] = []

        print(str(len(self.review_count_anomalies['anoms']['anoms'])))
        return self.calculate(len(self.review_count_anomalies['anoms']['anoms']), Review.objects.filter(asin=self.product_ASIN).count())



    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        anomaly_score = round(fake_reviews / total * 100, 2)
        Product.objects.filter(asin=self.product_ASIN).update(reviewAnomalyRate=anomaly_score)
        return anomaly_score
    

    def set_info(self):
        super(Anomaly, self).set_info(Review.objects.filter(asin=self.product_ASIN)) 