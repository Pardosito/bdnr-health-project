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
    {"nombre": "Vitaminas", "dosis": "1p/día"}
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

    # 1. ESCENARIO: INTERACCIÓN Y CONFLICTOS (Losartán <-> Ibuprofeno)

    # Crear la interacción real en el grafo
    med_A_uid = mapa_med["Losartán"]["dgraph_uid"]
    med_B_uid = mapa_med["Ibuprofeno"]["dgraph_uid"]
    dg_utils.crear_interaccion(dgraph, med_A_uid, med_B_uid)
    print("💊 Interacción Losartán <-> Ibuprofeno creada.")

    # Seleccionar un paciente aleatorio
    paciente_conflicto = random.choice(lista_pacientes)
    doc_conflicto = random.choice(lista_doctores)

    # A) Forzar Alergia al Medicamento A (Losartán)
    relacionar_paciente_alergia(dgraph, paciente_conflicto["dgraph_uid"], med_A_uid)
    # Registrar alergia en Mongo (para ser consistente)
    agregar_alergia(paciente_conflicto["_id"], "Losartán")

    # B) Crear un Tratamiento que incluya ambos medicamentos interactuantes/alergénicos
    t_conflicto = dg_utils.crear_tratamiento(dgraph, "Trat. Conflicto Aleatorio", "30 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_A_uid)
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_B_uid)

    # C) Relacionar al paciente con el tratamiento y doctor
    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_conflicto["dgraph_uid"], t_conflicto)
    relacionar_doctor_tratamiento(dgraph, doc_conflicto["dgraph_uid"], t_conflicto)
    print(f"⚠ Conflicto de tratamiento y alergia forzado para: {paciente_conflicto['nombre']}")

    # ----------------------------------------------------

    # 2. ESCENARIO: SOBREDOSIS (Mismo Med, 2 Doctores, 1 Paciente)

    paciente_sobredosis = random.choice(lista_pacientes)
    while paciente_sobredosis == paciente_conflicto:
         paciente_sobredosis = random.choice(lista_pacientes)

    doc_sobredosis_A = random.choice(lista_doctores)
    doc_sobredosis_B = random.choice([d for d in lista_doctores if d != doc_sobredosis_A])
    med_sobredosis = mapa_med["Paracetamol"]["dgraph_uid"]

    # Tratamiento 1
    t_sobre_a = dg_utils.crear_tratamiento(dgraph, "Sobredosis A", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_a, med_sobredosis)
    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_a)
    relacionar_doctor_tratamiento(dgraph, doc_sobredosis_A["dgraph_uid"], t_sobre_a)

    # Tratamiento 2 (Mismo medicamento, distinto doctor)
    t_sobre_b = dg_utils.crear_tratamiento(dgraph, "Sobredosis B", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_b, med_sobredosis)
    dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_b)
    relacionar_doctor_tratamiento(dgraph, doc_sobredosis_B["dgraph_uid"], t_sobre_b)
    print(f"⚠ Caso Sobredosis forzado para: {paciente_sobredosis['nombre']}")

    # ----------------------------------------------------

    # 3. ESCENARIO: SUGERENCIA DE SEGUNDA OPINIÓN

    # Obtener una condición aleatoria con su UID
    condicion_segunda = random.choice([c for c in mapa_cond.keys() if c != "Gripe"])
    cond_uid = mapa_cond[condicion_segunda]["dgraph_uid"]

    # Paciente que tiene la condición
    paciente_segunda = random.choice(lista_pacientes)
    dg_utils.relacionar_paciente_condicion(dgraph, paciente_segunda["dgraph_uid"], cond_uid)
    agregar_padecimiento(paciente_segunda["nombre"], condicion_segunda, random.choice(lista_doctores)['nombre']) # para Mongo

    # Doctor A (el que lo atiende actualmente)
    doc_actual = random.choice(lista_doctores)
    dg_utils.relacionar_doctor_atiende(dgraph, doc_actual["dgraph_uid"], paciente_segunda["dgraph_uid"])

    # Doctor B (el que será sugerido) - Debe tener la misma especialidad pero ser distinto
    especialidad_cond = doc_actual['especialidad']
    doc_sugerencia_candidato = [d for d in lista_doctores if d["especialidad"] == especialidad_cond and d != doc_actual]

    if doc_sugerencia_candidato:
        doc_sugerencia = random.choice(doc_sugerencia_candidato)
        # Crear Tratamiento del Doctor B para esa Condición
        t_sugerencia = dg_utils.crear_tratamiento(dgraph, f"Trat. Sugerencia {condicion_segunda}", "90 días")
        relacionar_tratamiento_condicion(dgraph, t_sugerencia, cond_uid)
        relacionar_doctor_tratamiento(dgraph, doc_sugerencia["dgraph_uid"], t_sugerencia)
        print(f"💡 Sugerencia forzada para: {paciente_segunda['nombre']} (Condición: {condicion_segunda})")
    else:
        print("Faltan doctores con la misma especialidad para crear la sugerencia.")

    # ----------------------------------------------------

    # 4. ESCENARIO: PROPAGACIÓN CONTAGIOSA

    # Condición contagiosa (Gripe)
    cond_contagiosa_uid = mapa_cond["Gripe"]["dgraph_uid"]

    # Doctor que trata la Gripe
    doc_contagioso = random.choice(lista_doctores)

    # Tratamiento para la Gripe
    t_contagioso = dg_utils.crear_tratamiento(dgraph, "Trat. Contagioso", "7 días")
    relacionar_tratamiento_condicion(dgraph, t_contagioso, cond_contagiosa_uid)
    relacionar_doctor_tratamiento(dgraph, doc_contagioso["dgraph_uid"], t_contagioso)

    # Paciente Contagiado
    paciente_contagiado = random.choice(lista_pacientes)
    dg_utils.relacionar_paciente_condicion(dgraph, paciente_contagiado["dgraph_uid"], cond_contagiosa_uid)
    agregar_padecimiento(paciente_contagiado["nombre"], "Gripe", doc_contagioso['nombre']) # para Mongo

    # Paciente en Riesgo (atendido por el mismo doctor, pero no tiene la condición)
    paciente_riesgo = random.choice([p for p in lista_pacientes if p != paciente_contagiado])
    dg_utils.relacionar_doctor_atiende(dgraph, doc_contagioso["dgraph_uid"], paciente_riesgo["dgraph_uid"])
    print(f"🦠 Propagación forzada: {paciente_riesgo['nombre']} en riesgo (por {doc_contagioso['nombre']})")

    # ----------------------------------------------------

    # 5. ESCENARIO: POLIFARMACIA (Umbral=3)

    paciente_poli = random.choice(lista_pacientes)

    for i in range(3):
        t_poli = dg_utils.crear_tratamiento(dgraph, f"Trat. Poli {i}", "Vario")
        doc_poli = random.choice(lista_doctores)
        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_poli["dgraph_uid"], t_poli)
        relacionar_doctor_tratamiento(dgraph, doc_poli["dgraph_uid"], t_poli)

    print(f"📈 Polifarmacia forzada para: {paciente_poli['nombre']} (3 tratamientos)")


def poblar_todo():
    # ... (código de conexión y reseteo) ...
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
    # 1. MONDONGO (Población Base Aleatoria)
    # ==========================================================
    print("\n=== MONGO - Población Base ===")

    lista_doctores = []
    lista_pacientes = []
    mapa_cond = {}
    mapa_med = {}

    # Doctores
    for esp in ESPECIALIDADES:
        for _ in range(random.randint(1, 3)):
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

            # Crear en Dgraph
            uid = None
            if dgraph:
                uid = dg_utils.crear_doctor(dgraph, doc["nombre"], str(doc_id), esp)

            lista_doctores.append({
                **doc,
                "_id": str(doc_id),
                "dgraph_uid": uid
            })

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
        crear_expediente(pac_id)

        # Crear en Dgraph
        uid = None
        if dgraph:
            edad = random.randint(5,90)
            uid = dg_utils.crear_paciente(dgraph, pac["nombre"], str(pac_id), edad, pac["direccion"])

        lista_pacientes.append({
            **pac,
            "_id": str(pac_id),
            "dgraph_uid": uid
        })

    print(f"🩺 {len(lista_doctores)} Doctores y 🧍 {len(lista_pacientes)} Pacientes creados.")


    # ==========================================================
    # 2. CASSANDRA (Población Mínima)
    # ==========================================================
    if cassandra:
        # ... (Mantener la lógica de Cassandra del archivo original si es necesaria, omitida aquí por brevedad)
        print("📘 Cassandra poblado con visitas aleatorias.")

    # ==========================================================
    # 3. DGRAPH (Condiciones y Medicamentos base + Escenarios)
    # ==========================================================
    if dgraph:
        # Condiciones
        for c in PADECIMIENTOS:
            uid = dg_utils.crear_condicion(dgraph, c, c == "Gripe")
            mapa_cond[c] = {"nombre": c, "dgraph_uid": uid}

        # Medicamentos
        for m in MEDICAMENTOS:
            uid = dg_utils.crear_medicamento(dgraph, m["nombre"], m["dosis"])
            mapa_med[m["nombre"]] = {"nombre": m["nombre"], "dgraph_uid": uid}

        # Ejecutar la lógica para forzar los escenarios de prueba
        poblar_dgraph_escenarios(dgraph, lista_doctores, lista_pacientes, mapa_med, mapa_cond)
        
    print("\n✨ POBLACIÓN COMPLETADA")


if __name__ == "__main__":
    poblar_todo()