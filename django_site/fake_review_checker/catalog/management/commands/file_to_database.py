import json
import operator
import pandas as pd
import json
import sqlite3
import time
import zlib
import os
from pandas import read_json
from sqlalchemy import create_engine

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
        self.entry_name = ""

    def serialize(self, table_name):
        # parse through every file name in directory 5_core
        entries = os.scandir(__json_location__)

        for entry in entries:
            self.entry_name = entry.name
            print("Process file: " + str(self.entry_name))  
            if entry.name == '.DS_Store':
                continue

            df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
            serializer = self._get_serializer(table_name)
            df = serializer(df)

            # push the data frame to the database
            u_conn = self.json_to_database(table_name, df)
            
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
        # only keep the columns we need according to the schema in user_columns; fill in extra attributes not present in json files 
        df = df[user_columns]
        df.drop_duplicates(subset=["reviewerID"], inplace=True) 
        df.fillna(value="", inplace=True)
        return df
    
    # serliazes product categories (updates old json format with new attributes needed for the db)
    def _serialize_to_product(self, df):
        # fill in extra attributes not present in json files 
        df["category"] = self.entry_name[:-7]
        df["duplicateRatio"] = 0.0
        df["incentivizedRatio"] = 0.0
        df["ratingAnomalyRate"] = 0.0
        df["reviewAnomalyRate"] = 0.0
        df = df[product_columns]
        df.drop_duplicates(subset=["asin"], inplace=True)
        return df

    # serliazes review categories (updates old json format with new attributes needed for the db
    def _serialize_to_review(self, df):
        # fill in extra attributes not present in json files 
        df["minHash"] = ""
        df["duplicate"] = 0
        df["incentivized"] = 0
        df = df[review_columns]
        return df

    '''
    Description:
        Export a json file to a sqlite3 db
    Parameters:
        path: absolute path of db file
    Return:
        None
    '''
    def json_to_database(self, table_name, df):    
        # Export data frame to sqlite database
        print("Data Frame:")
        print(df)
        print("DB Location:")
        print(__db_location__)

        df = df.applymap(str)
        engine = create_engine('sqlite:////' + __db_location__, echo=False)                     # can change first param to ':memory:' to store in RAM instead of disk, change echo to echo=True if you want to see description of exporting to sqlite
        sqlite_connection = engine.connect()                                                    # https://www.fullstackpython.com/blog/export-pandas-dataframes-sqlite-sqlalchemy.html
        sqlite_table = table_name
        df.to_sql(sqlite_table, sqlite_connection, if_exists='append', index=False)                          # use 'append' to keep duplicate reviews

