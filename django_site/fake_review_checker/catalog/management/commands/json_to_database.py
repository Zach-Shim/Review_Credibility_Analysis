import csv
import pandas as pd
import json
import sqlite3
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
__json_location__ = __current_dir__ + "/Datasets/"
__db_location__ = __current_dir__[:-8] + "/db.sqlite3"

# Global Model Schema Variables
review_columns = ["reviewerID", "asin", "reviewID", "reviewText", "overall", "unixReviewTime", "minHash"]
user_columns = ["reviewerID", "reviewerName"]
product_columns = ["asin", "category", "duplicateRatio", "incentivizedRatio", "ratingAnomalyRate", "reviewAnomalyRate"]



class Command(BaseCommand):
    help = 'Insert data into table'

    def add_arguments(self, parser):
        parser.add_argument('table_name', type=str, help='Indicates the name of the table to insert data into')

    def handle(self, *args, **kwargs):
        table = kwargs['table_name']
        function_factory(table)

    def function_factory(self, table_name):
        if(table_name == "user"):
            u_conn = json_to_database("user", user_columns, __json_location__, __db_location__)
        elif(table_name == "product"):
            p_conn = json_to_database("product", product_columns, __json_location__, __db_location__)
        elif(table_name == "review"):
            r_conn = json_to_database("review", review_columns, __json_location__, __db_location__)
        else:
            raise ValueError("Please enter the name of an existing table in the db.sqlite3 database")



'''
    https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do
'''
def parse2(path):
    g = open(path, 'r')
    for l in g:
        yield eval(l)



'''
Description:
    Query all rows in the tasks table
Parameters:
    conn: the Connection object
Return:
    None
'''
def select_all_tasks(table, curs):
    curs.execute("SELECT * FROM " + table)

    rows = curs.fetchall()                          

    x = 0
    for row in rows:
        if(x % 345679 == 0):
            print(row)
        x += 134589


'''
Description:
    Export a json file to a sqlite3 db
Parameters:
    path: absolute path of db file
Return:
    None
'''
connections = {}
def json_to_database(object_name, columns, json_path, db_path):    
    # connect to sqlite database and update dictionary with json_file_name:db_file_connection
    conn = sqlite3.connect(__db_location__)

    # parse through every file name in directory 5_core
    conn_num = 0
    entries = os.scandir(__json_location__)
    for entry in entries:
        print(entry.name)
        if(entry.name == '.DS_Store'):
            continue

        df = read_json(__json_location__ + entry.name, lines = True)        # Create A DataFrame From the JSON Data   
        
        # isolate rows x columns
        metaData = []                                       
        metaData.append([df.size, df.shape[1]])                             # append a tuple with values [0 = rows aka number of reviews][1 = number of columns]
    
        if(object_name == "review"):
            df["reviewID"] = range(1, len(df.index)+1)
            df["minHash"] = ""
            df = df[columns]

        if(object_name == "user"):
            df = df[columns]
            df.drop_duplicates(subset=["reviewerID"], inplace=True) 
            df.fillna(value="", inplace=True)

        if(object_name == "product"):
            df["category"] = entry.name[:-7]
            df["duplicateRatio"] = 0.0
            df["incentivizedRatio"] = 0.0
            df["ratingAnomalyRate"] = 0.0
            df["reviewAnomalyRate"] = 0.0
            df = df[columns]
            df.drop_duplicates(subset=["asin"], inplace=True) 

        # Export data frame to sqlite database
        engine = create_engine('sqlite:////' + __db_location__, echo=False)                     # can change first param to ':memory:' to store in RAM instead of disk, change echo to echo=True if you want to see description of exporting to sqlite
        sqlite_connection = engine.connect()                                                    # https://www.fullstackpython.com/blog/export-pandas-dataframes-sqlite-sqlalchemy.html
        sqlite_table = object_name
        df.to_sql(sqlite_table, sqlite_connection, if_exists='append', index=False)                          # use 'append' to keep duplicate reviews
        
        # save meta data for each table
        metaData.append(conn_num)
        connections[sqlite_table] = metaData        
        print(connections[sqlite_table])
        conn_num += 1

    return conn

