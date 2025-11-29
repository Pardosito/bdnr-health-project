"""Placeholder pipelines module.

Si tienes pipelines específicos para procesar datos antes de insertarlos en Mongo,
puedes implementar funciones aquí. Por ahora contiene helpers mínimos.
"""
from .collections import get_collections


def ensure_expediente_for_paciente(paciente_id):
    _, _, expedientes = get_collections()
    from bson import ObjectId
    if not expedientes.find_one({"paciente_id": ObjectId(paciente_id)}):
        expedientes.insert_one({"paciente_id": ObjectId(paciente_id), "alergias": [], "padecimientos": [], "tratamientos": []})
        return True
    return False
