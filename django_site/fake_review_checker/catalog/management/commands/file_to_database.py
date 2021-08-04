# Python Standard Library Imports
import numpy as np
import os
import pandas as pd
from pandas import read_json
import sqlite3
from sqlalchemy import create_engine, exc
import uuid

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Relative Imports
from ...models import User, Product, Review

# Global Directory Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__json_location__ = __current_dir__[:-20] + "/datasets/static_data/"
__db_location__ = __current_dir__[:-28] + "/db.sqlite3"

# Global Model Schema Variables
user_columns = ["reviewerID", "reviewerName"]
product_columns = ["asin", "title", "category", "url", "duplicateRatio", "incentivizedRatio", "ratingAnomalyRate", "reviewAnomalyRate"]
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
            self.entry_name = entry.name[:-7]
            #print("Processing file: " + str(entry.name))  
            if entry.name == '.DS_Store':
                continue

            df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
            serializer = self._get_serializer(table_name)
            df = serializer(df)
            self.df_to_database(table_name, df)
    


    def df_to_database(self, table_name, df):
        print(df)
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
        print("inserting data into user...")
        user_info = df.loc[:, user_columns]
        user_info.fillna("", inplace=True)
        user_info.drop_duplicates(subset=["reviewerID"], inplace=True)    
        return user_info
    


    # serliazes product categories (updates old json format with new attributes needed for the db)
    def _serialize_to_product(self, df):
        # fill in extra attributes not present in json files 
        print("inserting data into product...")
        df["category"] = self.entry_name
        df["url"] = self._add_url(df)
        df["title"] = ""
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
        print("inserting data into review...")
        df["minHash"] = ""
        df["duplicate"] = 0
        df["incentivized"] = 0
        df['reviewID'] = self._add_review_id(df)                       # create unique id's for each review
        
        df = df.loc[:, review_columns]
        return df



    def _add_review_id(self, df):
        # find current highest id in table
        existing = pd.read_sql(self.table_name, self.engine_connection)
        low_id = max_id = 0
        if existing.empty:
            low_id = 0
            max_id = len(df)
        else:
            low_id = existing["reviewID"].max() + 1
            max_id = len(df) + low_id

        return np.arange(low_id, max_id)



    def _add_user_id(self, df):
        print(self.table_name)
        existing = pd.read_sql(self.table_name, self.engine_connection)
        print(existing)
        unique_ids = []
        for reviewer_num in range(0, len(df)):
            # if the randomly generated id exists in the database, then generate new one
            random_id = str(uuid.uuid4())
            duplicate_id = True
            while duplicate_id:
                if existing.empty:
                    if random_id in unique_ids:
                        print("generating new id...")
                        random_id = str(uuid.uuid4())
                    else:
                        duplicate_id = False
                else:
                    if random_id in existing['reviewerID'].values or random_id in unique_ids:
                        print("generating new id...")
                        random_id = str(uuid.uuid4())
                    else:
                        duplicate_id = False
            unique_ids.append(random_id)
      

        return pd.Series(unique_ids) 



    def _add_url(self, df):
        urls = [("https://www.amazon.com/dp/" + str(asin)) for asin in df['asin']]
        return pd.Series(urls)



    def set_table_name(self, table_name):
        self.table_name = table_name
    


    def set_entry_name(self, entry_name):
        self.entry_name = entry_name