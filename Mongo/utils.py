from connect import get_mongo
from bson import ObjectId

mongo = get_mongo()


def _ensure_objectid(value):
    """Return an ObjectId if `value` looks like one, otherwise return value unchanged."""
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return value


def get_paciente_id(nombre):
    """Return the paciente _id as a string, or None if not found."""
    try:
        if mongo is None:
            print("[Mongo] Conexión no disponible en get_paciente_id")
            return None
        paciente = mongo.pacientes.find_one({"nombre": nombre})
        if paciente and "_id" in paciente:
            return str(paciente["_id"])
        return None
    except Exception as e:
        print(f"Error get_paciente_id: {e}")
        return None


def get_doctor_id(nombre):
    """Return the doctor _id as a string, or None if not found."""
    try:
        if mongo is None:
            print("[Mongo] Conexión no disponible en get_doctor_id")
            return None
        doctor = mongo.doctores.find_one({"nombre": nombre})
        if doctor and "_id" in doctor:
            return str(doctor["_id"])
        return None
    except Exception as e:
        print(f"Error get_doctor_id: {e}")
        return None


def get_paciente_by_id(id_value):
    """Accept either ObjectId or string id; return paciente nombre or None."""
    try:
        if mongo is None:
            print("[Mongo] Conexión no disponible en get_paciente_by_id")
            return None
        obj = _ensure_objectid(id_value)
        paciente = mongo.pacientes.find_one({"_id": obj})
        return paciente["nombre"] if paciente and "nombre" in paciente else None
    except Exception as e:
        print(f"Id no encontrado: {e}")
        return None


def get_doctor_by_id(id_value):
    """Accept either ObjectId or string id; return doctor nombre or None."""
    try:
        if mongo is None:
            print("[Mongo] Conexión no disponible en get_doctor_by_id")
            return None
        obj = _ensure_objectid(id_value)
        doctor = mongo.doctores.find_one({"_id": obj})
        return doctor["nombre"] if doctor and "nombre" in doctor else None
    except Exception as e:
        print(f"Id no encontrado: {e}")
        return None