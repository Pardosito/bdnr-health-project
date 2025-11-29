from bson import ObjectId

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
    return list(db.doctores.find({"nombre": nombre}))


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
