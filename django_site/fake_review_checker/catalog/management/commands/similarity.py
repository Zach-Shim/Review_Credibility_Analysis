# Name: Zach Shim & Anusha Prabakaran
# Project Capstone: Product Review Credibility Analysis
# UW
# Detection of duplicate reviews - Inverted Index part for similarity

# Standard library imports
import re
import random
import time
import binascii
import datetime
import csv
import sys
import os
import operator
import sqlite3

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

# Relative Imports
from ...models import User, Product, Review

# Global Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# Used by django admin on the command line: python manage.py similarity
class Command(BaseCommand):
    help = 'Get product similarity scores'

    def handle(self, *args, **kwargs):
        similarity = Similarity()
        similarity.InvertedIndex()
        similarity.CompareHashes()


# Calculates the similarity score for a given Product's Reviews
class Similarity():

    def __init__(self):
        # For each of the 'numHashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.numHashes = 105
        self.reviewCount = 0

        # inverted index
        self.dictList = [dict() for x in range(self.numHashes)]

        # compare hashes
        self.threshold = 0.3

    def InvertedIndex(self):
        for review in Review.objects.all():
            bigram_hash = review.minHash.split(",")
            for i in range(0, self.numHashes):
                key = int(bigram_hash[i])
                self.dictList[i].setdefault(key, [])
                self.dictList[i][key].append(self.reviewCount)         # if there are matching bigram hash code values, append 
            self.reviewCount += 1
            if self.reviewCount % 10000 == 0:
                print("\nLoading " + str(datetime.datetime.now()) + " " + str(self.reviewCount))
                if self.reviewCount > 10000 * 1000:
                    break

    def CompareHashes(self):
        review_num = 0
        for review in Review.objects.all():
            if review_num % 500 == 0:
                print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num))

            # For each review, find the number of keys that match with other reviews in the current table
            matchingKeys = dict()
            signature = review.minHash.split(",")
            for j in range(0, self.numHashes):
                value = self.dictList[j][int(signature[j])]

                # output checks
                if len(value) > 10000:
                    print("Hash " + str(j) + " has " + str(len(value)) + " matches for product " + str(review_num))
                    continue

                for v in value:
                    matchingKeys[v] = matchingKeys.get(v, 0) + 1

            # output checks
            print("\nMatching " + str(datetime.datetime.now()) + " " + str(review_num) + " has " + str(len(matchingKeys)) + "product matches")

            sortedMatchKeys = sorted(matchingKeys.items(), key=operator.itemgetter(1), reverse=True)
            for x in sortedMatchKeys:
                print ("Max hash matches for " + str(review_num) + " is " + str(x[1]))
                estJ = (x[1] / self.numHashes)
                if x[0] == review_num:
                    continue
                if estJ > self.threshold:
                    # push output data to a buffer
                    dup_review = Review.objects.filter(reviewID=x[0]).values('asin')
                    product = Product.objects.filter(asin=dup_review[0]['asin']).update(duplicateRatio=estJ)
                else:
                    break
            review_num += 1
        