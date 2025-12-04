from connect import get_dgraph
import pydgraph
import json

#schema
schema = """
type Doctor {
    nombre
    id
    especialidad
    atiende
    tiene_especialidad
    prescribe
}

type Paciente {
    nombre
    id
    edad
    direccion
    diagnosticado_con
    recibe
    es_alergico
}

type Tratamiento {
    duracion
    tipo
    incluye
    para
}

type Medicamento {
    nombre
    dosis
    interactua_con
}

type Condicion {
    nombre
    contagioso
}

type Especialidad {
    nombre
}

nombre: string @index(exact, term) .
id: string @index(exact) .
especialidad: string @index(term) .
edad: int .
direccion: string .
duracion: string .
tipo: string .
dosis: string .
contagioso: bool @index(bool) .

atiende: [uid] @reverse .
tiene_especialidad: [uid] @reverse .
prescribe: [uid] @reverse .
diagnosticado_con: [uid] @reverse .
recibe: [uid] @reverse .
es_alergico: [uid] @reverse .
incluye: [uid] @reverse .
para: [uid] @reverse .
interactua_con: [uid] @reverse .
"""


#carga de schema
def set_schema():
    """
    Carga el schema completo que está arriba.
    Lo dejo simple, sin adornos.
    """
    client = get_dgraph()
    op = pydgraph.Operation(schema=schema)
    client.alter(op)
    print(">>> SCHEMA cargado con éxito <<<")


#Mutaciones

#crear doctor
def crear_doctor(client, nombre, id_code, especialidad):
    """
    Crea nodo tipo Doctor.
    Misma estructura que tú usas.
    """
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
        return res.uids.get("doctor")
    except Exception as e:
        print("Error creando doctor:", e)
    finally:
        txn.discard()


#crear paciente
def crear_paciente(client, nombre, id_code, edad, direccion):
    """
    Crear nodo Paciente.
    Conservando estilo.
    """
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
        return res.uids.get("paciente")
    except Exception as e:
        print("Error creando paciente:", e)
    finally:
        txn.discard()


#crear condicion
def crear_condicion(client, nombre, contagioso=False):
    """
    Crear nodo Condicion.
    Igual estilo.
    """
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
        return res.uids.get("cond")
    except Exception as e:
        print("Error creando condición:", e)
    finally:
        txn.discard()


#crear medicamento
def crear_medicamento(client, nombre, dosis):
    """
    Crear nodo Medicamento.
    Igual estructura.
    """
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
        return res.uids.get("med")
    except Exception as e:
        print("Error creando medicamento:", e)
    finally:
        txn.discard()


#crear tratamiento
def crear_tratamiento(client, tipo, duracion):
    """
    Crear nodo Tratamiento.
    Función pedida por ti, misma forma que las otras.
    """
    txn = client.txn()
    try:
        data = {
            "uid": "_:trat",
            "dgraph.type": "Tratamiento",
            "tipo": tipo,
            "duracion": duracion
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res.uids.get("trat")
    except Exception as e:
        print("Error creando tratamiento:", e)
    finally:
        txn.discard()


#funciones de relaciones
def relacionar_doctor_atiende(client, doctor_uid, paciente_uid):
    """
    Doctor → atiende → Paciente
    """
    txn = client.txn()
    try:
        data = {"uid": doctor_uid, "atiende": [{"uid": paciente_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        print(f"Doctor {doctor_uid} ahora atiende a Paciente {paciente_uid}")
    except Exception as e:
        print("Error relacionando doctor con paciente:", e)
    finally:
        txn.discard()


def relacionar_paciente_condicion(client, paciente_uid, condicion_uid):
    """
    Paciente → diagnosticado_con → Condicion
    """
    txn = client.txn()
    try:
        data = {"uid": paciente_uid, "diagnosticado_con": [{"uid": condicion_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        print(f"Paciente {paciente_uid} diagnosticado con {condicion_uid}")
    except Exception as e:
        print("Error paciente-condición:", e)
    finally:
        txn.discard()


def relacionar_tratamiento_medicamento(client, tratamiento_uid, medicamento_uid):
    """
    Tratamiento → incluye → Medicamento
    """
    txn = client.txn()
    try:
        data = {"uid": tratamiento_uid, "incluye": [{"uid": medicamento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        print(f"Tratamiento {tratamiento_uid} incluye Medicamento {medicamento_uid}")
    except Exception as e:
        print("Error tratamiento-medicamento:", e)
    finally:
        txn.discard()


def relacionar_paciente_tratamiento(client, paciente_uid, tratamiento_uid):
    """
    Paciente → recibe → Tratamiento
    """
    txn = client.txn()
    try:
        data = {"uid": paciente_uid, "recibe": [{"uid": tratamiento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        print(f"Paciente {paciente_uid} recibe Tratamiento {tratamiento_uid}")
    except Exception as e:
        print("Error paciente-tratamiento:", e)
    finally:
        txn.discard()


#carga de datos
def cargar_datos_ejemplo():
    """
    Crea nodos y relaciones para probar.
    Simple y directo.
    """
    client = get_dgraph()

    print("Cargando datos de ejemplo")

    # crear nodos
    d1 = crear_doctor(client, "Dr. Ricardo Montes", "D001", "Cardiología")
    p1 = crear_paciente(client, "Luis Fernández", "P001", 27, "Av. México 1450")
    c1 = crear_condicion(client, "Hipertensión", False)
    m1 = crear_medicamento(client, "Losartán", "50mg")
    t1 = crear_tratamiento(client, "Control presión arterial", "30 días")

    # relaciones
    relacionar_doctor_atiende(client, d1, p1)
    relacionar_paciente_condicion(client, p1, c1)
    relacionar_tratamiento_medicamento(client, t1, m1)
    relacionar_paciente_tratamiento(client, p1, t1)

    print("datos cargados.")

def crear_interaccion(client, med1_uid, med2_uid):
    """
    Crea una relación bidireccional de interacción entre dos medicamentos.
    Medicamento1 <--- interactua_con ---> Medicamento2
    """
    txn = client.txn()
    try:
        txn.mutate(set_obj={
            "uid": med1_uid,
            "interactua_con": [{"uid": med2_uid}]
        })

        txn.mutate(set_obj={
            "uid": med2_uid,
            "interactua_con": [{"uid": med1_uid}]
        })

        txn.commit()
        print(f"Interacción creada: {med1_uid} <-> {med2_uid}")
    except Exception as e:
        print("Error creando interacción:", e)
    finally:
        txn.discard()

def crear_especialidad(client, nombre):
    txn = client.txn()
    try:
        data = {
            "uid": "_:esp",
            "dgraph.type": "Especialidad",
            "nombre": nombre
        }
        res = txn.mutate(set_obj=data)
        txn.commit()
        return res.uids.get("esp")
    except Exception as e:
        print("Error creando especialidad:", e)
    finally:
        txn.discard()

def relacionar_doctor_especialidad(client, doctor_uid, especialidad_uid):
    txn = client.txn()
    try:
        data = {"uid": doctor_uid, "tiene_especialidad": [{"uid": especialidad_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    except Exception as e:
        print("Error relacionando doctor-especialidad:", e)
    finally:
        txn.discard()

def obtener_uid_por_id_mongo(client, mongo_id):
    query = """query q($mid: string) {
      nodo(func: eq(id, $mid)) {
        uid
      }
    }"""

    try:
        res = client.txn(read_only=True).query(query, variables={'$mid': str(mongo_id)})
        data = json.loads(res.json)
        if data.get('nodo'):
            return data['nodo'][0]['uid']
        return None
    except Exception as e:
        print(f"Error buscando UID por Mongo ID: {e}")
        return None

def obtener_uid_por_id_mongo(client, mongo_id):
    """
    Busca el UID de un nodo (Doctor o Paciente) usando el ID de MongoDB almacenado en el predicado 'id'.
    """
    query = """query q($mid: string) {
      nodo(func: eq(id, $mid)) {
        uid
      }
    }"""

    try:
        res = client.txn(read_only=True).query(query, variables={'$mid': str(mongo_id)})
        data = json.loads(res.json)
        if data.get('nodo'):
            return data['nodo'][0]['uid']
        return None
    except Exception as e:
        print(f"Error buscando UID por Mongo ID: {e}")
        return None