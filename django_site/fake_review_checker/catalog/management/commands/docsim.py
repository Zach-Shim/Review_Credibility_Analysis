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
        parser.add_argument('-t', '--train', action='store_true', help='Train models for similarity on static dataset')
        parser.add_argument('-d', '--detect', action='store_true', help='Compare similarity of reviews in the database to newly scraped reviews')

    # args holds number of args, kwargs is dict of args
    def handle(self, *args, **kwargs):        
        asin = kwargs['asin']
        similarity = DocSim()

        if kwargs['train']:
            similarity.train()
        elif kwargs['detect']:
            print(similarity.detect(asin))
        else:
            raise ValueError("Please enter the command -a or an asin")
        
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
import datetime
import logging
import numpy as np
from os.path import dirname, abspath
import pandas as pd
from smart_open import open

# similarity detection model and vectors
from gensim.corpora import Dictionary
from gensim import corpora
from gensim import models
from gensim import similarities
from gensim.test.utils import get_tmpfile

# save training data and models
__keywords_path__ = dirname(dirname(dirname(abspath(__file__)))) + "/datasets/dynamic_data/keywords.dict"
__bow_corpus_path__ = dirname(dirname(dirname(abspath(__file__)))) + "/datasets/dynamic_data/bow_corpus.mm"
__lsi_model_path__ = dirname(dirname(dirname(abspath(__file__)))) + "/datasets/dynamic_data/lsi_model.lsi"
__lsi_corpus_path__ = dirname(dirname(dirname(abspath(__file__)))) + "/datasets/dynamic_data/lsi_corpus.lsi"
__sim_index_path__ = dirname(dirname(dirname(abspath(__file__)))) + "/datasets/dynamic_data/similarity.index"

'''
    Iterator class
'''
class DocSim(DetectionAlgorithms):
    def __init__(self):
        self.error_msg = ""
        self.product_ASIN = ""

        # invoking the constructor of the parent class  
        graph_info = {"method": "count", "title": "Duplicate Review Counts", "y_axis": "Number of Reviews", "x_axis": "Time"}
        super(DocSim, self).__init__(graph_info)  



    def detect(self, product_ASIN):
        # query_documents = ["Use a binary tree data structure to solve this graph algorithm", "Human computer interaction"]
        # if number of documents (reviews) is less than some threshold (lets say, 5 reviews), return an error message
        query_documents = Review.objects.filter(asin=product_ASIN).values('reviewID', 'reviewText')    
        if query_documents.count() < 5:
            # if the length of the 'documents' list is less than 1, the algorithm will not work
            self.error_msg = "Cannot analyze product due to lack of reviews"
            return False

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

        # perform a similarity query against indexed data with new documents
        loaded_index = similarities.Similarity.load(__sim_index_path__)

        print("Finding similar reviews with a threshold 80 percent similarity\n")
        duplicate_indexes = set()
        current_length = 0
        duplicates_in_category = 0

        for doc in query_lsi:
            sims = loaded_index[doc]
            for document_number, score in sorted(enumerate(sims), key=lambda x: x[1], reverse=True):
                if score > 0.9:
                    current_length += 1
                    print(document_number, score) #query_documents[document_number]['reviewText'][10:]
                    duplicate_indexes.add(document_number)
                else:
                    print("Finished processing\n")
                    break
            
            if current_length > 0:
                duplicates_in_category += 1
            current_length = 0

        #print(duplicate_indexes)
        print("\nPushing to database " + str(datetime.datetime.now()) + " start")
        queries_to_update = []
        for index in duplicate_indexes:
            review = Review.objects.get(reviewID=int(index))
            review.duplicate = 1
            queries_to_update.append(review)
        Review.objects.bulk_update(queries_to_update, ['duplicate'], batch_size=300)
        print("\nPushing to database " + str(datetime.datetime.now()) + " finish")

        # update dictionary
        loaded_dictionary.add_documents(texts)
        loaded_dictionary.save(__keywords_path__)

        # update lsi model (note: we are able to update the model with a new corpus, but are unable to update the dictionary vocabulary for the model, doing so would require retraining)
        loaded_lsi_model.add_documents(corpus=query_lsi, chunksize=500)
        loaded_lsi_model.save(__lsi_model_path__)
        
        self.product_ASIN = product_ASIN
        self.calculate(Review.objects.filter(asin=product_ASIN, duplicate=1).count(), Review.objects.filter(asin=product_ASIN).count())
        return len(queries_to_update)
        


    def calculate(self, fake_reviews, total):
        # calculate similarity score = (total number of similar reviews) / (total number of reviews for asin)
        similarity_score = round(fake_reviews / total * 100, 2)
        print('similarity_score ', similarity_score)
        Product.objects.filter(asin=self.product_ASIN).update(duplicateRatio=similarity_score)



    def train(self):
        print("Start " + str(datetime.datetime.now()))
        # make bag-of-words dictionary (id: word) and save to disk
        #processed_corpus = MyDictionary()
        document = "I have purchased this product several times. It is really high quality and will still be good after many uses."
        processed_corpus = [naturalize(document)]
        dictionary = corpora.Dictionary(document for document in processed_corpus)
        print(dictionary)
        breakpoint()
        dictionary.save(__keywords_path__)                                      

        # create document vectors based on dictionary (based on bag-of-words represetnation; each document is a list of (wordID: # of word occurences))
        print("Creating dictionary... " + str(datetime.datetime.now()))
        vector_corpus = MyCorpus(dictionary)
        bow_corpus = [vector for vector in vector_corpus]                       # iterate over corpus (load one review into memory at a time to save RAM)
        #corpora.MmCorpus.serialize(__bow_corpus_path__, bow_corpus)   

        # transform vector spaces and train tfidf model using bow vector data 
        print("Processing bow vectors -> tfidf vectors... " + str(datetime.datetime.now()))
        tfidf = models.TfidfModel(bow_corpus)
        corpus_tfidf = tfidf[bow_corpus]
        
        # chain transformations - train lsi model using tfidf vector data (this allows online training)
        print("Processing tfidf vectors -> lsi vectors... " + str(datetime.datetime.now()))
        lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=90)
        corpus_lsi = lsi[corpus_tfidf]
        lsi.save(__lsi_model_path__)

        #corpus_lsi = lsi[corpus_tfidf]
        #corpora.MmCorpus.serialize(__lsi_corpus_path__, corpus_lsi)
        
        # enter all documents (enter a corpus) which we want to compare against subsequent similarity queries
        print("Training similiarity model... " + str(datetime.datetime.now()))
        index = similarities.Similarity(__sim_index_path__, corpus=corpus_lsi, num_features=(len(dictionary.dfs)))  
        index.save(__sim_index_path__)
        print("End " + str(datetime.datetime.now()))



    def get_error(self):
        return self.error_msg