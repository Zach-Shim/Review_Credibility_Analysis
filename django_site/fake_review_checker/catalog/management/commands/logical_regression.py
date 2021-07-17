# Python Imports
import matplotlib.pyplot as plt, mpld3
import numpy as np
import pandas as pd

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

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

    def add_arguments(self, parser):
        parser.add_argument('product_ASIN', type=str, help='Indicates the asin of the product we are currently analyzing')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        asin = kwargs['product_ASIN']
        regression = LogicalRegression()

        # run on specific product asin
        cm = regression.train()
        #regression.detect(asin)

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(cm)
        ax.grid(False)
        ax.xaxis.set(ticks=(0, 1), ticklabels=('Predicted 0s', 'Predicted 1s'))
        ax.yaxis.set(ticks=(0, 1), ticklabels=('Actual 0s', 'Actual 1s'))
        ax.set_ylim(1.5, -0.5)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, cm[i, j], ha='center', va='center', color='darkred')

        plt.show()


class LogicalRegression(DetectionAlgorithms):
    def __init__(self):
        self.classifier = None
        pass


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
        
        # train model
        self.classifier = LogisticRegression(solver='liblinear', C=10.0, random_state=0).fit(x_train, y_train)

        # check accuracy of model
        score = self.classifier.score(x_test, y_test)
        print("Accuracy: ", score)

        conf_matrix = confusion_matrix(y_test, self.classifier.predict(x_test))
        print(conf_matrix)

        return conf_matrix



    def calculate(self, fake_reviews, total):
        pass