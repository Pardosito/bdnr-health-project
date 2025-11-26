from Mongo.mongo import pacientes, expedientes
from bson import ObjectId

def registrar_paciente(data):
    return str(pacientes.insert_one(data).inserted_id)

def consultar_paciente(id_o_nombre):
    if ObjectId.is_valid(id_o_nombre):
        paciente = pacientes.find_one({"_id": ObjectId(id_o_nombre)})
    else:
        paciente = pacientes.find_one({"nombre": {"$regex": id_o_nombre, "$options": "i"}})

    if not paciente:
        return None, None

    expediente = expedientes.find_one({"paciente_id": paciente["_id"]})
    return paciente, expediente

def filtrar_pacientes(filtros):
    resultados = []
    for p in pacientes.find(filtros):
        exp = expedientes.find_one({"paciente_id": p["_id"]})
        resultados.append({"paciente": p, "expediente": exp})
    return resultados

def obtener_info_medica(id_o_nombre):
    paciente, expediente = consultar_paciente(id_o_nombre)
    if not paciente:
        return None
    return {
        "nombre": paciente["nombre"],
        "alergias": expediente["alergias"] if expediente else "Sin expediente",
        "padecimientos": expediente["padecimientos"] if expediente else "Sin expediente",
        "tratamientos": expediente["tratamientos"] if expediente else "Sin expediente"
    }
