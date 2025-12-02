import random
import uuid
from datetime import datetime, timedelta, date
from faker import Faker
import pydgraph

# Imports de tus módulos
from connect import get_mongo, get_cassandra, get_dgraph
from Mongo.doctor_service import registrar_doctor
from Mongo.services.pacientes_service import registrar_paciente
from Mongo.services.expediente_service import crear_expediente
from Cassandra import model
from Dgraph import dgraph as dg_utils
from Mongo.utils import get_doctor_by_id, get_paciente_by_id

fake = Faker('es_MX')

# --- DATOS MAESTROS AMPLIADOS ---
ESPECIALIDADES = ["Cardiología", "Pediatría", "Medicina General", "Neurología", "Dermatología", "Urgencias"]
PADECIMIENTOS = ["Diabetes Tipo 2", "Hipertensión", "Asma", "Migraña", "Artritis", "Gripe", "Infección Estomacal"]

# Definimos medicamentos con sus interacciones conocidas para probar
MEDICAMENTOS = [
    {"nombre": "Paracetamol", "dosis": "500mg"},
    {"nombre": "Ibuprofeno", "dosis": "400mg"},
    {"nombre": "Metformina", "dosis": "850mg"},
    {"nombre": "Losartán", "dosis": "50mg"},
    {"nombre": "Salbutamol", "dosis": "100mcg"},
    {"nombre": "Amoxicilina", "dosis": "500mg"}
]

# Función auxiliar local para Dgraph (por si falta en tu utils)
def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    txn = client.txn()
    try:
        data = {"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
    finally:
        txn.discard()

def poblar_todo():
    print("🚀 Iniciando población de datos AVANZADA...")

    db_mongo = get_mongo()
    session_cass = get_cassandra()
    client_dgraph = get_dgraph()

    if db_mongo == None and session_cass == None and client_dgraph == None:
        print("❌ Error: Faltan conexiones.")
        return

    # Limpieza Dgraph
    op = pydgraph.Operation(drop_all=True)
    client_dgraph.alter(op)
    dg_utils.set_schema()

    # ==========================================
    # FASE 1: MONDONGO (Usuarios Base)
    # ==========================================
    print("\n--- Fase 1: MongoDB ---")

    lista_doctores = []
    lista_pacientes = []

    # 1.1 Doctores
    for esp in ESPECIALIDADES:
        for _ in range(2): # 2 docs por especialidad
            doc_data = {
                "nombre": "Dr. " + fake.first_name() + " " + fake.last_name(),
                "especialidad": esp,
                "subespecialidad": "N/A",
                "cedula": str(fake.random_number(digits=8)),
                "telefono": fake.phone_number(),
                "correo": fake.email(),
                "consultorio": str(random.randint(100, 500))
            }
            doc_id = registrar_doctor(db_mongo, doc_data)
            print(f"id: {doc_id} nombre: {get_doctor_by_id(doc_id)}")

            # Dgraph
            dg_uid = dg_utils.crear_doctor(client_dgraph, doc_data["nombre"], str(doc_id), esp)
            lista_doctores.append({**doc_data, "_id": str(doc_id), "dgraph_uid": dg_uid})

    # 1.2 Pacientes (Generamos 30 para tener volumen)
    for i in range(30):
        pac_data = {
            "nombre": fake.first_name() + " " + fake.last_name(),
            "fecha_nac": fake.date_of_birth(minimum_age=5, maximum_age=90).isoformat(),
            "sexo": random.choice(["M", "F"]),
            "telefono": fake.phone_number(),
            "correo": fake.email(),
            "cont_eme": fake.name(),
            "direccion": fake.address(),
            "seguro": "GNP",
            "poliza": str(fake.random_number(digits=10))
        }
        pac_id = registrar_paciente(db_mongo, pac_data)
        print(f"id: {pac_id} nombre: {get_paciente_by_id(pac_id)}")

        # Dgraph
        edad = random.randint(5, 90)
        dg_uid = dg_utils.crear_paciente(client_dgraph, pac_data["nombre"], str(pac_id), edad, pac_data["direccion"])

        # Crear expediente vacío en Mongo
        crear_expediente(db_mongo, {"paciente_id": pac_id, "alergias": [], "padecimientos": [], "tratamientos": []})

        lista_pacientes.append({**pac_data, "_id": str(pac_id), "dgraph_uid": dg_uid})

    print(f"✅ Creados {len(lista_doctores)} doctores y {len(lista_pacientes)} pacientes.")


    # ==========================================
    # FASE 2: CASSANDRA (Historial Completo)
    # ==========================================
    print("\n--- Fase 2: Cassandra (Visitas, Recetas, Signos) ---")

    # Preparar statements
    stmt_historia = session_cass.prepare(model.inicio_visita_stmt)
    stmt_agenda   = session_cass.prepare(model.INSERT_VISITA_DEL_DIA)
    stmt_receta   = session_cass.prepare(model.recete_medica_registro_stmt)
    stmt_diag     = session_cass.prepare(model.INSERT_DIAGNOSTICO)
    stmt_signos   = session_cass.prepare(model.signo_vital_registro_stmt) # ¡NUEVO!

    for paciente in lista_pacientes:
        # Cada paciente tiene entre 1 y 5 visitas
        for _ in range(random.randint(1, 5)):
            doctor = random.choice(lista_doctores)
            fecha_visita = fake.date_between(start_date='-6m', end_date='today')
            visita_uuid = uuid.uuid1()

            # 1. Registrar Visita
            print(session_cass.execute(stmt_historia, [paciente["_id"], doctor["_id"], visita_uuid, uuid.uuid1()]))
            print(session_cass.execute(stmt_agenda, [fecha_visita, "Consulta General", paciente["_id"], doctor["_id"], visita_uuid, uuid.uuid1()]))

            # 2. Registrar Signos Vitales (¡DATOS NUEVOS!)
            # Generamos datos realistas
            signos = [
                ("TEMPERATURA", f"{random.uniform(36.0, 39.5):.1f}"),
                ("PRESION", f"{random.randint(110, 140)}/{random.randint(70, 90)}"),
                ("RITMO_CARDIACO", str(random.randint(60, 100))),
                ("OXIGENO", str(random.randint(90, 99)))
            ]
            for tipo, valor in signos:
                print(f"{tipo}, {valor}")
                session_cass.execute(stmt_signos, [paciente["_id"], doctor["_id"], str(visita_uuid), tipo, valor, uuid.uuid1()])

            # 3. Recetas y Diagnósticos (Aleatorios base)
            if random.random() > 0.4:
                med = random.choice(MEDICAMENTOS)
                print(session_cass.execute(stmt_receta, [paciente["_id"], doctor["_id"], str(visita_uuid), f"{med['nombre']} {med['dosis']}"]))
                print(session_cass.execute(stmt_diag, [paciente["_id"], doctor["_id"], str(visita_uuid), random.choice(PADECIMIENTOS), fecha_visita]))

    print("✅ Cassandra poblado con visitas y signos vitales.")


    # ==========================================
    # FASE 3: DGRAPH (Escenarios de Prueba)
    # ==========================================
    print("\n--- Fase 3: Dgraph (Escenarios Específicos) ---")

    # 3.1 Nodos Base
    mapa_cond = {}
    for c in PADECIMIENTOS:
        es_contagioso = (c == "Gripe")
        mapa_cond[c] = dg_utils.crear_condicion(client_dgraph, c, es_contagioso)

    mapa_meds = {}
    for m in MEDICAMENTOS:
        mapa_meds[m["nombre"]] = dg_utils.crear_medicamento(client_dgraph, m["nombre"], m["dosis"])

    # CREAR INTERACCIÓN REAL: Losartán <-> Ibuprofeno
    # (Para probar 'Detectar conflictos de tratamiento')
    u_losartan = mapa_meds["Losartán"]
    u_ibuprofeno = mapa_meds["Ibuprofeno"]

    txn = client_dgraph.txn()
    try:
        # Relación bidireccional manual
        txn.mutate(set_obj={"uid": u_losartan, "interactua_con": [{"uid": u_ibuprofeno}]})
        txn.mutate(set_obj={"uid": u_ibuprofeno, "interactua_con": [{"uid": u_losartan}]})
        txn.commit()
    finally:
        txn.discard()
    print("   🔹 Interacción creada: Losartán <-> Ibuprofeno")

    # ----------------------------
    # Preparar datos para Query 24: medicamentos recetados juntos
    # Creamos 2 tratamientos asociados a una condición (p.ej. 'Migraña')
    # y hacemos que cada tratamiento incluya varios medicamentos.
    # Esto garantiza que la consulta: Condicion <- para - Tratamiento - incluye -> Medicamento
    # encuentre resultados.
    cond_target = None
    if "Migraña" in mapa_cond:
        cond_target = "Migraña"
    else:
        # fallback: primera condición disponible
        cond_target = list(mapa_cond.keys())[0]

    cond_uid = mapa_cond[cond_target]
    print(f"   🔸 Creando tratamientos de prueba para la condición '{cond_target}' (uid={cond_uid})")

    # Tratamiento A: Paracetamol + Ibuprofeno
    t_a = dg_utils.crear_tratamiento(client_dgraph, "Tratamiento A - Dolor", "7 días")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_a, mapa_meds.get("Paracetamol"))
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_a, mapa_meds.get("Ibuprofeno"))

    # Tratamiento B: Paracetamol + Amoxicilina
    t_b = dg_utils.crear_tratamiento(client_dgraph, "Tratamiento B - Infeccioso", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_b, mapa_meds.get("Paracetamol"))
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_b, mapa_meds.get("Amoxicilina"))

    # Relacionar ambos tratamientos con la condición (Tratamiento --para--> Condicion)
    txn = client_dgraph.txn()
    try:
        txn.mutate(set_obj={"uid": t_a, "para": [{"uid": cond_uid}]})
        txn.mutate(set_obj={"uid": t_b, "para": [{"uid": cond_uid}]})
        txn.commit()
        print(f"   🔸 Tratamientos ligados a '{cond_target}': t_a={t_a}, t_b={t_b}")
    finally:
        txn.discard()


    # --- ESCENARIO 1: SOBREDOSIS (Mismo med, diferentes doctores) ---
    # Paciente[0] recibe Paracetamol de Doctor[0] y Doctor[1]
    p_sobredosis = lista_pacientes[0]
    doc_A = lista_doctores[0]
    doc_B = lista_doctores[1]
    u_paracetamol = mapa_meds["Paracetamol"]

    # Tratamiento A (Doc A)
    t1 = dg_utils.crear_tratamiento(client_dgraph, "Dolor A", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t1, u_paracetamol)
    dg_utils.relacionar_paciente_tratamiento(client_dgraph, p_sobredosis["dgraph_uid"], t1)
    relacionar_doctor_tratamiento(client_dgraph, doc_A["dgraph_uid"], t1) # Helper local

    # Tratamiento B (Doc B) - ¡EL MISMO MEDICAMENTO!
    t2 = dg_utils.crear_tratamiento(client_dgraph, "Dolor B", "5 días")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t2, u_paracetamol)
    dg_utils.relacionar_paciente_tratamiento(client_dgraph, p_sobredosis["dgraph_uid"], t2)
    relacionar_doctor_tratamiento(client_dgraph, doc_B["dgraph_uid"], t2)

    print(f"   🔹 Escenario Sobredosis: {p_sobredosis['nombre']} recibe Paracetamol de {doc_A['nombre']} y {doc_B['nombre']}")


    # --- ESCENARIO 2: CONFLICTO (Toma A, receta B que interactúa) ---
    # Paciente[1] toma Losartán, se le agrega Ibuprofeno
    p_conflicto = lista_pacientes[1]

    # Ya toma Losartán
    t_base = dg_utils.crear_tratamiento(client_dgraph, "Control Presión", "Permanente")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_base, u_losartan)
    dg_utils.relacionar_paciente_tratamiento(client_dgraph, p_conflicto["dgraph_uid"], t_base)

    # Recibe Ibuprofeno (que choca con Losartán)
    t_nuevo = dg_utils.crear_tratamiento(client_dgraph, "Dolor Cabeza", "3 días")
    dg_utils.relacionar_tratamiento_medicamento(client_dgraph, t_nuevo, u_ibuprofeno)
    dg_utils.relacionar_paciente_tratamiento(client_dgraph, p_conflicto["dgraph_uid"], t_nuevo)

    print(f"   🔹 Escenario Conflicto: {p_conflicto['nombre']} toma Losartán y recibe Ibuprofeno")


    # --- ESCENARIO 3: CONTAGIO (Paciente Cero -> Doctor -> Otros Pacientes) ---
    # Doctor[2] atiende a Paciente[2] (con Gripe). Luego atiende a Paciente[3] y [4].
    doc_contagio = lista_doctores[2]
    p_cero = lista_pacientes[2]
    p_expuesto1 = lista_pacientes[3]
    p_expuesto2 = lista_pacientes[4]
    u_gripe = mapa_cond["Gripe"]

    # Paciente Cero tiene Gripe
    dg_utils.relacionar_paciente_condicion(client_dgraph, p_cero["dgraph_uid"], u_gripe)

    # El doctor trata esa gripe (Prescribe tratamiento PARA gripe)
    t_gripe = dg_utils.crear_tratamiento(client_dgraph, "Reposo", "7 días")
    # Relacionar correctamente doctor -> prescribe -> tratamiento
    relacionar_doctor_tratamiento(client_dgraph, doc_contagio["dgraph_uid"], t_gripe)
    # Relacionar tratamiento con condición (Faltaba helper, usamos 'para' directo si existe o genérico)
    # Asumimos que Tratamiento --para--> Condicion
    txn = client_dgraph.txn()
    txn.mutate(set_obj={"uid": t_gripe, "para": [{"uid": u_gripe}]})
    txn.commit()

    # Doctor atiende a los 3 (La relación 'atiende' la usamos para trazar contacto)
    dg_utils.relacionar_doctor_atiende(client_dgraph, doc_contagio["dgraph_uid"], p_cero["dgraph_uid"])
    dg_utils.relacionar_doctor_atiende(client_dgraph, doc_contagio["dgraph_uid"], p_expuesto1["dgraph_uid"])
    dg_utils.relacionar_doctor_atiende(client_dgraph, doc_contagio["dgraph_uid"], p_expuesto2["dgraph_uid"])

    print(f"   🔹 Escenario Contagio: {doc_contagio['nombre']} trató Gripe de {p_cero['nombre']} y atendió a otros 2 pacientes.")

    print("\n✨ ¡Población finalizada exitosamente!")

if __name__ == "__main__":
    poblar_todo()