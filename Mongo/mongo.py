import os
import logging
from pymongo import MongoClient

logging.basicConfig()
logger = logging.getLogger(__name__)


def _connect():
	"""Crear una conexión a MongoDB usando variables de entorno.

	Variables utilizadas:
	- MONGO_URI: URI de conexión (por defecto mongodb://localhost:27017)
	- MONGO_DB: nombre de la base de datos (por defecto health_platform)
	"""
	uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
	db_name = os.getenv("MONGO_DB", "health_platform")

	try:
		client = MongoClient(uri, serverSelectionTimeoutMS=5000)
		# Forzar la selección del servidor para detectar errores pronto
		client.admin.command('ping')
	except Exception as e:
		logger.error("No se pudo conectar a MongoDB en %s: %s", uri, e)
		raise

	db = client[db_name]

	# Collections
	doctores = db["doctores"]
	pacientes = db["pacientes"]
	expedientes = db["expedientes"]

	# Índices (creación idempotente)
	try:
		doctores.create_index("nombre")
		doctores.create_index("especialidad")
		pacientes.create_index("nombre")
		pacientes.create_index("fecha_nac")
		expedientes.create_index("paciente_id")
		expedientes.create_index("padecimientos")
	except Exception as e:
		logger.warning("No fue posible crear índices: %s", e)

	return client, db, doctores, pacientes, expedientes


# Conexión por defecto al importar el módulo
try:
	client, db, doctores, pacientes, expedientes = _connect()
except Exception:
	# Si la conexión falla en la importación, dejamos las variables como None
	client = None
	db = None
	doctores = None
	pacientes = None
	expedientes = None