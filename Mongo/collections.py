"""Getter perezoso de colecciones de Mongo para evitar problemas en import-time.

Provee `get_collections()` que devuelve (doctores, pacientes, expedientes).
Intentará (re)inicializar la conexión si las colecciones están en `None`.
"""
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def get_collections():
    try:
        from . import mongo as _mongo
    except Exception as e:
        logger.error("No se pudo importar Mongo.mongo: %s", e)
        raise

    # Si la importación no falló pero las colecciones son None, intentamos reinicializar
    if getattr(_mongo, 'doctores', None) is None or getattr(_mongo, 'pacientes', None) is None or getattr(_mongo, 'expedientes', None) is None:
        try:
            from . import init as _init
            _init.init_db()
            # recargar módulo mongo para obtener las colecciones actualizadas
            import importlib
            importlib.reload(_mongo)
        except Exception as e:
            logger.error("No se pudo inicializar/reconectar Mongo: %s", e)
            # Dejar que la excepción se propague para que el llamador la maneje
            raise

    return _mongo.doctores, _mongo.pacientes, _mongo.expedientes
