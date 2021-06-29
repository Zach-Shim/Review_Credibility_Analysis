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
        self.max_shingle_id = 2 ** 32 - 1                     # Record the maximum shingle ID that we assigned.
        self.next_prime = 4294967311                         # Next largest prime number above 'max_shingle_id'.

        # For each of the 'num_of_hashes' hash functions, generate a different coefficient 'a' and 'b'.
        self.num_of_hashes = 105
        self.coeff_a = self.generate_random(self.num_of_hashes)
        self.coeff_b = self.generate_random(self.num_of_hashes)

        # List of documents represented as signature vectors
        self.signatures = []

        

    '''
        Create a list of 'k' random values
    '''
    def generate_random(self, count):
        randList = []                                                    
        while count > 0:
            random_index = random.randint(0, self.max_shingle_id)                     # Get a random shingle ID from 0 to (2^32 - 1)
            while random_index in randList:                                    # Ensure that each random number is unique.
                random_index = random.randint(0, self.max_shingle_id)                 # Add the random number to the list.
            randList.append(random_index)
            count = count - 1

        return randList



    '''
        Hash bigram shingles to a 32-bit integer
    '''
    def find_bigram_crcs(self, input_list):
        bigram_crcs = set()
        for index in range(0, len(input_list) - 1):
            bigram = input_list[index] + " " + input_list[index + 1]            # Construct the shingle text by combining two words together.
            crc = binascii.crc32(bytes(bigram, "utf8")) & 0xffffffff            # Hash bigram to a 32-bit integer.
            bigram_crcs.add(crc)                                                 # Add the hash value of current shingle to the list of shingles for the current document. No duplicate items
        return bigram_crcs



    '''
        create a minHash for all bishingles
    '''
    def minHash(self):
        review_count = 0
        print("\n" + str(datetime.datetime.now()) + " " + str(review_count))
        
        # open original json file data
        queries_to_update = []
        for review in Review.objects.all():
            review_text = review.reviewText.split()
            bigram_crcs = self.find_bigram_crcs(review_text) 

            review_count += 1
            if review_count % 1000 == 0:
                print("\n" + str(datetime.datetime.now()) + " " + str(review_count))

            signature = []
            for i in range(0, self.num_of_hashes):
                # Track the lowest hash ID seen. Initialize 'minhash_code' to be greater than the maximum possible value output by the hash.
                minhash_code = self.next_prime + 1
                for shingle_id in bigram_crcs:                                                        # For each bigram in the review..
                    hash_code = (self.coeff_a[i] * shingle_id + self.coeff_b[i]) % self.next_prime       # For each of the bigrams in the document, calculate its hash code using hash number 'i' in the following hash function
                    if hash_code < minhash_code:                                                      # track the lowest hash ID seen.
                        minhash_code = hash_code
                signature.append(minhash_code)
            self.signatures.append(signature)

            # Join the hash code signautures into one string
            str_sig = ','.join(str(num) for num in signature)

            review.minHash = str_sig
            queries_to_update.append(review)

        Review.objects.bulk_update(queries_to_update, ['minHash'])
        print("\n" + str(datetime.datetime.now()) + " " + str(review_count))
