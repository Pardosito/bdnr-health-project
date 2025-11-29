from bson import ObjectId
from .collections import get_collections


def registrar_paciente(data):
    _, pacientes, _ = get_collections()
    return str(pacientes.insert_one(data).inserted_id)


def consultar_paciente(id_o_nombre):
    _, pacientes, expedientes = get_collections()

    if ObjectId.is_valid(id_o_nombre):
        paciente = pacientes.find_one({"_id": ObjectId(id_o_nombre)})
    else:
        paciente = pacientes.find_one({"nombre": {"$regex": id_o_nombre, "$options": "i"}})

    if not paciente:
        return None, None

    expediente = expedientes.find_one({"paciente_id": paciente["_id"]})
    return paciente, expediente


def filtrar_pacientes(filtros):
    _, pacientes, expedientes = get_collections()
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
        "nombre": paciente.get("nombre"),
        "alergias": expediente.get("alergias") if expediente else "Sin expediente",
        "padecimientos": expediente.get("padecimientos") if expediente else "Sin expediente",
        "tratamientos": expediente.get("tratamientos") if expediente else "Sin expediente"
    }
