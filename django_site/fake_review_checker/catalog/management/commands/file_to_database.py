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
review_columns = ["reviewerID", "asin", "reviewID", "reviewText", "overall", "unixReviewTime", "minHash", "duplicate"]
user_columns = ["reviewerID", "reviewerName"]
product_columns = ["asin", "category", "duplicateRatio", "incentivizedRatio", "ratingAnomalyRate", "reviewAnomalyRate"]



class Command(BaseCommand):
    help = 'Insert data into table'

    def add_arguments(self, parser):
        parser.add_argument('table_name', type=str, help='Indicates the name of the table to insert data into')

    def handle(self, *args, **kwargs):
        table = kwargs['table_name']
        self.function_factory(table)

    def function_factory(self, table_name):
        ftd = FileToDatabase()
        
        # connect to sqlite database and update dictionary with json_file_name:db_file_connection
        conn = sqlite3.connect(__db_location__)
        
        # parse through every file name in directory 5_core
        entries = os.scandir(__json_location__)
        for entry in entries:
            print(entry.name)
            df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
            if(entry.name == '.DS_Store'):
                continue
            if(table_name == "user"):
                # only keep the columns we need according to the schema in user_columns
                df = df[user_columns]

                # fill in extra attributes not present in json files 
                df.drop_duplicates(subset=["reviewerID"], inplace=True) 
                df.fillna(value="", inplace=True)
                
                # push the data frame to the database
                u_conn = ftd.json_to_database("user", df)
            elif(table_name == "product"):
                # fill in extra attributes not present in json files 
                df["category"] = entry.name[:-7]
                df["duplicateRatio"] = 0.0
                df["incentivizedRatio"] = 0.0
                df["ratingAnomalyRate"] = 0.0
                df["reviewAnomalyRate"] = 0.0
                df = df[product_columns]
                df.drop_duplicates(subset=["asin"], inplace=True) 
                
                # push the data frame to the database
                p_conn = ftd.json_to_database("product", df)   
            elif(table_name == "review"):
                # fill in extra attributes not present in json files 
                ftd.add_id(df)
                df["minHash"] = ""
                df["duplicate"] = 0
                df = df[review_columns]
                r_conn = ftd.json_to_database("review", df)

            else:
                raise ValueError("Please enter the name of an existing table in the db.sqlite3 database")



class FileToDatabase():

    def __init__(self):
        self.data = dict()

    '''
        Description: 
            Converts a json file to a pandas dataframe
            The Review entity is a weak-entity type. It's parents are User and Product
            add_id() gives each Review a unique review_id depending on what Product a User is writing a Review for
        Parameters:
        Returns:
            Dataframe containing json file data
    '''
    def add_id(self, df):
        
        entries = os.scandir(__json_location__)
        for entry in entries:
            for index, row in df.iterrows():
                unique = str(row['reviewerID'] + ', ' + row['asin'])
                if unique in self.data:
                    max_val = max(self.data.items(), key=operator.itemgetter(1))[0]
                    self.data[unique] = self.data[max_val] + 1
                    df.at[index, "reviewID"] = self.data[max_val]
                else:
                    self.data[unique] = 1
                    df.at[index, "reviewID"] = 1
        print(df)

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
        print("Data Framee:")
        print(df)
        print("DB Location:")
        print(__db_location__)

        df = df.applymap(str)
        engine = create_engine('sqlite:////' + __db_location__, echo=False)                     # can change first param to ':memory:' to store in RAM instead of disk, change echo to echo=True if you want to see description of exporting to sqlite
        sqlite_connection = engine.connect()                                                    # https://www.fullstackpython.com/blog/export-pandas-dataframes-sqlite-sqlalchemy.html
        sqlite_table = table_name
        df.to_sql(sqlite_table, sqlite_connection, if_exists='append', index=False)                          # use 'append' to keep duplicate reviews

