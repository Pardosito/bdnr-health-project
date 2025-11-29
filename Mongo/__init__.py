"""Compatibilidad de paquete `mongo` en minúsculas.

Este paquete replica el contenido de la carpeta `Mongo/` pero con nombre
en minúsculas según la petición del proyecto.
"""
from . import init as init
from . import mongo as mongo
from . import collections as collections
from . import pacientes_services as pacientes_services
from . import doctors_service as doctors_service
from . import expedientes_services as expedientes_services
from . import pipelines as pipelines

__all__ = [
    'init', 'mongo', 'collections', 'pacientes_services', 'doctors_service', 'expedientes_services', 'pipelines'
]
