from bson import ObjectId
from Mongo.mongo import doctores, pacientes

#doctores
def get_doctor_id(nombre: str):
    doc = doctores.find_one({"nombre": nombre})
    if not doc:
        return None
    return doc["_id"]

def get_doctor_by_id(doctor_id: str):

    if not ObjectId.is_valid(doctor_id):
        return "ID de doctor inválido"


    doc = doctores.find_one({"_id": ObjectId(doctor_id)})

    if not doc:
        return "Doctor no encontrado"
    return doc

#pacientes
def get_paciente_id(nombre: str):
    pac = pacientes.find_one({"nombre": nombre})
    if not pac:
        return None
    return pac["_id"]

def get_paciente_by_id(paciente_id: str):
    
    if not ObjectId.is_valid(paciente_id):
        return "ID de paciente inválido"


    pac = pacientes.find_one({"_id": ObjectId(paciente_id)})

    if not pac:
        return "Paciente no encontrado"
    return pac