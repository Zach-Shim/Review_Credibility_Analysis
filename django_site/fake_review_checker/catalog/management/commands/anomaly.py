# Python Imports
from collections import defaultdict
from pyculiarity import detect_ts, detect_vec
import numpy as np
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
        Also used as terminal command: python manage.py anomaly (asin)
    Parameters:
        A valid product ASIN given as input in the command line
'''
class Command(BaseCommand):
    help = 'Get product review anomaly scores'

    # adds an argument to **kwards in the handle function
    def add_arguments(self, parser):
        parser.add_argument('asin', type=str, nargs='?', help='Indicates the asin of the product we are currently analyzing')
        parser.add_argument('-rating', '--rating', action='store_true', help='Calculate anomalies from ratings')
        parser.add_argument('-review', '--review', action='store_true', help='Calculate anomalies from reviews')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        asin = ''
        if kwargs['asin']:
            asin = kwargs['asin']
        else:
            raise ValueError("Please enter an asin.")

        if kwargs['rating']:
            rating_anomaly = RatingAnomaly()   
            print(rating_anomaly.detect(asin))
        elif kwargs['review']:
            review_anomaly = ReviewAnomaly()
            print(review_anomaly.detect(asin)) 

        fig, (ax1) = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.5)
        rating_anomaly.plot(ax1)
        #plt.show()



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class Anomaly(DetectionAlgorithms):

    def __init__(self, graph_info):
        # invoking the constructor of the parent class  
        super(Anomaly, self).__init__(graph_info)  



    # returns reviews in bins of 30-day time series
    def detect_anomalies(self, product_ASIN):
        self.product_ASIN = product_ASIN
        self.set_info()

        # Calculate an even number of bins based on range of unix_review_times x months
        self.series = self.generate_frame()
        #print(self.series)

        # convert timestamp to unix timestamp integer
        self.series['timestamp'] = self.series['timestamp'].astype(np.int64) 

        # calculate anomalies in rating value distribution
        detected_anomalies = defaultdict(dict)
        try:
            detected_anomalies = detect_ts(self.series, max_anoms=0.02, alpha=0.001, direction='both')
        except Exception as e:
            detected_anomalies['anoms']['anoms'] = []
        
        # format the unix timestamp integer back to datetime
        self.series['timestamp'] = pd.to_datetime(self.series['timestamp'])
        
        # return number of anomalies
        return len(detected_anomalies['anoms']['anoms'])



    # overloaded plot method, because we had to build the dataframes in detect in order to analyze the data (so no need to do it again)
    def plot(self, subplot):
        if self.empty_graph(subplot):
            return
        self.plot_frame(subplot, self.series)



    def set_info(self):
        # query sets of review data for histogram bins
        reviews = Review.objects.filter(asin=self.product_ASIN)
        review_times_int = [review['unixReviewTime'] for review in reviews.values('unixReviewTime').order_by('unixReviewTime')]
        review_scores = [review['overall'] for review in reviews.values('overall').order_by('unixReviewTime')]
        self.fake_review_info = {"review_times": review_times_int, "review_scores": review_scores}



    def get_rating_color(self):
        num_of_anoms = len(self.rating_value_anomalies['anoms']['anoms'])
        return check_length(num_of_anoms)



    def get_review_color(self):
        num_of_anoms = len(self.review_count_anomalies['anoms']['anoms'])
        return check_length(num_of_anoms)
    


    def check_length(self, num_of_anoms):
        if num_of_anoms == 0:
            return "green"
        elif num_of_anoms == 1:
            return "orange"
        elif num_of_anoms > 1:
            return "red"



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class RatingAnomaly(Anomaly):

    def __init__(self):
        rating_anomalies = 0

        # invoking the constructor of the parent class  
        super(RatingAnomaly, self).__init__({"method": "mean", "title": "Average Rating Anomalies", "y_axis": "Rating Value", "x_axis": "Time"})  

    def detect(self, product_ASIN):
        self.rating_anomalies = self.detect_anomalies(product_ASIN)
        return self.calculate(self.rating_anomalies, Review.objects.filter(asin=self.product_ASIN).count())

    # accepts total number of anomalies and total number of anomalies (anomaly score = number of anomalies / total number of reviews)
    def calculate(self, fake_reviews, total):
        anomaly_rate = round(fake_reviews / total * 100, 2)
        Product.objects.filter(asin=self.product_ASIN).update(ratingAnomalyRate=anomaly_rate)
        return anomaly_rate



'''
    Description:
        Used by the results() view in views.py to dynamically calculate a new review's review and rating anomaly score
    Parameters:
        A valid product ASIN
'''
class ReviewAnomaly(Anomaly):

    def __init__(self):
        review_anomalies = 0

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

