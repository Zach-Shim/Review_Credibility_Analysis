# Standard library imports
import numpy as np
import pickle
from pprint import pprint
import pandas as pd
import seaborn as sns

# Dependecy packages
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import ShuffleSplit
import matplotlib.pyplot as plt

# Django Imports
from django.contrib.auth.models import User

# Relative Imports
from ..models import User, Product, Review



class RandomForest():
    def __init__(self):
        pass
    
    def detect(self):
        pass

    def train(self):
        # pull test/train data for model
        df = pd.DataFrame(list(Review.objects.values('minHash', 'duplicate')))
        reviews = df['minHash'].values
        duplicates = df['duplicate'].values
        
        # split test and train data
        sentences_train, sentences_test, y_train, y_test = train_test_split(reviews, duplicates, test_size=0.2)    

        # convert review texts into vectors
        vectorizer = TfidfVectorizer().fit(sentences_train)

        # create sparse matrices
        x_train = vectorizer.fit_transform(sentences_train)
        x_test = vectorizer.transform(sentences_test)

        print(x_train)
        print(x_test)
        pass
    


rf = RandomForest()
result = rf.train()