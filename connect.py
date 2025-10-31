import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from cassandra.cluster import Cluster
from cassandra.connection import NoHostAvailable

MongoDBClient = MongoClient('mongodb://localhost:27017/')

CassandraCluster = Cluster(['127.0.0.1'])
CassandraSession = CassandraCluster.connect()

