from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.connection import NoHostAvailable

import pydgraph


#mondongo
def get_mongo():
    """
    Retorna una conexión funcional a MongoDB.
    Si falla, regresa None pero NO truena todo el sistema.
    """
    try:
        client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=2000
        )
        db = client["plataforma_salud"]
        client.server_info()   # fuerza verificar conexión
        print("[MongoDB] Conectado correctamente.")
        return db

    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        print("[MongoDB] ERROR de conexión:", e)
        return None


#cassandra
def get_cassandra():
    """
    Retorna una sesión funcional con Cassandra.
    Requiere que el keyspace plataforma_salud ya exista.
    """
    try:
        cluster = Cluster(["127.0.0.1"])
        session = cluster.connect("plataforma_salud")  # importante especificar keyspace
        print("[Cassandra] Conectado correctamente.")
        return session

    except NoHostAvailable as e:
        print("[Cassandra] ERROR: Cassandra no está corriendo o no responde:", e)
        return None

    except Exception as e:
        print("[Cassandra] ERROR de conexión:", e)
        return None


#dgraph
def get_dgraph():
    """
    Crea y retorna un cliente Dgraph usando gRPC.
    Solo se usa si lo necesitas en pruebas.
    """
    try:
        stub = pydgraph.DgraphClientStub("localhost:9080")
        client = pydgraph.DgraphClient(stub)
        print("[Dgraph] Conectado correctamente.")
        return client

    except Exception as e:
        print("[Dgraph] ERROR de conexión:", e)
        return None

#las tres bases
def get_all_connections():
    """
    Regresa un diccionario con TODAS las conexiones.
    """
    return {
        "mongo": get_mongo(),
        "cassandra": get_cassandra(),
        "dgraph": get_dgraph()
    }


#preuba rápida
if __name__ == "__main__":
    print("=== Probando conexiones ===")
    conns = get_all_connections()
    print(conns)
