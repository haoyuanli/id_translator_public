"""
Suite of methods used to communicate with MongoDB backend
"""

import json
import os
import re
from pathlib import Path
from pprint import pprint


import pandas as pd
from pymongo import ReturnDocument, MongoClient, TEXT, DeleteOne, ReplaceOne
from pymongo.errors import ServerSelectionTimeoutError, InvalidOperation, BulkWriteError, InvalidName
from flask_table import create_table, Col

from id_translator.database.db_handler import DBHandler


class GSCHandler(DBHandler):
    """
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
        self.missed_table = None
        self.translate_table = None
        self.db = None
        self.collection_temp = None
        self.collection_main = None
        self.collection_link = None
        self.client = None

        super().__init__(mongo_configs, project_configs, logger)

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
            self.collection_link = self.db[self.mongo_configs["COLLECTION_LINK"]]
            self.collection_temp = self.db[self.mongo_configs["COLLECTION_TEMP"]]
            self.collection_main.create_index([("$**", TEXT)])
            self.collection_link.create_index([("$**", TEXT)])
            self.collection_temp.create_index([("$**", TEXT)])

        except ServerSelectionTimeoutError as SSTE:
            self.logger.warning("Check the connection of "
                                "MongoDB running at "
                                "{}".format(self.mongo_configs["URI"]))
            self.logger.error(SSTE)
            raise SSTE
        except InvalidName as invalid:
            self.logger.warning("Check config file and/or collections")
            self.logger.error(invalid)
            raise invalid

    def print_test(self):
        print(self.collection_main)
        print(self.collection_link)
        print(self.collection_temp)

    def update_temp_collection(self, file):
        print("Updating")
        if not self.client:
            self.connect()

        try:
            self.collection_temp.drop()
            dataframe = pd.read_csv(file)
            records = dataframe.to_dict('records')
            self.collection_temp.insert_many(records)
        except FileNotFoundError:
            raise FileNotFoundError

    def update_main_collection(self):
        """
        Documents in the linked collection
        {'_id': 'lims_pt_id', 'lims_pt_id': 'project_id'}

        Documents in the temp collection
        {'_id': mongo generated id,
        'project_title1':'project1_id,
        'project_titleN': 'projectN_id'}

        Need to check for the existence of matching project_id in both
        a linked and temp Document. A match will allow it to be added to
        the main data collection
        """
        if not self.client:
            self.connect()

        links = list(self.collection_link.find({}))
        temp = list(self.collection_temp.find({}))

        delete_operations = []
        upload_operations = []

        for ldoc in links:
            for tdoc in temp:
                if ldoc[ldoc['_id']] in tdoc.values():
                    delete_operations.append(DeleteOne({'_id': tdoc['_id']}))
                    sync = tdoc
                    sync.pop("_id")
                    sync['lims_pt_id'] = ldoc['_id']

                    upload_operations.append(ReplaceOne({'lims_pt_id': sync['lims_pt_id']},
                                                        sync,
                                                        upsert=True))
        try:
            self.collection_main.bulk_write(upload_operations, ordered=False)
            self.collection_temp.bulk_write(delete_operations, ordered=False)
        except BulkWriteError as bwe:
            pprint(bwe.details)
        except InvalidOperation as io:
            arg = io.args[0].strip()
            if arg == 'No operations to execute':
                pass
            else:
                raise io

        return self.make_missed_table(), len(upload_operations)

    def make_missed_table(self):
        """
        Makes a table of all the missed records and stores it
        as a class variable since a helper function is the
        one that returns the table via AJAX

        :return: Count of missed records (Int)
        """
        if not self.client:
            self.connect()

        cursor = self.collection_temp.find({})
        missed = [record for record in cursor]
        missed_table = create_table()

        # remove _id
        for record in missed:
            del record["_id"]

        # create table columns
        for k, v in missed[0].items():
            missed_table.add_column(k, Col(k))

        self.missed_table = missed_table(missed)

        return len(list(missed))

    def get_missed_table(self):
        """
        Getter for missed table, populated by entries in temp collection
        remaining after an update to the main collection
        """
        return self.missed_table

    def put_linked_data(self, data):
        """
        Store linking data in Linked Collection, rewriting regular mongoID
        with the expected lims ID

        :param data: json dict of <project_id:lims_pt_id>
        :return True if new updates, False if no new links
        """
        if not self.client:
            self.connect()

        entries = [{"_id": str(lims), str(lims): project} for project, lims in data.items()]
        current = list(self.collection_link.find({}))
        updated = []
        bulk = self.collection_link.initialize_unordered_bulk_op()

        for item in entries:
            if item not in current:
                updated.append(item)
                bulk.insert(item)

        if len(updated) > 0:
            bulk.execute()
            return True
        return False

    def get_missed_records(self):
        """
        Used to query database and retrieve missed records

        :return: list of all missed pog ids
        """
        if not self.client:
            self.connect()

        missed = list(self.collection_temp.find({}))
        pogs = [item['pogid'] for item in missed]
        return json.dumps(pogs)

    def get_current_linked_ids(self):
        """
        Getter for link collection

        """
        if not self.client:
            self.connect()
        return json.dumps(list(self.collection_link.find({})))

