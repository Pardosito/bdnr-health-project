from bson import ObjectId
from .collections import get_collections


def registrar_doctor(data):
    doctores, _, _ = get_collections()
    result = doctores.insert_one(data)
    return str(result.inserted_id)


def buscar_doctor(id_o_nombre):
    doctores, _, _ = get_collections()
    if ObjectId.is_valid(id_o_nombre):
        return doctores.find_one({"_id": ObjectId(id_o_nombre)})
    return doctores.find_one({"nombre": {"$regex": id_o_nombre, "$options": "i"}})


def filtrar_por_especialidad(especialidad):
    doctores, _, _ = get_collections()
    return list(doctores.find(
        {"especialidad": especialidad},
        {"nombre": 1, "especialidad": 1, "subespecialidad": 1, "correo": 1, "consultorio": 1}
    ))
