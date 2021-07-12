import json
import operator
import pandas as pd
import json
import sqlite3
import time
import zlib
import os
import numpy as np
from pandas import read_json
from sqlalchemy import create_engine, exc

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.conf import settings

# Relative Imports
from ...models import User, Product, Review

# Global Directory Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__json_location__ = __current_dir__[:-20] + "/datasets/"
__db_location__ = __current_dir__[:-28] + "/db.sqlite3"

# Global Model Schema Variables
user_columns = ["reviewerID", "reviewerName"]
product_columns = ["asin", "category", "duplicateRatio", "incentivizedRatio", "ratingAnomalyRate", "reviewAnomalyRate"]
review_columns = ["reviewID", "reviewText", "overall", "unixReviewTime", "minHash", "asin", "reviewerID", "duplicate", "incentivized"]



class Command(BaseCommand):
    help = 'Insert data into table'

    def add_arguments(self, parser):
        parser.add_argument('table_name', type=str, help='Indicates the name of the table to insert data into')

    def handle(self, *args, **kwargs):
        table = kwargs['table_name']
        ftd = FileToDatabase()
        ftd.serialize(table)



class FileToDatabase():
    def __init__(self):

        self.engine_connection = create_engine('sqlite:////' + __db_location__, echo=False).connect()                     # can change first param to ':memory:' to store in RAM instead of disk, change echo to echo=True if you want to see description of exporting to sqlite
        
        self.entry_name = ""
        self.table_name = ""



    def serialize(self, table_name):
        self.table_name = table_name

        # parse through every file name in directory 5_core
        entries = os.scandir(__json_location__)
        for entry in entries:
            self.entry_name = entry.name
            print("Process file: " + str(entry.name))  
            if entry.name == '.DS_Store':
                continue

            df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
            serializer = self._get_serializer(table_name)
            df = serializer(df)
            self.df_to_database(table_name, df)
    


    def df_to_database(self, table_name, df):
        # push the data frame to the database
        try:
            df.to_sql(table_name, self.engine_connection, if_exists='append', index=False, method='multi', chunksize=500)                          # use 'append' to keep duplicate reviews
        except exc.IntegrityError as e:
            self.replace(table_name, df)



    # fix pk duplicate errors
    def replace(self, table_name, df):
        print("Initial failure to append:")
        print("Attempting to rectify...")

        # create temp database
        df.to_sql(name='temp_table', con=self.engine_connection, if_exists='append', index=False, method='multi', chunksize=500)

        conn = None
        try:
            conn = sqlite3.connect(__db_location__)
        except Exception as e:
            print(e)
        db_curs = conn.cursor()
        
        # concatenate current table and new data, then drop all duplicates od pk
        try:
            db_curs.execute('INSERT OR IGNORE INTO ' + table_name + ' SELECT * FROM temp_table;')
            db_curs.execute('drop table temp_table')
            conn.commit()
            print("Successful deduplication.")
        except Exception as e:
            print("Could not rectify duplicate entries.")



    # creator component
    def _get_serializer(self, table_name):           
        if table_name == "user":
            return self._serialize_to_user
        elif table_name == "product":
            return self._serialize_to_product
        elif table_name == "review" :
            return self._serialize_to_review
        else:
            raise ValueError("Please enter the name of an existing table in the db.sqlite3 database")



    # serliazes user categories (updates old json format with new attributes needed for the db)
    def _serialize_to_user(self, df):
        # only keep the columns we need according to the schema in user_columns;
        user_info = df.loc[:, user_columns]
        #user_info.dropna(axis=0, how="any", inplace=True)
        user_info.fillna("", inplace=True)
        user_info.drop_duplicates(subset=["reviewerID"], inplace=True)    
        return user_info
    


    # serliazes product categories (updates old json format with new attributes needed for the db)
    def _serialize_to_product(self, df):
        # fill in extra attributes not present in json files 
        df["category"] = self.entry_name[:-7]
        df["duplicateRatio"] = 0.0
        df["incentivizedRatio"] = 0.0
        df["ratingAnomalyRate"] = 0.0
        df["reviewAnomalyRate"] = 0.0

        # only keep the columns we need according to the schema in user_columns;
        df = df.loc[:, product_columns]
        df.drop_duplicates(subset=["asin"], inplace=True)
        return df

    # serliazes review categories (updates old json format with new attributes needed for the db
    def _serialize_to_review(self, df):
        # fill in extra attributes not present in json files 
        df["minHash"] = ""
        df["duplicate"] = 0
        df["incentivized"] = 0
        df = self._add_id(df)

        # only keep the columns we need according to the schema in user_columns;
        
        #df.dropna(axis=0, subset=['reviewerName'], inplace=True)
        print(df)
        #breakpoint()
        df = df.loc[:, review_columns]
        return df


    def _add_id(self, df):
        # default current df's ids to all 0s
        #df["reviewID"] = 0
        
        # find current highest id in table
        existing = pd.read_sql(self.table_name, self.engine_connection)
        low_id = max_id = 0
        if existing.empty:
            low_id = 0
            max_id = len(df)
        else:
            low_id = existing["reviewID"].max() + 1
            max_id = len(df) + low_id

        df['reviewID'] = np.arange(low_id, max_id)

        '''
        # iterate over df and assign ids based on max id value from current table
        for index, row in df.iterrows():
            df.at[index, "reviewID"] = current_max_id + 1
        '''
        return df