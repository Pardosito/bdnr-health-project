from bson import ObjectId
import re
# No crear la conexión al importar: use siempre el parámetro `db` pasado a las funciones.

#Registro de doctor
def registrar_doctor(db, data):
    return db.doctores.insert_one(data).inserted_id


#búsqueda por ID
def buscar_doctor_por_id(db, id_str):
    try:
        return db.doctores.find_one({"_id": ObjectId(id_str)})
    except:
        return None


#búsqueda por nombre
def buscar_doctor_por_nombre(db, nombre):
    if db is None:
        print("[Mongo] Conexión no disponible al buscar doctor por nombre.")
        return None

    try:
        # Búsqueda flexible: permite fragmentos y no distingue mayúsculas/minúsculas
        pattern = ".*" + re.escape(nombre.strip()) + ".*"
        query = {"nombre": {"$regex": pattern, "$options": "i"}}
        doctor = db.doctores.find_one(query)
        return doctor
    except Exception as e:
        print(f"Errorsito: {e}")
        return None


#búsqueda de doctor por especialidad
def buscar_por_especialidad(db, especialidad):
    return list(
        db.doctores.find(
            {"especialidad": especialidad},
            {
                "nombre": 1,
                "especialidad": 1,
                "subespecialidad": 1,
                "correo": 1,
                "consultorio": 1
            }
        )
    )
