"""
Basic suite of methods used to communicate with MongoDB backend
"""

import json
import os
import re
from pathlib import Path
from pprint import pprint


import pandas as pd
from pymongo import ReturnDocument, MongoClient, TEXT, DeleteOne, ReplaceOne
from pymongo.errors import ServerSelectionTimeoutError, InvalidOperation, BulkWriteError
from flask_table import create_table, Col


class DBHandler(object):
    """
    DBHandler 'extends' many PyMongo methods to include basic error handling
    and logic specific to the ID-Translator front end routes/methods. This
    class is used for any regular implementation of the ID-Translator. For
    running the ID-translator within the GSC, use ___

    configs is the parsed mongo configuration dictionary created on runtime
    in __main__

    logger is the Flask logger
    """
    def __init__(self, mongo_configs, project_configs, logger):
        self.mongo_configs = mongo_configs
        self.project_configs = project_configs
        self.logger = logger
        self.editing_record = None
        self.delete_record = None
        self.translate_table = None
        self.db = None
        self.collection_main = None
        self.client = None

    def connect(self):
        try:

            if self.mongo_configs["SSL"] == "True":
                self.client = MongoClient(
                    self.mongo_configs["URI"],
                    ssl=True,
                    ssl_ca_certs=self.mongo_configs["CERT"]
                )
            else:
                self.client = MongoClient(self.mongo_configs["URI"])

            self.db = self.client[self.mongo_configs["DB"]]
            self.collection_main = self.db[self.mongo_configs["COLLECTION_MAIN"]]
            self.collection_main.create_index([("$**", TEXT)])

        except ServerSelectionTimeoutError as SSTE:
            self.logger.warning("Check the connection of "
                                "MongoDB running at "
                                "{}".format(self.mongo_configs["URI"]))
            self.logger.error(SSTE)
            raise SSTE

    def print_test(self):
        print(self.collection_main)

    def translate(self, request_id):
        """
        Returns all project IDs corresponding to given ID
        Parameters
        ==========
        request_id: string
            Any patient identifier

        Returns
        =======
        response: table
            dict of titles and corresponding values wrapped in an HTML table
        """
        if not self.client:
            self.connect()

        projects = {}

        if request_id is not None:
            response = self.collection_main.find_one({"$text": {'$search': request_id}})

            # Search the returned query for any of the known project IDs
            valid = False

            if response:
                for pid, pvalue in response.items():
                    # print('{}:{},{}:{}'.format(pid, type(pid), pvalue, type(pvalue)))

                    # The document is formatted to only have strings. Floats are only
                    # possible as a NaN, which should be turned to a string.

                    if type(pvalue) is float:
                        pvalue = ''

                    if pid in self.project_configs['IDS_TO_RETURN']:
                        if pvalue.lower() == request_id.lower() and pvalue != '':
                            valid = True
                            projects[pid] = pvalue

                        elif pvalue != '':
                            projects[pid] = pvalue
            if valid:
                return projects

        return None

    def get_record(self, _id):
        """
        Get all information of a given patient

        Parameters
        ==========
        _id: string
            Secure identifier of a patient

        Returns
        =======
        response: json.string
            key-value pairs for all fields of the requested record

        """
        if not self.client:
            self.connect()

        search = _id
        record = self.collection_main.find_one({self.project_configs['PRIMARY_KEY']: {'$in': [search]}})
        if not record:
            response = {}
        else:
            record.pop('_id')
            response = record
        return response

    def set_record(self, _id):
        """
        Update a record with primary key _id with the supplied record

        Parameters
        ==========
        _id: string
            Secure identifier of a patient, PK of records

        """
        if not self.client:
            self.connect()

        # Check the difference between the existing record and the updated one
        # Differences are old fields that need to be removed

        new_record = self.get_editing_record()
        checked_record = {field: value for field, value in new_record.items() if field is not ''}
        checked_record_keys = set(checked_record.keys())
        current_record = self.get_record(_id)
        current_record_keys = set(current_record.keys())
        removed_keys = list(current_record_keys - checked_record_keys)

        print("Checked Record: {}".format(checked_record))

        # Add in any fields marked for deletion

        if self.delete_record:
            removed_keys += self.delete_record

        print("Things to be deleted: {}".format(removed_keys))

        self.remove_fields(_id, removed_keys)

        # Remove deleted fields from the temp edited record before calling update function in Mongo

        final_record = {field: value for field, value in checked_record.items() if field not in self.delete_record}

        print("Final Record: {}".format(final_record))

        updated_record = self.collection_main.find_one_and_update(
            {self.project_configs['PRIMARY_KEY']: _id},
            {'$set': final_record},
            upsert=True,
            return_document=ReturnDocument.AFTER)

    def remove_fields(self, _id, fields):
        """
        Remove fields of record _id

        Parameters
        ==========
        _id: string
            Secure identifier of a patient that is also the PK of the table
        fields: list
            field names to remove

        Returns
        =======
        None

        """
        if not self.client:
            self.connect()

        request = dict((field, "") for field in fields)

        if request:
            record = self.collection_main.find_one_and_update(
                {self.project_configs['PRIMARY_KEY']: _id},
                {'$unset': request},
                upsert=True,
                return_document=ReturnDocument.AFTER)
            record.pop("_id")

    def update_collection(self, file):
        """
        Update the database with a selected CSV file found in {base}/data
        """
        if not self.client:
            self.connect()

        update_operations = []
        pk = self.project_configs['PRIMARY_KEY']

        try:
            dataframe = pd.read_csv(file)
            records = dataframe.to_dict('records')
            for record in records:
                update_operations.append(ReplaceOne({pk: record[pk]}, record, upsert=True))

            self.collection_main.bulk_write(update_operations, ordered=False)
        except KeyError:
            raise KeyError
        except FileNotFoundError:
            raise FileNotFoundError
        except BulkWriteError as bwe:
            pprint(bwe.details)
            raise BulkWriteError
        except InvalidOperation as io:
            arg = io.args[0].strip()
            if arg == 'No operations to execute':
                return 206, len(update_operations)
            else:
                raise io

        return 200, len(update_operations)

    def make_translated_table(self, record):
        """
        Creates a table using a record searched up by translate()
        """
        translate_table = create_table()
        for k, v in record.items():
            translate_table.add_column(k, Col(k))

        self.translate_table = translate_table([record])
        return self.translate_table

    def get_translate_table(self):
        """
        Getter for translate table
        """
        return self.translate_table

    def get_upload_files(self):
        """
        Parses /data folder to populate dropdown
        selection in Upload page
        """
        path = Path(os.path.realpath(__file__)).parents
        p = "{}/data".format(path[2])
        if not os.path.exists(p):
            os.mkdir(p)
        files = [file for r, d, f in os.walk(p) for file in f if '.csv' in file]
        file_array = [{"value": n+1, "text": file} for n, file in enumerate(files)]
        return file_array

    def get_partial_record(self, term, all_fields=False):
        """
        Get all possible records based on current search id

        Parameters
        ==========
        term: string
            Any field in the db

        all_fields: Boolean
            Flag to alter search query. Needed for Translate
            page since it won't always use the PK

        Returns
        =======
        response: list
            Possible records

        """
        if not self.client:
            self.connect()

        search = term

        if all_fields:
            query = {'$regex': search, '$options': 'i'}
            fields = [{field: query} for field in self.project_configs['IDS_TO_RETURN']]
            records = self.collection_main.find({
                "$or": fields})
        else:
            records = self.collection_main.find({self.project_configs['PRIMARY_KEY']: {'$regex': search, '$options': 'i'}})

        combined = []

        if not records:
            self.logger.warning("get_partial_record({}) - No record found".format(search))
        else:
            for record in records:
                record.pop('_id')
                primary = list(record.values())
                combined += primary

        regex = re.compile("(?i){}+".format(term))
        response = list(filter(regex.match, map(lambda x: '' if isinstance(x, float) else x, combined)))

        return response

    def get_records(self):
        """
        Grab all primary keys in collection

        :return: list of primary keys
        """
        if not self.client:
            self.connect()

        records = self.collection_main.find()
        resp = [record[self.project_configs['PRIMARY_KEY']] for record in records]
        return resp

    def get_main_db_count(self):
        """
        Count function to populate info panel
        """
        if not self.client:
            self.connect()
        return self.collection_main.count_documents({})

    def get_editing_record(self):
        """
        Getter for editing record
        """
        return self.editing_record

    def get_delete_record(self):
        """
        Getter for delete record
        """
        return self.delete_record

    def check_editing_record(self):
        """
        Query editing record existence
        """
        return bool(self.editing_record)

    def check_delete_record(self):
        """
        Query delete record existence
        """
        return bool(self.delete_record)

    def set_delete_record(self):
        """
        Reset delete record for new entry
        """
        self.delete_record = {}

    def set_editing_record(self, record):
        """
        Set the editing record as a copy of record provided
        """
        self.editing_record = record

    def add_to_delete(self, key, value):
        """
        Add a key-pair value to the delete record to be deleted
        when the Upload button is pressed
        """
        self.delete_record[key] = value
