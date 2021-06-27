# Name: Zach Shim & Anusha Prabakaran
# Project Capstone: Product Review Credibility Analysis
# UW
# Detection of duplicate reviews - Inverted Index part for similarity

# Standard library imports
import datetime
import math
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import operator
import sys

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.db.models import Max, Min, Avg

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms



# Used by django admin on the command line: python manage.py similarity
class Command(BaseCommand):
    help = 'Get product similarity scores'
    
    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        similarity = Similarity()
        similarity.invert_index()
        matching_keys = similarity.compare_all_hashes()

        '''
        similarity.detect("B001LHVOVK")
        similarity.calculate("B001LHVOVK")
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        similarity.plot({"figure": fig, "axis": ax1}, "B001LHVOVK")
        fig.show()
        '''



# Calculates the similarity score for a given Product's Reviews
class Similarity(DetectionAlgorithms):

    def __init__(self):
        # For each of the 'num_of_hashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.num_of_hashes = 105

        # plotting info
        self.duplicate_review_times = []
        self.duplicate_scores = []

        # inverted index
        self.dictList = [dict() for x in range(self.num_of_hashes)]

        # compare hashes
        self.threshold = 0.3

        # invoking the constructor of the parent class  
        method = 'count'
        graph_info = {"title": "Duplicate Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        super(Similarity, self).__init__(method, graph_info)  



    # store bigram numHash {index: bigram: review} in dictionary for efficiency
    def invert_index(self):
        review_count = 0
        for review in Review.objects.values('id', 'minHash'):
            bigram_hash = review['minHash'].split(",")
            for i in range(0, self.num_of_hashes):
                key = int(bigram_hash[i])
                self.dictList[i].setdefault(key, [])
                self.dictList[i][key].append(review['id'])         # all reviews that share this key(bigram) are appended to the list
            review_count += 1
            if review_count % 10000 == 0:
                print("\nLoading " + str(datetime.datetime.now()) + " " + str(review_count))
                if review_count > 10000 * 1000:
                    break


    # compares each review's bigram hashes against other review's bigram hashses (takes the cross section)
    def compare_all_hashes(self):
        review_num = 1
        queries_to_update = []
        for review in Review.objects.values('id', 'minHash'):
            if review_num % 1000 == 0:
                print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num))

            # For the current review, find that number of other reviews that have the same bigrams; every bigram should already be indexed in dictList, holding what reviews have it
            matching_keys = dict()
            signature = review['minHash'].split(",")
            for j in range(0, self.num_of_hashes):

                # for each review that has this bigram hash, add 1 to their matching key index
                reviews = self.dictList[j][int(signature[j])]
                for r in reviews:
                    matching_keys[r] = matching_keys.get(r, 0) + 1

                # output checks
                if len(reviews) > 10000:
                    #print("Hash " + str(j) + " has " + str(len(reviews)) + " matches for product " + str(review_num))
                    continue

            #print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num) + " has " + str(len(matching_keys)) + "product matches")

            sorted_matched_keys = sorted(matching_keys.items(), key=operator.itemgetter(1), reverse=True)
            for x in sorted_matched_keys:
                #print ("Max hash matches for " + str(review_num) + " is " + str(x[1]))
                estJ = (x[1] / self.num_of_hashes)
                if x[0] == review['id']:
                    continue
                if estJ > self.threshold:
                    queries_to_update.append(x[0])
                else:
                    break
            review_num += 1
        print("\nMatching " + str(datetime.datetime.now()) + " finished")

        self._update_db(queries_to_update)



    # accepts a list of review id's to update
    def _update_db(self, queries_to_update):
        print("\nPushing to database " + str(datetime.datetime.now()) + " start")
        for review in queries_to_update:
            obj = Review.objects.filter(id=review).values('unixReviewTime', 'overall')
            print(obj)
            self.duplicate_review_times.append(obj[0]['unixReviewTime'])
            self.duplicate_scores.append(obj[0]['overall'])
            obj.update(duplicate=1)
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")



    def detect(self, product_ASIN):
        return self.calculate(product_ASIN)



    def plot(self, subplot, method, product_ASIN):
        # Get unixReviewTimes and scores of all fake reviews
        self.set_bins(product_ASIN)
        self.set_info()
        if not self.empty_graph():
            return

        self.generate_frame('similarity')
        return self.plot_axes(self.bins, subplot)



    # calculates the duplicateRatio = (number of duplicate reviews for a given asin) / (total reviews for a given asin)
    def calculate(self, product_ASIN):
        duplicates = Review.objects.filter(asin=product_ASIN, duplicate=1).count()
        total_reviews = Review.objects.filter(asin=product_ASIN).count()
        dup_score = round(duplicates / total_reviews * 100, 2)
        Product.objects.filter(asin=product_ASIN).update(duplicateRatio=dup_score)
        return dup_score



    # retrieve the information of all duplicate reviews for a given asin 
    # method used by views.py - plot()
    def set_info(self):
        self.fake_review_info = {"review_times": duplicate_review_times, "scores": duplicate_scores}



    # Calculate an even number of bins based on range of unixReviewTimes x months
    def set_bins(self, product_ASIN):
        reviews = Review.objects.filter(asin=product_ASIN, duplicate=1)
        return self.get_date_range(reviews)