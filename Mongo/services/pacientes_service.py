from Mongo.mongo import pacientes, expedientes
from Mongo.utils import get_paciente_id
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

    return print(f"NOMBRE: {paciente['nombre']}, FECHA_NAC: {paciente['fecha_nac']}, SEXO: {paciente['sexo']}, TELEFONO: {paciente['telefono']}, CORREO: {paciente['correo']}, CONTACTO EMERGENCIA: {paciente['cont_eme']}, DIRECCION: {paciente['direccion']}, SEGURO: {paciente['seguro']}, POLIZA: {paciente['poliza']}")



#buscar pacientes por nombre
def buscar_paciente_por_nombre(nombre: str):
    """Busca paciente usando regex sobre nombre."""

    paciente = pacientes.find_one({"nombre": {"$regex": nombre, "$options": "i"}})

    if not paciente:
        return {"error": "Paciente no encontrado."}

    paciente["_id"] = str(paciente["_id"])
    return print(f"NOMBRE: {paciente['nombre']}, FECHA_NAC: {paciente['fecha_nac']}, SEXO: {paciente['sexo']}, TELEFONO: {paciente['telefono']}, CORREO: {paciente['correo']}, CONTACTO EMERGENCIA: {paciente['cont_eme']}, DIRECCION: {paciente['direccion']}, SEGURO: {paciente['seguro']}, POLIZA: {paciente['poliza']}")



#obtener expedientes junto con pacientes
def obtener_paciente_y_expediente(id_o_nombre: str):
    """Devuelve {paciente, expediente} según ID o nombre."""

    paciente = None

    if ObjectId.is_valid(id_o_nombre):
        paciente = pacientes.find_one({"_id": ObjectId(id_o_nombre)})
    else:
        paciente = pacientes.find_one({"nombre": {"$regex": id_o_nombre, "$options": "i"}})

    if not paciente:
        return "Paciente no encontrado."

    expediente = expedientes.find_one({"paciente_id": paciente["_id"]})

    nombre = paciente.get('nombre', 'N/A')
    fecha = paciente.get('fecha_nac', 'N/A')
    sexo = paciente.get('sexo', 'N/A')
    tel = paciente.get('telefono', 'N/A')
    correo = paciente.get('correo', 'N/A')
    eme = paciente.get('cont_eme', 'N/A')
    dir_ = paciente.get('direccion', 'N/A')
    seguro = paciente.get('seguro', 'N/A')
    poliza = paciente.get('poliza', 'N/A')

    if expediente:
        alergias = expediente.get('alergias', [])
        padecimientos = expediente.get('padecimientos', [])
        tratamientos = expediente.get('tratamientos', [])
        texto_expediente = f"ALERGIAS: {alergias}, PADECIMIENTOS: {padecimientos}, TRATAMIENTOS: {tratamientos}"
    else:
        texto_expediente = "Este paciente no tiene expediente."

    # 5. IMPRIMIR
    return print(
        f"NOMBRE: {nombre}, FECHA_NAC: {fecha}, SEXO: {sexo}, TELEFONO: {tel}, "
        f"CORREO: {correo}, CONTACTO EMERGENCIA: {eme}, DIRECCION: {dir_}, "
        f"SEGURO: {seguro}, POLIZA: {poliza}\n"
        f"EXPEDIENTE\n{texto_expediente}"
    )


# filtrar pacientes con cualquier campo
def filtrar_pacientes(filtros: dict):
    """Filtro genérico: edad, sexo, aseguradora, etc."""

    resultados = []

    for p in pacientes.find(filtros):
        p_id_obj = str(p["_id"])
        print(f"Buscando expediente para Paciente ID: {p_id_obj} (Tipo: {type(p_id_obj)})")
        exp = expedientes.find_one({"paciente_id": ObjectId(p["_id"])})

        if exp is None:
            print("❌ No se encontró expediente (Revisa si en Mongo 'paciente_id' es String o ObjectId)")
        else:
            print("✅ Expediente encontrado")

        resultados.append({"paciente": p, "expediente": exp})

    for item in resultados:
        pac = item["paciente"]
        exp = item["expediente"]

        alergias = exp["alergias"] if exp else "N/A"
        padeci = exp["padecimientos"] if exp else "N/A"
        trata = exp["tratamientos"] if exp else "N/A"

        print(
            f"NOMBRE: {pac['nombre']}, FECHA_NAC: {pac['fecha_nac']}, SEXO: {pac['sexo']}, "
            f"TELEFONO: {pac['telefono']}, CORREO: {pac['correo']}, "
            f"CONTACTO EMERGENCIA: {pac['cont_eme']}, DIRECCION: {pac['direccion']}, "
            f"SEGURO: {pac['seguro']}, POLIZA: {pac['poliza']}\n"
            f"EXPEDIENTE\n"
            f"ALERGIAS: {alergias}, PADECIMIENTOS: {padeci}, TRATAMIENTOS: {trata}\n"
            f"{'-'*50}"
        )



#obtener información médica
def obtener_info_medica(id_o_nombre: str):
    """Devuelve solo lo clínico: alergias, padecimientos, tratamientos."""

    paciente_id = get_paciente_id(id_o_nombre)
    if not paciente_id:
        return "Paciente no encontrado"

    expediente = expedientes.find_one({"paciente_id": paciente_id})
    if not expediente:
        return "Paciente no tiene expediente creado"

    paciente = buscar_paciente_por_id(paciente_id)

    return {
        "alergias": expediente["alergias"] if expediente else [],
        "padecimientos": expediente["padecimientos"] if expediente else [],
        "tratamientos": expediente["tratamientos"] if expediente else []
    }
