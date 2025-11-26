from Mongo.mongo import doctores
from bson import ObjectId

def registrar_doctor(data):
    result = doctores.insert_one(data)
    return str(result.inserted_id)

def buscar_doctor(id_o_nombre):
    if ObjectId.is_valid(id_o_nombre):
        return doctores.find_one({"_id": ObjectId(id_o_nombre)})
    return doctores.find_one({"nombre": {"$regex": id_o_nombre, "$options": "i"}})

def filtrar_por_especialidad(especialidad):
    return list(doctores.find(
        {"especialidad": especialidad},
        {"nombre": 1, "especialidad": 1, "subespecialidad": 1, "correo": 1, "consultorio": 1}
    ))
