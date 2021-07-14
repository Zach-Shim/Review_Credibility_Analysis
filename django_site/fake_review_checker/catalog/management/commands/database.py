# Python Imports
import os
import sqlite3

# Django Imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

# Relative Imports
from ...models import User, Product, Review
from .file_to_database import FileToDatabase

# Global Directory Variables
__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__json_location__ = __current_dir__[:-20] + "/datasets/"
__db_location__ = __current_dir__[:-28] + "/db.sqlite3"



class Command(BaseCommand):
    help = 'Manipulate SQl database'

    def add_arguments(self, parser):
        parser.add_argument('table_name', type=str, nargs='?', help='Indicates the name of the table to insert data into')
        parser.add_argument('-r', '--remove', action='store_true', help='Remove all records from a given table')
        parser.add_argument('-ra', '--remove_all', action='store_true', help='Remove all records from all tables (User, Product, and Review)')
        parser.add_argument('-d', '--drop', action='store_true', help='Drop a given table')
        parser.add_argument('-da', '--drop_all', action='store_true', help='Drop all tables (User, Product, and Review)')
        parser.add_argument('-s', '--select', action='store_true', help='Query all records from a given table')
        parser.add_argument('-sa', '--select_all', action='store_true', help='Query all records from all tables (User, Product, and Review)')
        parser.add_argument('-i', '--insert', action='store_true', help='Insert all records from a given directory')
        parser.add_argument('-ia', '--insert_all', action='store_true', help='Insert all records into all tables (User, Product, and Review). Data is taken from a local directory')


    def handle(self, *args, **kwargs):
        db = Database()
        command = db.serialize(*args, **kwargs)
        if db.all:
            command()
        else:
            try:
                table = kwargs['table_name']
            except Exception as e:
                print(e)
                print("Please enter a table name preceding the sql command")
            command(table)
            


class Database():
    def __init__(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect(__db_location__)
        except Exception as e:
            print(e)
        
        self.db_curs = self.conn.cursor()
        self.all = False
        self.tables = ['user', 'product', 'review']



    # creator component
    def serialize(self, *args, **kwargs):    
        if kwargs['remove']:
            return self.remove
        elif kwargs['remove_all']:
            self.all = True
            return self.remove_all
        elif kwargs['drop']:
            return self.drop
        elif kwargs['drop_all']:
            self.all = True
            return self.drop_all
        elif kwargs['select']:
            return self.select
        elif kwargs['select_all']:
            self.all = True
            return self.select_all
        elif kwargs['insert']:
            return self.insert
        elif kwargs['insert_all']:
            self.all = True
            return self.insert_all
        else:
            raise ValueError("Please enter the name of an existing table in the db.sqlite3 database")



    def remove(self, table_name):
        print("removing records from table " + table_name)
        try:
            self.db_curs.execute('delete from ' + table_name + ';')
            self.conn.commit()
            print("Successfully removed all records from " + table_name)
        except Exception as e:
            print(e)
            print("Failed to remove records from " + table_name)



    def remove_all(self):
        print("removing all records")
        for table in self.tables:
            self.remove(table)



    def drop(self, table_name):
        print("dropping table " + table_name)
        try:
            self.db_curs.execute('drop table ' + table_name + ';')
            self.conn.commit()
            print("Successfully dropped table " + table_name)
        except Exception as e:
            print("Failed to drop table " + table_name)



    def drop_all(self):
        print("dropping all tables")
        for table in self.tables:
            self.drop(table)



    def select(self, table_name):
        print("querying records from table " + table_name)
        try:
            self.db_curs.execute("select * from " + table_name + ";")
            self.conn.commit()
            rows = self.db_curs.fetchall()
            
            x = 0
            for row in rows:
                x += 1
                print(row)
                print('\n')
            print("Retrieved a total of " + str(x) + " " + table_name + "s from database")
        except Exception as e:
            print(e)
            print("Failed to retrieve records from " + table_name)



    def select_all(self):
        print("querying from all tables")
        for table in self.tables:
            self.select(table)

    

    def insert(self, table_name):
        print("inserting data")
        ftd = FileToDatabase()
        ftd.serialize(table_name)

    

    def insert_all(self):
        print("querying from all tables")
        for table in self.tables:
            self.insert(table)