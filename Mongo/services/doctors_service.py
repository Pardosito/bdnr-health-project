from Mongo.mongo import doctores
from bson import ObjectId
from connect import get_dgraph
from Dgraph import dgraph as dg_utils

#reguistro de doctrores
def registrar_doctor(data: dict) -> str:
    result = doctores.insert_one(data)
    mongo_id = str(result.inserted_id)

    client = get_dgraph()
    if client:
        try:
            doc_uid = dg_utils.crear_doctor(
                client,
                data['nombre'],
                mongo_id,
                data['especialidad']
            )

            esp_uid = dg_utils.crear_especialidad(client, data['especialidad'])

            dg_utils.relacionar_doctor_especialidad(client, doc_uid, esp_uid)

            print(f"[Sync]")
        except Exception as e:
            print(f"[Sync Error]")

    return mongo_id


#búsqueda de doctor por ID
def buscar_doctor_por_id(doctor_id: str):
    """Busca un doctor usando su ObjectId."""
    if not ObjectId.is_valid(doctor_id):
        return {"error": "ID inválido."}

    doc = doctores.find_one({"_id": ObjectId(doctor_id)})
    if not doc:
        return {"error": "Doctor no encontrado."}

    return print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, SUBESPECIALIDAD: {doc['subespecialidad']}, CEDULA: {doc['cedula']}, TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, CONSULTORIO: {doc['consultorio']}")

#busqueda de doctor por nombre
def buscar_doctor_por_nombre(nombre: str):
    """Búsqueda flexible por nombre (regex)."""
    doc = doctores.find_one({"nombre": {"$regex": nombre, "$options": "i"}})
    if not doc:
        return {"error": "Doctor no encontrado."}
    else:
        return print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, SUBESPECIALIDAD: {doc['subespecialidad']}, CEDULA: {doc['cedula']}, TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, CONSULTORIO: {doc['consultorio']}")

#filtrado de doctores por especialidad
def buscar_por_especialidad(especialidad: str):
    """Devuelve todos los doctores que coincidan con la especialidad."""

    resultados = list(doctores.find(
        {"especialidad": {"$regex": especialidad, "$options": "i"}}
    ))

    if not resultados:
        return print("No hay doctores con esa especialidad.")

    print(f"--- Encontrados: {len(resultados)} doctores ---")

    for doc in resultados:
        print(f"NOMBRE: {doc['nombre']}, ESPECIALIDAD: {doc['especialidad']}, "
              f"SUBESPECIALIDAD: {doc.get('subespecialidad', 'N/A')}, CEDULA: {doc['cedula']}, "
              f"TELEFONO: {doc['telefono']}, CORREO: {doc['correo']}, "
              f"CONSULTORIO: {doc['consultorio']}")

    return