# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review
from .detection_algorithms import DetectionAlgorithms
from .minhash import MinHash



# Used by django admin on the command line: python manage.py logistic_regression
class Command(BaseCommand):
    help = 'Use logistic regression to determine spam score'

    def add_arguments(self, parser):
        parser.add_argument('asin', type=str, nargs='?', help='run similarity on a specific product asin')
        parser.add_argument('-a', '--all', action='store_true', help='Run similarity on all products')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        asin = kwargs['asin']
        lsi_model = LSI()
        lsi_model.train()
        lsi_model.detect(asin)

        '''
        if kwargs['all']:
            # cross validate
            log_regression.all()
        elif kwargs['asin']:        
            # run on specific product asin
            cm = log_regression.binary()
            log_regression.detect(asin)
        else:
            raise ValueError("Please enter the command -a or an asin")
        '''
        '''
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



# natural language processing imports
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer

def naturalize(review_text):      
    # get rid of punctutaion and isolate individual words
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    review_words = tokenizer.tokenize(review_text)

    # lemmatize the words to obtain core meaning (lemma -> "blend" vs. lexeme -> "blending") (lemma = word that represents a group of words)
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word.casefold()) for word in review_words]

    return lemmatized_words



'''
    Iterator class
'''
class MyDictionary():        
    def __iter__(self):
        # proprocess document corpus through tokenization, naturalization, and lemmatization
        for review in Review.objects.values('reviewText'):
            yield naturalize(review['reviewText'])



'''
    Iterator class
'''
class MyCorpus:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.corpus_iter = MyDictionary()
        
    def __iter__(self):
        for review in self.corpus_iter:
            yield self.dictionary.doc2bow(review)



# feature selection
from collections import defaultdict
import logging
import numpy as np
import os
import pandas as pd
from smart_open import open

# similarity detection model and vectors
from gensim.corpora import Dictionary
from gensim import corpora
from gensim import models
from gensim import similarities
from gensim.test.utils import get_tmpfile

# save training data and models
__keywords_path__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))[:-20] + "/datasets/dynamic_data/keywords.dict"
__bow_corpus_path__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))[:-20] + "/datasets/dynamic_data/bow_corpus.mm"
__lsi_model_path__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))[:-20] + "/datasets/dynamic_data/lsi_model.lsi"
__lsi_corpus_path__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))[:-20] + "/datasets/dynamic_data/lsi_corpus.lsi"
__sim_index_path__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))[:-20] + "/datasets/dynamic_data/similarity.index"

'''
    Iterator class
'''
class LSI():
    def detect(self, product_ASIN):
        # query_documents = ["Use a binary tree data structure to solve this graph algorithm", "Human computer interaction"]
        # if number of documents (reviews) is less than some threshold (lets say, 5 reviews), return an error message
        query_documents = Review.objects.filter(asin=product_ASIN)
        if query_documents.count() < 5:
            # if the length of the 'documents' list is less than 1, the algorithm will not work
            return "Cannot analyze product due to lack of reviews"
        else:
            query_documents = query_documents.values('reviewText')    

        # preprcoess text 
        texts = [naturalize(text['reviewText']) for text in query_documents]        # sanization, lemmatization, tokenization
        loaded_dictionary = corpora.Dictionary.load(__keywords_path__)              # create vocabulary from tokenized reviews
        query_corpus = [loaded_dictionary.doc2bow(text) for text in texts]          # convert original tokenized reviews to numbered vectors (bag-of-words representation = count of each word); the dictionary is of the form {word: number of occurences in the corpus}

        # transform vector spaces and train tfidf model using bow vector data 
        model = models.TfidfModel(query_corpus)
        tfidf_corpus = model[query_corpus]

        # chain transformations - train lsi model using tfidf vector data (this allows online training)
        loaded_lsi_model = models.LsiModel.load(__lsi_model_path__)
        query_lsi = loaded_lsi_model[tfidf_corpus]

        '''
        # test output
        documents = Review.objects.values('reviewText')
        for doc, as_text in zip(query_lsi, query_documents):
            print(doc, as_text, '\n')
            # perform a similarity query against indexed data with new documents
            loaded_index = similarities.Similarity.load(__sim_index_path__)
            sims = loaded_index[doc]

            x = 5
            for document_number, score in sorted(enumerate(sims), key=lambda x: x[1], reverse=True):
                if x > 0:
                    print(document_number, score, documents[document_number]['reviewText'][10:])
                    x -= 1
                else:
                    print()
                    break
        '''

        # update dictionary
        loaded_dictionary.add_documents(texts)
        loaded_dictionary.save(__keywords_path__)

        # update lsi model (note: we are able to update the model with a new corpus, but are unable to update the dictionary vocabulary for the model, doing so would require retraining)
        loaded_lsi_model.add_documents(corpus=query_lsi, chunksize=500)
        loaded_lsi_model.save(__lsi_model_path__)
        


    def train(self):
        # make bag-of-words dictionary (id: word) and save to disk
        processed_corpus = MyDictionary()
        dictionary = corpora.Dictionary(document for document in processed_corpus)
        dictionary.save(__keywords_path__)                                      

        # create document vectors based on dictionary (based on bag-of-words represetnation; each document is a list of (wordID: # of word occurences))
        vector_corpus = MyCorpus(dictionary)
        bow_corpus = [vector for vector in vector_corpus]                       # iterate over corpus (load one review into memory at a time to save RAM)
        corpora.MmCorpus.serialize(__bow_corpus_path__, bow_corpus)   

        # transform vector spaces and train tfidf model using bow vector data 
        tfidf = models.TfidfModel(bow_corpus)
        corpus_tfidf = tfidf[bow_corpus]
        
        # chain transformations - train lsi model using tfidf vector data (this allows online training)
        lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=90)
        lsi.save(__lsi_model_path__)

        corpus_lsi = lsi[corpus_tfidf]
        corpora.MmCorpus.serialize(__lsi_corpus_path__, corpus_lsi)
        
        # enter all documents (enter a corpus) which we want to compare against subsequent similarity queries
        index = similarities.Similarity(__sim_index_path__, corpus=corpus_lsi, num_features=(len(dictionary.dfs)))  
        index.save(__sim_index_path__)