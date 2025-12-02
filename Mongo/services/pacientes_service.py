from Mongo.mongo import pacientes, expedientes
from bson import ObjectId

#registrar pacientes
def registrar_paciente(data: dict) -> str:
    """Registra un nuevo paciente y devuelve su ID."""
    result = pacientes.insert_one(data)
    return str(result.inserted_id)

#buscar pacientes por ID
def buscar_paciente_por_id(paciente_id: str):
    """Devuelve el documento del paciente usando su ObjectId."""

    if not ObjectId.is_valid(paciente_id):
        return {"error": "ID inválido."}

    paciente = pacientes.find_one({"_id": ObjectId(paciente_id)})

    if not paciente:
        return {"error": "Paciente no encontrado."}

    paciente["_id"] = str(paciente["_id"])
    return paciente



#buscar pacientes por nombre
def buscar_paciente_por_nombre(nombre: str):
    """Busca paciente usando regex sobre nombre."""

    paciente = pacientes.find_one({"nombre": {"$regex": nombre, "$options": "i"}})

    if not paciente:
        return {"error": "Paciente no encontrado."}

    paciente["_id"] = str(paciente["_id"])
    return paciente



#obtener expedientes junto con pacientes
def obtener_paciente_y_expediente(id_o_nombre: str):
    """Devuelve {paciente, expediente} según ID o nombre."""

    # Selección automática según formato
    paciente = (
        buscar_paciente_por_id(id_o_nombre)
        if ObjectId.is_valid(id_o_nombre)
        else buscar_paciente_por_nombre(id_o_nombre)
    )

    if "error" in paciente:
        return {"error": paciente["error"]}

    # Obtener expediente
    expediente = expedientes.find_one({"paciente_id": ObjectId(paciente["_id"])})

    # Convertir ids si existe expediente
    if expediente:
        expediente["_id"] = str(expediente["_id"])
        expediente["paciente_id"] = str(expediente["paciente_id"])

    return {"paciente": paciente, "expediente": expediente}



# filtrar pacientes con cualquier campo
def filtrar_pacientes(filtros: dict):
    """Filtro genérico: edad, sexo, aseguradora, etc."""

    resultados = []

    for p in pacientes.find(filtros):
        p["_id"] = str(p["_id"])
        exp = expedientes.find_one({"paciente_id": ObjectId(p["_id"])})

        if exp:
            exp["_id"] = str(exp["_id"])
            exp["paciente_id"] = str(exp["paciente_id"])

        resultados.append({"paciente": p, "expediente": exp})

    return resultados



#obtener información médica
def obtener_info_medica(id_o_nombre: str):
    """Devuelve solo lo clínico: alergias, padecimientos, tratamientos."""

    datos = obtener_paciente_y_expediente(id_o_nombre)

    if "error" in datos:
        return datos

    paciente = datos["paciente"]
    expediente = datos["expediente"]

    return {
        "nombre": paciente["nombre"],
        "alergias": expediente["alergias"] if expediente else [],
        "padecimientos": expediente["padecimientos"] if expediente else [],
        "tratamientos": expediente["tratamientos"] if expediente else []
    }
