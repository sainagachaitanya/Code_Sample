# import built-ins
import time
import logging

# import pymongo
import pymongo

# import osvfx
from logger import Logger
from preferences import Preference
from schema import validate as validate_schema

# Module Constants
MONGO_PREFERENCES = Preference("mongo_preferences.yaml")
DATABASE = MONGO_PREFERENCES["database"]
TIMEOUT = MONGO_PREFERENCES["timeout"]
MONGO_URI = MONGO_PREFERENCES["mongo_uri"]

# Initiate Logger
class OSMongo(Logger):
    LOGGER_NAME = "OSMongo"
    DEFAULT_LEVEL = logging.INFO
    PROPAGATE_DEFAULT = False

class MongoAPI:
    """
    A class for performing operations using PyMongo, the official Python driver for MongoDB.

    Attributes:
        _is_installed (bool):
            A flag indicating whether PyMongo is connected in the current environment.
            It is set to True if PyMongo is connected, otherwise, it remains False.
            This attribute is used to check the availability of PyMongo functionalities.

        _client (MongoClient or None):
            The MongoClient object representing the connection to the MongoDB server.
            It is set to None if the connection has not been established yet.
            The connection is initialized using the '_connect' method

        database (str or None):
            The name of the MongoDB database with which the class is currently working.
            It is set to None initially and gets assigned when a valid database is selected.

    Methods:
        __init__(self, connection_uri=None, timeout=None, database_name=None)
        _connect(self)
        disconnect(self)
        insert_one(self, collection, document)
        insert_many(self, collection, documents)
        find(self, collection_name, query=None, projection=None, limit=0)
        find_one(self, collection, query=None, projection=None)
        update_one(self, collection, query, data)
        replace_one(self, collection, query, data)
        delete_one(self, collection)
        delete_many(self, collection)
        count(self, collection, query)
    """
    def __init__(self, connection_uri=None, server_timeout=None, database_name=None):
        """
        Initialize the MongoAPI class by calling _connect method which creates a MongoClient instance.

            connection_uri (str):
                The MongoDB connection URI used to establish a connection with the MongoDB server.

                If 'connection_uri' is provided, it will attempt to connect to the specified MongoDB server.
                If 'connection_uri' is not provided, it will connect to the server specified in mongo_preferences.yaml.
                If 'connection_uri' is None, it will connect to the default localhost server.

            server_timeout (int or None):
                The timeout value (in milliseconds) for operations on the MongoDB server.
                If set to None, the operations will not timeout, and they may block indefinitely.
                If set to a positive integer, operations will timeout after the given number of milliseconds.

                If 'server_timeout' is provided, it will use the provided value.
                If 'server_timeout' is not provided, it will get the value specified in mongo_preferences.yaml.
                If 'server_timeout' is None, it will default to 1000.

            database_name (str or None):
                The name of the current MongoDB database being used.

                If 'database_name' is provided, it will use the provided value.
                If 'database_name' is not provided, it will get the value specified in mongo_preferences.yaml.
                If 'database_name' is None, it will default to osvfx.

        :param connection_uri: MongoDB Server URI, eg: mongodb://127.0.0.1:27017
        :type connection_uri: str

        :param server_timeout: Timeout value in ms
        :type server_timeout: int
        
        :param database_name: Name of the database
        :type database_name: str
        """

        # Declare Instance Attributes
        self._is_installed = False
        self._client = None
        self.database = None

        self.connection_uri = (
            connection_uri if connection_uri is not None else (MONGO_URI if MONGO_URI is not None else "mongodb://127.0.0.1:27017")
        )

        self.server_timeout = (
            server_timeout if server_timeout is not None else (TIMEOUT if TIMEOUT is not None else 1000)
        )

        self.database_name = (
            database_name if database_name is not None else (DATABASE if DATABASE is not None else "osvfx")
        )

        # Connect to Database when this class is Initiated
        self._connect()

    def __repr__(self):
        return "mongo = MongoAPI()\ncollection = mongo.database[collection_name]\nmongo.insert_ine(collection, data)"
    
    def _connect(self):

        """
        Method to connect to the database
        """
        if self._is_installed:
            OSMongo.warning("We are already connected to the database")
            return
        
        self._client = pymongo.MongoClient(self.connection_uri, serverSelectionTimeoutMS=self.server_timeout)

        for retry in range(3):
            try:
                time_1 = time.time()
                self._client.server_info()
            except Exception as e:
                OSMongo.error(f"Something gone wrong while attempting to connect, Retrying: {str(retry)} time(s)")
                time.sleep(1)
                self.server_timeout += 1.5
            else:
                break
        else:
            raise IOError(f"ERROR: Couldn't Connect to database in less than {self.server_timeout}")
        
        OSMongo.log(20, "Connected to %s, delay %.3f s" % (self.connection_uri, time.time() - time_1))
        self.database = self._client[self.database_name]
        self._is_installed = True
    
    def disconnect(self):
        """
        Close any connection to the database
        """
        try:
            self._client.close()
            OSMongo.warning("Disconnecting MongoDB...")
        except AttributeError as e:
            OSMongo.exception(e)

        self._client = False
        self.database = None
        self._is_installed = None

    def count(self, collection, query={}):
        """
        Count the number of documents in the specified collection that match the 'query'.
        If 'query' is None, it will return the total number of documents in the collection.

        :param collection: Collection to insert the document
        :type collection: pymongo collection object

        :param query: query to count
        :type query: dict
        
        :return: number of documents in the collection
        :rtype: int

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            total_count = mongo.count(collection)
            print(total_count)
        """
        return collection.count_documents(query)

    def insert_one(self, collection, data):
        """
        Insert a single document into the specified collection.

        :param collection: Collection to insert the document
        :type collection: pymongo collection object

        :param data: Dictionary to insert as document
        :type data: dict
        
        :return: ID of the document inserted
        :rtype: pymongo ObjectID

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            data = {"item1": "value1"}
            inserted_id = mongo.insert_one(collection, data)
            print(inserted_id)
        """
        assert isinstance(data, dict), "data must be of type <dict>"
        validate_schema(data)
        inserted_id = collection.insert_one(data).inserted_id
        if inserted_id:
            OSMongo.info(f"Successfully inserted: {inserted_id}")
            return inserted_id
        else:
            OSMongo.error("Something went wrong when inserting data")

    def insert_many(self, collection, data, ordered=True):
        """
        Insert multiple documents into the specified collection.

        :param collection: Collection to insert the document
        :type collection: pymongo collection object

        :param data: list of Dictionaries to insert as documents
        :type data: list
        
        :return: IDs of the document inserted
        :rtype: pymongo ObjectIDs

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            data = [{"item1": "value1"}, {"item2": "value2"}]
            inserted_ids = mongo.insert_many(collection, data)
            print(inserted_ids)
        """
        assert isinstance(data, list), "`items` must be of type <list>"

        for item in data:
            assert isinstance(item, dict), "`item` must be of type <dict>"
            validate_schema(data)

        inserted_ids = collection.insert_many(data, ordered=ordered).inserted_ids

        if inserted_ids:
            OSMongo.info(f"Successfully inserted: {inserted_ids}")
            return inserted_ids
        else:
            OSMongo.error("Something went wrong when inserting data")
    
    def find(self, collection, query={}, projection=None, sort=None, limit=0):
        """
        Find and retrieve multiple documents from the specified collection.
        'query' allows filtering the search
        'projection' lets you specify which fields to include.
        'sort' allows sorting the search in ascending or decending order
        'limit' restricts the maximum number of documents to be returned (default: all).

        :param collection: Collection to find the documents
        :type collection: pymongo collection object

        :param query: query to match the search
        :type query: dict
        
        :param projection: Determines which fields are returned in the matching documents
        :type projection: dict

        :param sort: sort parameters 
        :type sort: list

        :param limit: maximum number of documents to return
        :type limit: int

        :return: Iterator with Documents in the collection collection
        :rtype: pymongo.cursor.Cursor object

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            query = {"item1": "value1"}
            projection = {"item1": "value1"}
            sort = [("_id", 1)]
            limit = 2
            all_docs = mongo.find(collection, query, projection, sort, limit)
            for doc in all_docs:
                print(doc)
        """
        if projection is not None:
            assert isinstance(projection, dict), "`filter` must be <dict>"

        if sort is not None:
            assert isinstance(sort, list), "`sort` must be <list> of <tuple> like [(field, direction)], 1 for ascending, -1 for decending eg[('_id', 1)]"
            for item in sort:
                assert isinstance(item, tuple), "`sort item` must be of type <tuple>"
        else:
            sort = [("_id", 1)]

        return collection.find(filter=query, projection=projection).sort(sort).limit(limit)

    def find_one(self, collection, query, projection=None):
        """
         Find and retrieve a single document from the specified collection.
        'query' allows filtering the search, and 'projection' lets you specify which fields to include.

        :param collection: Collection to find the documents
        :type collection: pymongo collection object

        :param query: query to match the search
        :type query: dict
        
        :param projection: Determines which fields are returned in the matching documents. eg: {"item1": "value1"}
        :type projection: dict

        :return: Document as a Dictionary
        :rtype: dict

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            doc = mongo.find_one(collection, {"item1": "value1"})
            print(doc)
        """
        assert isinstance(query, dict), "`query` must be <dict>"
        if projection is not None:
            assert isinstance(projection, dict), "`query` must be <dict>"

        return collection.find_one(filter=query, projection=projection)

    def update_one(self, collection, query, data):
        """
        Update a single document in the specified collection that matches the 'query'.
        The 'data' parameter should contain the modification to apply.

        :param collection: Collection to insert the document
        :type collection: pymongo collection object

        :param query: query to get the document
        :type query: dict

        :param data: data to update
        :type data: dict
        
        :return: Updated result object
        :rtype: pymongo.results.UpdateResult object

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            query = {"_id": ObjectId('64bbb2d05356bf8411271a81')}
            data = {
                "$set": {"item1": "Super Updated Value"},
                "$rename": {"item2": "renamed_item"},
                "$unset": {"item2", ""}
            }
            mongo.update_one(collection, query, data)
        """
        assert isinstance(query, dict), "query must be <dict>"
        assert isinstance(data, dict), "data must be of type <dict>"
        updated_result = collection.update_one(query, data)
    
        if updated_result:
            OSMongo.info(f"Successfully updated {query} with {data}")
            return updated_result
        else:
            OSMongo.error("Something went wrong when updating data")

    def replace_one(self, collection, query, data):
        """
        Replace a single document in the collection that matches the specified query criteria.
        This will keep the id and replace data

        :param collection: Collection to insert the document
        :type collection: pymongo collection object

        :param query: query to get the document
        :type query: dict

        :param data: data to replace
        :type data: dict
        
        :return: Updated result object
        :rtype: pymongo.results.UpdateResult object

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            data = {"item10": "value10"}
            mongo.replace_one(collection, data)
        """
        assert isinstance(query, dict), "filter must be <dict>"
        assert isinstance(data, dict), "data must be of type <dict>"
        updated_result = collection.replace_one(query, data)

        if updated_result:
            OSMongo.info(f"Successfully replaced {query} with {data}")
            return updated_result
        else:
            OSMongo.error("Something went wrong when replacing data")

    def delete_one(self, collection, query):
        """
        Delete a single document from the specified collection that matches the 'query'.

        :param collection: Collection to delete the document from
        :type collection: pymongo collection object

        :param query: query to get the document
        :type query: dict
        
        :return: Deleted result object
        :rtype: pymongo.results.DeleteResult object

        Example:
            from osmongo import MongoAPI
            mongo = MongoAPI()
            collection = mongo.database["osvfx"]
            query = {"_id": ObjectId('64bbb2d05356bf8411271a81')}
            mongo.delete_one(collection, query)
        """
        assert isinstance(query, dict), "filter must be <dict>"
        deleted_result = collection.delete_one(query)

        if deleted_result:
            OSMongo.info(f"Successfully deleted {query}")
            return deleted_result
        else:
            OSMongo.error("Something went wrong when deleting data")
    
    def update_many(self, collection=None):
        raise NotImplementedError("This method is not implemented, use update_one in a for-loop")

    def delete_many(self, documents=None):
        raise NotImplementedError("This is not implemented as this has potential risk to delete all if used incorrectly")
    