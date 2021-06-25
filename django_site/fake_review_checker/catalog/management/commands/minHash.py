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



class Command(BaseCommand):
    help = 'Get product similarity scores'

    def handle(self, *args, **kwargs):
        similarity = Similarity()
        similarity.minHash()



class Similarity():

    def __init__(self):
        self.maxShingleID = 2 ** 32 - 1                     # Record the maximum shingle ID that we assigned.
        self.nextPrime = 4294967311                         # Next largest prime number above 'maxShingleID'.

        # For each of the 'numHashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.numHashes = 105
        self.coeffA = self.pickRandomCoeffs(self.numHashes)
        self.coeffB = self.pickRandomCoeffs(self.numHashes)

        # List of documents represented as signature vectors
        self.signatures = []
        self.reviewCount = 0

        

    '''
        Create a list of 'k' random values
    '''
    def pickRandomCoeffs(self, iter):
        randList = []                                                    
        while iter > 0:
            randIndex = random.randint(0, self.maxShingleID)                     # Get a random shingle ID from 0 to (2^32 - 1)
            while randIndex in randList:                                    # Ensure that each random number is unique.
                randIndex = random.randint(0, self.maxShingleID)                 # Add the random number to the list.
            randList.append(randIndex)
            iter = iter - 1

        return randList



    '''
        Hash bigram shingles to a 32-bit integer
    '''
    def find_bigram_crcs(self, input_list):
        bigramCrcs = set()
        for index in range(0, len(input_list) - 1):
            bigram = input_list[index] + " " + input_list[index + 1]            # Construct the shingle text by combining two words together.
            crc = binascii.crc32(bytes(bigram, "utf8")) & 0xffffffff            # Hash bigram to a 32-bit integer.
            bigramCrcs.add(crc)                                                 # Add the hash value of current shingle to the list of shingles for the current document. No duplicate items
        return bigramCrcs



    '''
        create a minHash for all bishingles
    '''
    def minHash(self):
        print("\n" + str(datetime.datetime.now()) + " " + str(self.reviewCount))
        
        # open original json file data
        for review in Review.objects.all():
            reviewText = review.reviewText
            reviewText = reviewText.split()
            biGramCrcs = self.find_bigram_crcs(reviewText) 

            self.reviewCount += 1
            if self.reviewCount % 10000 == 0:
                print("\n" + str(datetime.datetime.now()) + " " + str(self.reviewCount))

            signature = []
            for i in range(0, self.numHashes):
                # Track the lowest hash ID seen. Initialize 'minHashCode' to be greater than the maximum possible value output by the hash.
                minHashCode = self.nextPrime + 1
                for shingleID in biGramCrcs:                                                        # For each bigram in the review..
                    hashCode = (self.coeffA[i] * shingleID + self.coeffB[i]) % self.nextPrime       # For each of the bigrams in the document, calculate its hash code using hash number 'i' in the following hash function
                    if hashCode < minHashCode:                                                      # track the lowest hash ID seen.
                        minHashCode = hashCode
                signature.append(minHashCode)
            self.signatures.append(signature)

            # Join the hash code signautures into one string
            str_sig = ','.join(str(num) for num in signature)

            review.minHash = str_sig
            review.save()
        print("\n" + str(datetime.datetime.now()) + " " + str(self.reviewCount))
