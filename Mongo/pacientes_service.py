from bson import ObjectId

#registro de paciente
def registrar_paciente(db, data):
    return db.pacientes.insert_one(data).inserted_id


#consultar paciente
def consultar_paciente(db, valor):
    try:
        obj = ObjectId(valor)
        doc = db.pacientes.find_one({"_id": obj})
        id_doc = doc["_id"]
        exp = db.expedientes.find_one({"paciente_id": id_doc})
        return doc, exp
    except Exception as e:
        print(f"Error consultando paciente: {e}")
