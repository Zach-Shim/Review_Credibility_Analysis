# Name: Zach Shim & Anusha Prabakaran
# Project Capstone: Product Review Credibility Analysis
# UW
# Detection of duplicate reviews - Inverted Index part for similarity

# Standard library imports
import datetime
import numpy as np
import operator

# Python Dependency Library Imports
import matplotlib.pyplot as plt, mpld3
import matplotlib
matplotlib.use("TkAgg")

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms



# Used by django admin on the command line: python manage.py similarity
class Command(BaseCommand):
    help = 'Get product similarity scores'
    
    def add_arguments(self, parser):
        parser.add_argument('asin', type=str, nargs='?', help='run similarity on a specific product asin')
        parser.add_argument('-a', '--all', action='store_true', help='Run similarity on all products')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        asin = kwargs['asin']
        similarity = Similarity()

        if kwargs['all']:
            # run on entire database (takes a really long time if database is large because it has to cross check data)
            similarity.detect_all()
        elif kwargs['asin']:
            # run on specific product asin (uncomment this section and commment out above two lines)
            similarity.detect(asin)
            fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
            fig.subplots_adjust(wspace=0.5)
            similarity.plot(ax1)
            plt.show()
        else:
            print("Please enter an asin, or enter the -a command")



# Calculates the similarity score for a given Product's Reviews
class Similarity(DetectionAlgorithms):

    def __init__(self):
        # For each of the 'num_of_hashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.num_of_hashes = 105

        # inverted index
        self.dictList = [dict() for x in range(self.num_of_hashes)]

        # compare hashes
        self.threshold = 0.3

        # invoking the constructor of the parent class  
        graph_info = {"method": "count", "title": "Duplicate Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        super(Similarity, self).__init__(graph_info)  



    # store bigram numHash {index: bigram: review} in dictionary for efficiency
    def invert_index(self):
        review_count = 0
        for review in Review.objects.values('reviewID', 'minHash'):
            bigram_hash = review['minHash'].split(",")
            for i in range(0, self.num_of_hashes):
                key = int(bigram_hash[i])
                self.dictList[i].setdefault(key, [])
                self.dictList[i][key].append(review['reviewID'])         # all reviews that share this key(bigram) are appended to the list
            review_count += 1
            if review_count % 10000 == 0:
                print("\nLoading " + str(datetime.datetime.now()) + " " + str(review_count))
                if review_count > 10000 * 1000:
                    break



    # compares a review's bigram hashes against other review's bigram hashses (takes the cross section of hashes in common)
    def detect_all(self):
        self.invert_index()
        
        queries_to_update = []
        review_num = 0
        for review in Review.objects.values('reviewID', 'minHash'):
            if review_num % 1000 == 0:
                print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num))

            # For the current review, find that number of other reviews that have the same bigrams; every bigram should already be indexed in dictList, holding what reviews have it
            matching_keys = dict()
            signature = review['minHash'].split(",")
            for j in range(0, self.num_of_hashes):
                reviews = self.dictList[j][int(signature[j])]

                # avoid parsing infinitely large number of reviews to save performance
                if len(reviews) > 10000:
                    continue

                # for each review that has this bigram hash, add 1 to their matching key index
                for r in reviews:
                    matching_keys[r] = matching_keys.get(r, 0) + 1

            #print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num) + " has " + str(len(matching_keys)) + "product matches")
            
            sorted_matched_keys = sorted(matching_keys.items(), key=operator.itemgetter(1), reverse=True)
            for x in sorted_matched_keys:
                #print ("Max hash matches for " + str(review_num) + " is " + str(x[1]))
                estJ = (x[1] / self.num_of_hashes)
                if x[0] == review['reviewID']:
                    continue
                if estJ > self.threshold:
                    queries_to_update.append(x[0])
                else:
                    break
            review_num += 1

        print("\nMatching " + str(datetime.datetime.now()) + " finished")
        self._update_db(queries_to_update)



    # accepts a list of reviewID's to update
    def _update_db(self, queries_to_update):
        print("\nPushing to database " + str(datetime.datetime.now()) + " start")
        for review in queries_to_update:
            obj = Review.objects.filter(reviewID=review).update(duplicate=1)
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")



    # used to identify all duplicate reviews for a single product (used dynamically)
    def detect(self, product_ASIN):
        self.product_ASIN = product_ASIN
        duplicates = Review.objects.filter(asin=self.product_ASIN, duplicate=1).count()
        total_reviews = Review.objects.filter(asin=self.product_ASIN).count()
        return self.calculate(duplicates, total_reviews)



    def calculate(self, fake_reviews, total):
        try:
            # calculate similarity score = (total number of similar reviews) / (total number of reviews for asin)
            similarity_score = round(fake_reviews / total * 100, 3)
            Product.objects.filter(asin=self.product_ASIN).update(duplicateRatio=similarity_score)
        except:
            self.error_msg = "Error in calculating similarity score"
            return False
        return True



    def set_info(self):
        super(Similarity, self).set_info(Review.objects.filter(asin=self.product_ASIN, duplicate=1))  