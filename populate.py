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
from Mongo.services.expediente_service import agregar_padecimiento, agregar_alergia
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
    {"nombre": "Amoxicilina", "dosis": "500mg"},
    {"nombre": "Vitaminas", "dosis": "1p/día"},
    {"nombre": "Omeprazol", "dosis": "20mg"},
    {"nombre": "Loratadina", "dosis": "10mg"}
]

# --- HELPERS PARA RELACIONES DGRAPH ---

def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    """Crea la relación: Doctor --prescribe--> Tratamiento"""
    txn = client.txn()
    try:
        txn.mutate(set_obj={"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]})
        txn.commit()
    finally:
        txn.discard()

def relacionar_tratamiento_condicion(client, tratamiento_uid, condicion_uid):
    """Tratamiento -> para -> Condicion"""
    txn = client.txn()
    try:
        data = {"uid": tratamiento_uid, "para": [{"uid": condicion_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    finally:
        txn.discard()

def relacionar_paciente_alergia(client, paciente_uid, medicamento_uid):
    """Paciente -> es_alergico -> Medicamento"""
    txn = client.txn()
    try:
        data = {"uid": paciente_uid, "es_alergico": [{"uid": medicamento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    finally:
        txn.discard()


# --- LÓGICA DE CREACIÓN DE ESCENARIOS DGRAPH ---

def poblar_dgraph_escenarios(dgraph, lista_doctores, lista_pacientes, mapa_med, mapa_cond):
    print("\n=== DGRAPH - Creando Escenarios de Prueba ===")

    # ----------------------------------------------------
    # ESCENARIO 0: MEDICAMENTOS RECETADOS JUNTOS (QUERY 2)
    # Crear un tratamiento que tenga 3 medicamentos específicos para una condición
    # ----------------------------------------------------
    cond_asma_uid = mapa_cond["Asma"]["dgraph_uid"]
    t_combo = dg_utils.crear_tratamiento(dgraph, "Combo Asma Severo", "15 días")

    # Asignamos 3 medicamentos al mismo tratamiento
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_combo, mapa_med["Salbutamol"]["dgraph_uid"])
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_combo, mapa_med["Loratadina"]["dgraph_uid"])
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_combo, mapa_med["Vitaminas"]["dgraph_uid"])

    relacionar_tratamiento_condicion(dgraph, t_combo, cond_asma_uid)
    print(f"💊 Combo creado para Query 'Meds recetados juntos': Salbutamol + Loratadina + Vitaminas (para Asma)")


    # ----------------------------------------------------
    # ESCENARIO 1: INTERACCIÓN Y CONFLICTOS (Losartán <-> Ibuprofeno) (QUERY 4)
    # ----------------------------------------------------
    med_A_uid = mapa_med["Losartán"]["dgraph_uid"]
    med_B_uid = mapa_med["Ibuprofeno"]["dgraph_uid"]
    dg_utils.crear_interaccion(dgraph, med_A_uid, med_B_uid)
    print("💊 Interacción Losartán <-> Ibuprofeno creada.")

    paciente_conflicto = random.choice(lista_pacientes)
    doc_conflicto = random.choice(lista_doctores)

    # A) Forzar Alergia
    relacionar_paciente_alergia(dgraph, paciente_conflicto["dgraph_uid"], med_A_uid)
    agregar_alergia(paciente_conflicto["_id"], "Losartán")

    # B) Crear Tratamiento con conflicto
    t_conflicto = dg_utils.crear_tratamiento(dgraph, "Trat. Conflicto Aleatorio", "30 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_A_uid)
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_B_uid)

    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_conflicto["dgraph_uid"], t_conflicto)
    relacionar_doctor_tratamiento(dgraph, doc_conflicto["dgraph_uid"], t_conflicto)
    print(f"⚠ Conflicto forzado para: {paciente_conflicto['nombre']}")

    # ----------------------------------------------------
    # ESCENARIO 2: SOBREDOSIS (Mismo Med, 2 Doctores) (QUERY 7)
    # ----------------------------------------------------
    paciente_sobredosis = random.choice([p for p in lista_pacientes if p != paciente_conflicto])

    doc_sobredosis_A = lista_doctores[0]
    doc_sobredosis_B = lista_doctores[1]
    med_sobredosis = mapa_med["Paracetamol"]["dgraph_uid"]

    t_sobre_a = dg_utils.crear_tratamiento(dgraph, "Sobredosis A", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_a, med_sobredosis)
    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_a)
    relacionar_doctor_tratamiento(dgraph, doc_sobredosis_A["dgraph_uid"], t_sobre_a)

    t_sobre_b = dg_utils.crear_tratamiento(dgraph, "Sobredosis B", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_b, med_sobredosis)
    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_b)
    relacionar_doctor_tratamiento(dgraph, doc_sobredosis_B["dgraph_uid"], t_sobre_b)
    print(f"⚠ Caso Sobredosis forzado para: {paciente_sobredosis['nombre']}")

    # ----------------------------------------------------
    # ESCENARIO 3: SUGERENCIA SEGUNDA OPINIÓN (QUERY 3)
    # ----------------------------------------------------
    condicion_segunda = "Cardiología" # Usamos una especialidad como proxy de condición o una condición real
    cond_nombre = "Hipertensión"
    cond_uid = mapa_cond[cond_nombre]["dgraph_uid"]

    # Buscamos 2 doctores con la misma especialidad (ej. Cardiología)
    docs_cardio = [d for d in lista_doctores if d["especialidad"] == "Cardiología"]

    if len(docs_cardio) >= 2:
        doc_actual = docs_cardio[0]
        doc_sugerido = docs_cardio[1]
        paciente_segunda = random.choice(lista_pacientes)

        # Paciente diagnosticado y atendido por Doc A
        dg_utils.relacionar_paciente_condicion(dgraph, paciente_segunda["dgraph_uid"], cond_uid)
        dg_utils.relacionar_doctor_atiende(dgraph, doc_actual["dgraph_uid"], paciente_segunda["dgraph_uid"])

        # Doc B prescribe tratamiento para esa misma condición (lo hace elegible para sugerencia)
        t_sugerencia = dg_utils.crear_tratamiento(dgraph, "Control Experto Presión", "Permanent")
        relacionar_tratamiento_condicion(dgraph, t_sugerencia, cond_uid)
        relacionar_doctor_tratamiento(dgraph, doc_sugerido["dgraph_uid"], t_sugerencia)

        print(f"💡 Sugerencia preparada: {paciente_segunda['nombre']} atendido por {doc_actual['nombre']}, se sugerirá {doc_sugerido['nombre']}")

    # ----------------------------------------------------
    # ESCENARIO 4: PROPAGACIÓN CONTAGIOSA (QUERY 1)
    # ----------------------------------------------------
    cond_contagiosa_uid = mapa_cond["Gripe"]["dgraph_uid"]
    doc_contagioso = random.choice(lista_doctores)

    # Doctor prescribe para Gripe
    t_contagioso = dg_utils.crear_tratamiento(dgraph, "Trat. Antigripal", "7 días")
    relacionar_tratamiento_condicion(dgraph, t_contagioso, cond_contagiosa_uid)
    relacionar_doctor_tratamiento(dgraph, doc_contagioso["dgraph_uid"], t_contagioso)

    # Paciente Enfermo
    paciente_contagiado = random.choice(lista_pacientes)
    dg_utils.relacionar_paciente_condicion(dgraph, paciente_contagiado["dgraph_uid"], cond_contagiosa_uid)
    dg_utils.relacionar_doctor_atiende(dgraph, doc_contagioso["dgraph_uid"], paciente_contagiado["dgraph_uid"]) # Importante: el doctor lo atiende

    # Paciente Sano (En riesgo porque lo atiende el mismo doctor)
    paciente_riesgo = random.choice([p for p in lista_pacientes if p != paciente_contagiado])
    dg_utils.relacionar_doctor_atiende(dgraph, doc_contagioso["dgraph_uid"], paciente_riesgo["dgraph_uid"])

    print(f"🦠 Propagación: {doc_contagioso['nombre']} atiende a {paciente_contagiado['nombre']} (Enfermo) y a {paciente_riesgo['nombre']} (Riesgo).")

    # ----------------------------------------------------
    # ESCENARIO 5: POLIFARMACIA (QUERY 6)
    # ----------------------------------------------------
    paciente_poli = random.choice(lista_pacientes)
    for i in range(4): # 4 tratamientos > umbral 3
        t_poli = dg_utils.crear_tratamiento(dgraph, f"Trat. Extra {i}", "Vario")
        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_poli["dgraph_uid"], t_poli)
    print(f"📈 Polifarmacia forzada para: {paciente_poli['nombre']}")

    # ----------------------------------------------------
    # ESCENARIO 6: RED DE DOCTORES (QUERY 5)
    # Crear un doctor central y dos colegas que comparten pacientes con él
    # ----------------------------------------------------
    doc_central = lista_doctores[0]
    doc_colega1 = lista_doctores[1]
    doc_colega2 = lista_doctores[2]

    p_shared_1 = lista_pacientes[0]
    p_shared_2 = lista_pacientes[1]

    # Central y Colega 1 atienden a P1
    dg_utils.relacionar_doctor_atiende(dgraph, doc_central["dgraph_uid"], p_shared_1["dgraph_uid"])
    dg_utils.relacionar_doctor_atiende(dgraph, doc_colega1["dgraph_uid"], p_shared_1["dgraph_uid"])

    # Central y Colega 2 atienden a P2
    dg_utils.relacionar_doctor_atiende(dgraph, doc_central["dgraph_uid"], p_shared_2["dgraph_uid"])
    dg_utils.relacionar_doctor_atiende(dgraph, doc_colega2["dgraph_uid"], p_shared_2["dgraph_uid"])

    print(f"🕸 Red Doctor: {doc_central['nombre']} comparte pacientes con {doc_colega1['nombre']} y {doc_colega2['nombre']}.")


def poblar_todo():
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    if mongo is None:
        print("❌ Mongo no conectado")
        return

    # --- RESET DGRAPH ---
    if dgraph:
        print("\n🧨 Reseteando Dgraph...")
        dgraph.alter(pydgraph.Operation(drop_all=True))
        dg_utils.set_schema()

    # ==========================================================
    # 1. MONDONGO y ESTRUCTURA BASE
    # ==========================================================
    print("\n=== MONGO & DGRAPH BASE ===")

    lista_doctores = []
    lista_pacientes = []

    # Mapas para guardar los UIDs de dgraph y reutilizarlos
    mapa_especialidades_uid = {}
    mapa_cond = {}
    mapa_med = {}

    # 1. Crear Nodos de Especialidad en Dgraph (NECESARIO PARA QUERY 8)
    if dgraph:
        for esp_nombre in ESPECIALIDADES:
            uid = dg_utils.crear_especialidad(dgraph, esp_nombre)
            mapa_especialidades_uid[esp_nombre] = uid

    # 2. Doctores
    for esp in ESPECIALIDADES:
        for _ in range(random.randint(1, 2)):
            doc_data = {
                "nombre": "Dr. " + fake.first_name() + " " + fake.last_name(),
                "especialidad": esp,
                "subespecialidad": "N/A",
                "cedula": str(fake.random_number(digits=8)),
                "telefono": fake.phone_number(),
                "correo": fake.email(),
                "consultorio": str(random.randint(100, 500))
            }
            # Mongo
            doc_id = registrar_doctor(doc_data)

            # Dgraph
            uid = None
            if dgraph:
                uid = dg_utils.crear_doctor(dgraph, doc_data["nombre"], str(doc_id), esp)
                # VINCULAR DOCTOR -> ESPECIALIDAD (CRITICO)
                if esp in mapa_especialidades_uid:
                    dg_utils.relacionar_doctor_especialidad(dgraph, uid, mapa_especialidades_uid[esp])

            lista_doctores.append({**doc_data, "_id": str(doc_id), "dgraph_uid": uid})

    # 3. Pacientes
    for _ in range(15):
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
        crear_expediente(pac_id)

        uid = None
        if dgraph:
            edad = random.randint(5,90)
            uid = dg_utils.crear_paciente(dgraph, pac["nombre"], str(pac_id), edad, pac["direccion"])

        lista_pacientes.append({**pac, "_id": str(pac_id), "dgraph_uid": uid})

    print(f"🩺 {len(lista_doctores)} Doctores y 🧍 {len(lista_pacientes)} Pacientes creados.")

    # 4. Cassandra (Dummy run)
    if cassandra:
        print("📘 Cassandra inicializado.")

    # 5. DGRAPH - Entidades Base y Escenarios
    if dgraph:
        # Condiciones
        for c in PADECIMIENTOS:
            uid = dg_utils.crear_condicion(dgraph, c, c == "Gripe")
            mapa_cond[c] = {"nombre": c, "dgraph_uid": uid}

        # Medicamentos
        for m in MEDICAMENTOS:
            uid = dg_utils.crear_medicamento(dgraph, m["nombre"], m["dosis"])
            mapa_med[m["nombre"]] = {"nombre": m["nombre"], "dgraph_uid": uid}

        # EJECUTAR ESCENARIOS COMPLETOS
        poblar_dgraph_escenarios(dgraph, lista_doctores, lista_pacientes, mapa_med, mapa_cond)

    print("\n✨ POBLACIÓN COMPLETADA - LISTO PARA PROBAR TODOS LOS QUERIES")


if __name__ == "__main__":
    poblar_todo()