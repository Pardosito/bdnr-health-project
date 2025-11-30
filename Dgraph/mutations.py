#crear doctor
def crear_doctor(client, nombre, id_code, especialidad):
    txn = client.txn()
    try:
        data = {
            "uid": "_:doctor",
            "dgraph.type": "Doctor",
            "nombre": nombre,
            "id": id_code,
            "especialidad": especialidad
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res
    except Exception as e:
        print("Error creando doctor:", e)
    finally:
        txn.discard()


#crear paciente
def crear_paciente(client, nombre, id_code, edad, direccion):
    txn = client.txn()
    try:
        data = {
            "uid": "_:paciente",
            "dgraph.type": "Paciente",
            "nombre": nombre,
            "id": id_code,
            "edad": edad,
            "direccion": direccion
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res
    except Exception as e:
        print("Error creando paciente:", e)
    finally:
        txn.discard()


#crear condicion
def crear_condicion(client, nombre, contagioso=False):
    txn = client.txn()
    try:
        data = {
            "uid": "_:cond",
            "dgraph.type": "Condicion",
            "nombre": nombre,
            "contagioso": contagioso
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res
    except Exception as e:
        print("Error creando condición:", e)
    finally:
        txn.discard()


#crear medicamento
def crear_medicamento(client, nombre, dosis):
    txn = client.txn()
    try:
        data = {
            "uid": "_:med",
            "dgraph.type": "Medicamento",
            "nombre": nombre,
            "dosis": dosis
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res
    except Exception as e:
        print("Error creando medicamento:", e)
    finally:
        txn.discard()
