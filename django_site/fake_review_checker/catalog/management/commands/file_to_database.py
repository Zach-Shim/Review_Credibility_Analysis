import json
import operator
import pandas as pd
import json
import sqlite3
import time
import zlib
import os
from pandas import read_json
from sqlalchemy import create_engine, exc

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

# Relative Imports
from ...models import User, Product, Review

# Global Directory Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__json_location__ = __current_dir__[:-20] + "/datasets/"
__db_location__ = __current_dir__[:-28] + "/db.sqlite3"

# Global Model Schema Variables
user_columns = ["reviewerID", "reviewerName"]
product_columns = ["asin", "category", "duplicateRatio", "incentivizedRatio", "ratingAnomalyRate", "reviewAnomalyRate"]
review_columns = ["reviewText", "overall", "unixReviewTime", "minHash", "asin", "reviewerID", "duplicate", "incentivized"]



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
        self.engine = create_engine('sqlite:////' + __db_location__, echo=False)                     # can change first param to ':memory:' to store in RAM instead of disk, change echo to echo=True if you want to see description of exporting to sqlite
        self.sqlite_connection = self.engine.connect()                                                    # https://www.fullstackpython.com/blog/export-pandas-dataframes-sqlite-sqlalchemy.html

    def serialize(self, table_name):
        # parse through every file name in directory 5_core
        entries = os.scandir(__json_location__)
        for entry in entries:
            print("Process file: " + str(entry.name))  
            if entry.name == '.DS_Store':
                continue

            df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
            serializer = self._get_serializer(table_name)
            df = serializer(df)

            # Export data frame to sqlite database
            df = df.applymap(str)

            # push the data frame to the database
            try:
                df.to_sql(table_name, self.sqlite_connection, if_exists='append', index=False, method='multi')                          # use 'append' to keep duplicate reviews
            except exc.IntegrityError as e:
                print(str(e))
                pass
    
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
        user_info.dropna(axis=0, how="any", inplace=True)
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

        # only keep the columns we need according to the schema in user_columns;
        df = df.loc[:, review_columns]
        return df

  