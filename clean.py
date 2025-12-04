import os
from connect import get_mongo, get_dgraph
from cassandra.cluster import Cluster
import pydgraph

MONGO_DB_NAME = os.getenv("MONGO_DB", "health_platform")
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'health_service')

def limpiar_todo():
    print("Iniciando limpieza total de bases de datos...\n")

    # 1. LIMPIAR MONGODB
    print(f"--- Limpiando MongoDB ({MONGO_DB_NAME}) ---")
    try:
        mongo_db = get_mongo()
        if mongo_db is not None:
            client = mongo_db.client
            client.drop_database(MONGO_DB_NAME)
            print(f"Base de datos '{MONGO_DB_NAME}' eliminada.")
        else:
            print("No hay conexión a MongoDB.")
    except Exception as e:
        print(f"Error limpiando Mongo: {e}")


    # 2. LIMPIAR CASSANDRA
    print(f"\n--- Limpiando Cassandra ({CASSANDRA_KEYSPACE}) ---")
    try:
        cluster = Cluster(["127.0.0.1"])
        session = cluster.connect()

        query = f"DROP KEYSPACE IF EXISTS {CASSANDRA_KEYSPACE};"
        session.execute(query)
        print(f"Keyspace '{CASSANDRA_KEYSPACE}' eliminado.")
        cluster.shutdown()
    except Exception as e:
        print(f"Error limpiando Cassandra: {e}")


    # 3. LIMPIAR DGRAPH
    print("\n--- Limpiando Dgraph (Drop All) ---")
    try:
        client = get_dgraph()
        if client is not None:
            op = pydgraph.Operation(drop_all=True)
            client.alter(op)
            print("Dgraph reseteado totalmente (Drop All).")
        else:
            print("No hay conexión a Dgraph.")
    except Exception as e:
        print(f"Error limpiando Dgraph: {e}")

    print("\n¡Limpieza finalizada! El sistema está vacío.")

if __name__ == "__main__":
    limpiar_todo()