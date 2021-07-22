# Python Imports

# feature selection
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import chi2

# scoring
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt, mpld3
import seaborn as sns

# classifiers
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC

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
        log_regression = LogicalRegression()
        log_regression.all()

        '''
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
        '''

class LogicalRegression():
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



    def binary(self):
        # pull test/train data for model
        df = pd.DataFrame(list(Review.objects.values('minHash', 'duplicate')))
        reviews = df['minHash'].values
        duplicates = df['duplicate'].values
        
        # split test and train data
        sentences_train, sentences_test, y_train, y_test = train_test_split(reviews, duplicates, test_size=0.25, random_state=1000)    

        # convert review texts into vectors
        vectorizer = CountVectorizer().fit(sentences_train)

        # create sparse matrices
        x_train = vectorizer.fit_transform(sentences_train)
        x_test = vectorizer.transform(sentences_test)
        
        # train model
        self.classifier = LogisticRegression(solver='liblinear', C=10.0, random_state=0).fit(x_train, y_train)

        # check accuracy of model
        score = self.classifier.score(x_test, y_test)
        print("Accuracy: ", score)

        conf_matrix = confusion_matrix(y_test, self.classifier.predict(x_test))
        print(conf_matrix)

        print(classification_report(y_test, self.classifier.predict(x_test)))

        return conf_matrix



    def multinomial(self):
        df = pd.DataFrame(Review.objects.values('reviewID', 'reviewText', 'incentivized'))
        reviews = df['reviewText'].values
        duplicates = df['incentivized'].values

        X_train, X_test, y_train, y_test = train_test_split(reviews, duplicates, random_state = 0)

        vectorizer = CountVectorizer()
        X_train_count = vectorizer.fit_transform(X_train)
        X_test_count = vectorizer.transform(X_test)

        transformer = TfidfTransformer()
        X_train_tfidf = transformer.fit_transform(X_train_count)
        X_test_tfidf = transformer.transform(X_test_count)

        clf = MultinomialNB().fit(X_train_tfidf, y_train)

        score = clf.score(X_test_tfidf, y_test)
        print("Accuracy: ", score)

        conf_matrix = confusion_matrix(y_test, clf.predict(X_test_tfidf))
        print(conf_matrix)

        #r_test = vectorizer.transform(["these are good enough to get most motorized vehicles up and running, for semi and farm equipment, get solid copper."])
        #print(clf.predict(r_test))
        

    def all(self):
        df = pd.DataFrame(Review.objects.values('reviewID', 'reviewText', 'incentivized'))
        tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', encoding='latin-1', ngram_range=(1, 2), stop_words='english')
        features = tfidf.fit_transform(df.reviewText).toarray()
        labels = df.reviewID
        print(features.shape)

        models = [
            RandomForestClassifier(n_estimators=200, max_depth=3, random_state=0),
            LinearSVC(),
            MultinomialNB(),
            LogisticRegression(random_state=0),
        ]

        CV = 5
        cv_df = pd.DataFrame(index=range(CV * len(models)))
        entries = []
        for model in models:
            model_name = model.__class__.__name__
            accuracies = cross_val_score(model, features, labels, scoring='accuracy', cv=CV)
            for fold_idx, accuracy in enumerate(accuracies):
                entries.append((model_name, fold_idx, accuracy))
        cv_df = pd.DataFrame(entries, columns=['model_name', 'fold_idx', 'accuracy'])

        # plot data
        sns.boxplot(x='model_name', y='accuracy', data=cv_df)
        sns.stripplot(x='model_name', y='accuracy', data=cv_df, size=8, jitter=True, edgecolor="gray", linewidth=2)
        plt.show()