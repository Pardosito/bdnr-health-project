import os
import importlib
import logging

logger = logging.getLogger(__name__)


def init_db(mongo_uri=None, mongo_db=None):
    """Inicializa o reconfigura la conexión a MongoDB para el paquete `mongo`.

    Si `mongo_uri` o `mongo_db` se proporcionan, ajusta las variables de entorno
    y recarga el módulo `mongo.mongo` para aplicar la nueva configuración.

    Retorna un dict con objetos: client, db, doctores, pacientes, expedientes
    """
    if mongo_uri:
        os.environ["MONGO_URI"] = mongo_uri
    if mongo_db:
        os.environ["MONGO_DB"] = mongo_db

    try:
        # Importar y recargar el módulo para que use las variables de entorno
        from . import mongo as _mongo
        importlib.reload(_mongo)
        return {
            "client": _mongo.client,
            "db": _mongo.db,
            "doctores": _mongo.doctores,
            "pacientes": _mongo.pacientes,
            "expedientes": _mongo.expedientes,
        }
    except Exception as e:
        logger.error("Error inicializando Mongo: %s", e)
        raise


if __name__ == "__main__":
    # Uso rápido desde línea de comandos para verificar la conexión
    import argparse

    parser = argparse.ArgumentParser(description="Inicializar conexión a MongoDB para el paquete mongo")
    parser.add_argument("--uri", help="MongoDB URI, p.ej. mongodb://localhost:27017/")
    parser.add_argument("--db", help="Nombre de la base de datos")
    args = parser.parse_args()

    try:
        cfg = init_db(mongo_uri=args.uri, mongo_db=args.db)
        print("Conexión establecida.")
        print("DB:", cfg["db"].name if cfg["db"] else None)
    except Exception as e:
        print("Fallo al inicializar la conexión:", e)
import os
import importlib
import logging

logger = logging.getLogger(__name__)


def init_db(mongo_uri=None, mongo_db=None):
	"""Inicializa o reconfigura la conexión a MongoDB para el paquete `Mongo`.

	Si `mongo_uri` o `mongo_db` se proporcionan, ajusta las variables de entorno
	y recarga el módulo `Mongo.mongo` para aplicar la nueva configuración.

	Retorna un dict con objetos: client, db, doctores, pacientes, expedientes
	"""
	if mongo_uri:
		os.environ["MONGO_URI"] = mongo_uri
	if mongo_db:
		os.environ["MONGO_DB"] = mongo_db

	try:
		# Importar y recargar el módulo para que use las variables de entorno
		from . import mongo as _mongo
		importlib.reload(_mongo)
		return {
			"client": _mongo.client,
			"db": _mongo.db,
			"doctores": _mongo.doctores,
			"pacientes": _mongo.pacientes,
			"expedientes": _mongo.expedientes,
		}
	except Exception as e:
		logger.error("Error inicializando Mongo: %s", e)
		raise


if __name__ == "__main__":
	# Uso rápido desde línea de comandos para verificar la conexión
	import argparse

	parser = argparse.ArgumentParser(description="Inicializar conexión a MongoDB para el paquete Mongo")
	parser.add_argument("--uri", help="MongoDB URI, p.ej. mongodb://localhost:27017/")
	parser.add_argument("--db", help="Nombre de la base de datos")
	args = parser.parse_args()

	try:
		cfg = init_db(mongo_uri=args.uri, mongo_db=args.db)
		print("Conexión establecida.")
		print("DB:", cfg["db"].name if cfg["db"] else None)
	except Exception as e:
		print("Fallo al inicializar la conexión:", e)
