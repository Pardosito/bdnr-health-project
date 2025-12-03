import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from cassandra.cluster import Cluster, NoHostAvailable
import pydgraph
from Cassandra import model

CASSANDRA_KEYSPACE = "health_service"

#conexion de mondongo
def get_mongo():
    try:
        client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=2000
        )
        db = client["plataforma_salud"]
        client.server_info()
        print("[MongoDB] Conectado correctamente.")
        return db

    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        print("[MongoDB] ERROR de conexión:", e)
        return None


#conexion de cassandra
def get_cassandra():
    try:
        cluster = Cluster(["127.0.0.1"])
        session = cluster.connect()
        model.create_keyspace(session, CASSANDRA_KEYSPACE, 1)
        session.set_keyspace(CASSANDRA_KEYSPACE)
        model.create_schema(session)
        print("[Cassandra] Conectado e inicializado correctamente.")
        return session

    except NoHostAvailable as e:
        print("[Cassandra] ERROR: Cassandra no responde:", e)
        return None
    except Exception as e:
        print(f"[Cassandra] ERROR de conexión: {e}")
        return None


#dgrapph solo la conexion
def get_dgraph():
    """
    SOLO conecta a Dgraph. TODO lo demás se prueba desde el main.
    """
    try:
        stub = pydgraph.DgraphClientStub("localhost:9080")
        client = pydgraph.DgraphClient(stub)
        print("[Dgraph] Conectado correctamente.")
        return client

    except Exception as e:
        print("[Dgraph] ERROR de conexión:", e)
        return None

#todas las bases
def get_all_connections():
    return {
        "mongo": get_mongo(),
        "cassandra": get_cassandra(),
        "dgraph": get_dgraph()
    }


if __name__ == "__main__":
    print("=== Probando conexiones ===")
    conns = get_all_connections()
    print(conns)

