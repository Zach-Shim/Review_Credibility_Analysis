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
        similarity.InvertedIndex()
        matchingKeys = similarity.CompareAllHashes()

        similarity.detect("B001LHVOVK")
        similarity.calculate("B001LHVOVK")
        fig, ax1 = plt.subplots(ncols=1, figsize=(11, 7))
        fig.subplots_adjust(wspace=0.4)
        similarity.plot({"figure": fig, "axis": ax1}, "B001LHVOVK")
        fig.show()



# Calculates the similarity score for a given Product's Reviews
class Similarity():

    def __init__(self):
        # For each of the 'numHashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.numHashes = 105
        self.reviewCount = 1
        self.duplicateInfo = dict()

        # inverted index
        self.dictList = [dict() for x in range(self.numHashes)]

        # compare hashes
        self.threshold = 0.3

        # invoking the constructor of the parent class  
        #super(Incentivized, self).__init__()  

    # store bigram numHash {index: bigram: review} in dictionary for efficiency
    def InvertedIndex(self):
        for review in Review.objects.all():
            bigram_hash = review.minHash.split(",")
            for i in range(0, self.numHashes):
                key = int(bigram_hash[i])
                self.dictList[i].setdefault(key, [])
                self.dictList[i][key].append(review)         # all reviews that share this key(bigram) are appended to the list
            self.reviewCount += 1
            if self.reviewCount % 10000 == 0:
                print("\nLoading " + str(datetime.datetime.now()) + " " + str(self.reviewCount))
                if self.reviewCount > 10000 * 1000:
                    break


    # compares each review's bigram hashes against other review's bigram hashses (takes the cross section)
    def CompareAllHashes(self):
        review_num = 1
        for review in Review.objects.all():
            if review_num % 500 == 0:
                print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num))

            # For the current review, find that number of other reviews that have the same bigrams; every bigram should already be indexed in dictList, holding what reviews have it
            matchingKeys = dict()
            signature = review.minHash.split(",")
            for j in range(0, self.numHashes):

                # for each review that has this bigram hash, add 1 to their matching key index
                reviews = self.dictList[j][int(signature[j])]
                for r in reviews:
                    matchingKeys[r] = matchingKeys.get(r, 0) + 1

                # output checks
                if len(reviews) > 10000:
                    #print("Hash " + str(j) + " has " + str(len(reviews)) + " matches for product " + str(review_num))
                    continue

            #print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num) + " has " + str(len(matchingKeys)) + "product matches")

            sortedMatchKeys = sorted(matchingKeys.items(), key=operator.itemgetter(1), reverse=True)
            for x in sortedMatchKeys:
                #print ("Max hash matches for " + str(review_num) + " is " + str(x[1]))
                estJ = (x[1] / self.numHashes)
                if x[0] == review:
                    continue
                if estJ > self.threshold:
                    # duplicate is a bool, so updating to 1 means we are marking this review as a duplicate
                    self.duplicateInfo[review.asin] = [x[0].asin]
                    Review.objects.filter(asin=x[0].asin, reviewerID=x[0].reviewerID).update(duplicate=1)     
                else:
                    break
            review_num += 1



    def detect(self, productASIN):
        return getInfo(productASIN)



    def plot(self, subplot, method, productASIN):
        # Get unixReviewTimes and scores of all fake reviews
        info = self.getInfo(productASIN)
        unixReviewTimes = info["unixReviewTimes"]
        scores = info["scores"]

        # error checking for empty graph
        if (len(unixReviewTimes) == 0 or len(scores) == 0):
            subplot["figure"].delaxes(subplot["axis"])
            return

        # Calculate an even number of bins based on range of unixReviewTimes x months
        self.bins = self.getBins(productASIN)
        self.fakeReviewInfo = info

        self.method = 'count'
        self.graphInfo = {"title": "Duplicate Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        return self.plotAxis(self.bins, subplot, productASIN)


    # retrieve the information of all duplicate reviews for a given asin 
    # method used by views.py - plot()
    def getInfo(self, productASIN):
        duplicateTimeInts = []
        duplicateScores = []

        for review in Review.objects.filter(asin=productASIN, duplicate=1):
            duplicateTimeInts.append(review.unixReviewTime)
            duplicateScores.append(review.overall)

        return {"duplicateTimeInts": duplicateTimeInts, "duplicateScores": duplicateScores}



    # calculates the duplicateRatio = (number of duplicate reviews for a given asin) / (total reviews for a given asin)
    def calculate(self, productASIN):
        duplicates = Review.objects.filter(asin=productASIN, duplicate=1).count()
        totalReviews = Review.objects.filter(asin=productASIN).count()
        duplicateScore = round(duplicates / totalReviews * 100, 2)
        Product.objects.filter(asin=productASIN).update(duplicateRatio=duplicateScore)
        return duplicateScore



    def getBins(self, productASIN):
        reviews = Review.objects.filter(asin=productASIN, duplicate=1)
        return self.getDateRange(reviews)