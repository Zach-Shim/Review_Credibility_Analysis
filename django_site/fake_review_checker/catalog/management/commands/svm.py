# Python Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.datasets import make_blobs
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms
from .minhash import MinHash



# Used by django admin on the command line: python manage.py logical_regression
class Command(BaseCommand):
    help = 'Use logical regression to determine spam score'

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):
        svm = SVM()
        svm.train()



class SVM():
    def __init__(self):
        self.classifier = None


    # single-variate logistic regression
    def detect(self, product_ASIN):
        # pull unseen data
        data = {'minhash': MinHash.min_hash_asin(product_ASIN)}
        review = (pd.DataFrame(data)).values

        # convert minHash into vector
        vectorizer = CountVectorizer(min_df=0, lowercase=False).fit(reviews)
        x_test = vectorizer.transform(vectorizer).toarray()

        # predict score on new data
        predictions = self.classifier.predict(x_test)

        # check accuracy of prediction on unseen data
        score = self.classifier.score(x_test, y_test)
        print("Accuracy: ", score)
        breakpoint()
        pass



    def train(self):
        # pull test/train data for model
        df = pd.DataFrame(list(Review.objects.values('minHash', 'duplicate')))
        reviews = df['minHash'].values
        duplicates = df['duplicate'].values
        
        # split test and train data
        sentences_train, sentences_test, y_train, y_test = train_test_split(reviews, duplicates, test_size=0.25, random_state=1000)    

        # convert review texts into vectors
        vectorizer = CountVectorizer().fit(sentences_train)
        
        # create sparse matrices
        x_train = vectorizer.transform(sentences_train)
        x_test = vectorizer.transform(sentences_test)

        print(x_train.shape)
        


    def load_training_data(self):
        for review in Review.objects.filter()