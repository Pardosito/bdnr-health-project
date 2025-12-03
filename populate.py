import random
import uuid
from datetime import datetime, timedelta, date
from faker import Faker
import pydgraph

# Imports
from connect import get_mongo, get_cassandra, get_dgraph
from Mongo.services.doctors_service import registrar_doctor
from Mongo.services.pacientes_service import registrar_paciente
from Mongo.services.expediente_service import crear_expediente
from Cassandra import model
from Dgraph import dgraph as dg_utils
from Mongo.utils import get_doctor_by_id, get_paciente_by_id

fake = Faker('es_MX')

# --- DATOS MAESTROS ---
ESPECIALIDADES = ["Cardiología", "Pediatría", "Medicina General", "Neurología", "Dermatología", "Urgencias"]
PADECIMIENTOS = ["Diabetes Tipo 2", "Hipertensión", "Asma", "Migraña", "Artritis", "Gripe", "Infección Estomacal"]

MEDICAMENTOS = [
    {"nombre": "Paracetamol", "dosis": "500mg"},
    {"nombre": "Ibuprofeno", "dosis": "400mg"},
    {"nombre": "Metformina", "dosis": "850mg"},
    {"nombre": "Losartán", "dosis": "50mg"},
    {"nombre": "Salbutamol", "dosis": "100mcg"},
    {"nombre": "Amoxicilina", "dosis": "500mg"}
]


def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    txn = client.txn()
    try:
        txn.mutate(set_obj={"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]})
        txn.commit()
    finally:
        txn.discard()


def poblar_todo():
    print("🚀 Poblando todo (Mongo + Cassandra + Dgraph)...")

    # conexiones
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    if not mongo:
        print("❌ Mongo no conectado")
        return

    # --- RESET DGRAPH ---
    if dgraph:
        print("\n🧨 Reseteando Dgraph...")
        dgraph.alter(pydgraph.Operation(drop_all=True))
        dg_utils.set_schema()

    # ==========================================================
    # 1. MONDONGO
    # ==========================================================
    print("\n=== MONGO ===")

    lista_doctores = []
    lista_pacientes = []

    # Doctores
    for esp in ESPECIALIDADES:
        for _ in range(2):
            doc = {
                "nombre": "Dr. " + fake.name(),
                "especialidad": esp,
                "subespecialidad": "N/A",
                "cedula": str(fake.random_number(digits=8)),
                "telefono": fake.phone_number(),
                "correo": fake.email(),
                "consultorio": str(random.randint(100, 500))
            }
            doc_id = registrar_doctor(doc)
            mongo_doc = get_doctor_by_id(doc_id)

            if dgraph:
                uid = dg_utils.crear_doctor(
                    dgraph,
                    doc["nombre"],
                    str(doc_id),
                    esp
                )
            else:
                uid = None

            lista_doctores.append({
                **doc,
                "_id": str(doc_id),
                "dgraph_uid": uid
            })

            print("🩺 Doctor creado:", mongo_doc)

    # Pacientes
    for _ in range(30):
        pac = {
            "nombre": fake.name(),
            "fecha_nac": fake.date_of_birth(minimum_age=5, maximum_age=90).isoformat(),
            "sexo": random.choice(["M", "F"]),
            "telefono": fake.phone_number(),
            "correo": fake.email(),
            "cont_eme": fake.name(),
            "direccion": fake.address(),
            "seguro": "GNP",
            "poliza": str(fake.random_number(digits=10))
        }

        pac_id = registrar_paciente(pac)
        mongo_pac = get_paciente_by_id(pac_id)

        # CORREGIDO: expediente recibe SOLO EL ID
        crear_expediente(pac_id)

        if dgraph:
            edad = random.randint(5,90)
            uid = dg_utils.crear_paciente(dgraph, pac["nombre"], str(pac_id), edad, pac["direccion"])
        else:
            uid = None

        lista_pacientes.append({
            **pac,
            "_id": str(pac_id),
            "dgraph_uid": uid
        })

        print("🧍 Paciente creado:", mongo_pac)

    # ==========================================================
    # 2. CASSANDRA
    # ==========================================================
    print("\n=== CASSANDRA ===")

    if cassandra:
        for pac in lista_pacientes:
            for _ in range(random.randint(1,3)):
                doc = random.choice(lista_doctores)
                fecha = fake.date_between(start_date='-4m', end_date='today')
                visita_id = uuid.uuid1()

                # statements correctos según tu modelo (YA corregido)
                cassandra.execute(model.inicio_visita_stmt, [pac["_id"], doc["_id"], visita_id, uuid.uuid1()])
                cassandra.execute(model.INSERT_VISITA_DEL_DIA, [fecha, "Consulta", pac["_id"], doc["_id"], visita_id, uuid.uuid1()])

        print("📘 Cassandra poblado")

    # ==========================================================
    # 3. DGRAPH → CASOS DE PRUEBA
    # ==========================================================
    if dgraph:
        print("\n=== DGRAPH ===")

        # Condiciones
        mapa_cond = {}
        for c in PADECIMIENTOS:
            mapa_cond[c] = dg_utils.crear_condicion(
                dgraph,
                c,
                c == "Gripe"
            )

        # Medicamentos
        mapa_med = {}
        for m in MEDICAMENTOS:
            mapa_med[m["nombre"]] = dg_utils.crear_medicamento(
                dgraph,
                m["nombre"],
                m["dosis"]
            )

        # Interacción real
        dg_utils.crear_interaccion(dgraph, mapa_med["Losartán"], mapa_med["Ibuprofeno"])

        print("💊 Interacción Losartán ↔ Ibuprofeno creada.")

        # Sobredosis
        pac_s = lista_pacientes[0]
        docA = lista_doctores[0]
        docB = lista_doctores[1]
        u_para = mapa_med["Paracetamol"]

        t1 = dg_utils.crear_tratamiento(dgraph, "Dolor A", "5 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t1, u_para)
        dg_utils.relacionar_paciente_tratamiento(dgraph, pac_s["dgraph_uid"], t1)
        relacionar_doctor_tratamiento(dgraph, docA["dgraph_uid"], t1)

        t2 = dg_utils.crear_tratamiento(dgraph, "Dolor B", "5 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t2, u_para)
        dg_utils.relacionar_paciente_tratamiento(dgraph, pac_s["dgraph_uid"], t2)
        relacionar_doctor_tratamiento(dgraph, docB["dgraph_uid"], t2)

        print("⚠ Caso sobredosis creado.")

    print("\n✨ POBLACIÓN COMPLETADA")


if __name__ == "__main__":
    poblar_todo()
