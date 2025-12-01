"""
For MongoDB, we plan to use a JSON file to populate our database since we believe it makes the most sense for this particular case.
Using mongoimport we can make a small script or function that will help us populate the database in case it is still empty.

For Cassandra, we plan to use a csv file to populate the database. We will have a small script or function that will run a for loop
reading and inserting all information.

For Dgraph, we also plan to use a JSON file since we also believe it makes the most sense to use that format. We will load it using
a small script or function using pydgraph to make sure everything is handled properly.

We are still debating whether to use an AI like ChatGPT or Gemini to generate the bulk data, which would allow us to have some control
over the generated data, or using a library like Faker to generate such bulk data.
"""

import random
import uuid
from datetime import datetime, timedelta, date
from faker import Faker
from bson import ObjectId
import pydgraph

# Importamos tus conexiones y servicios
# Asegúrate de que los imports coincidan con tu estructura de carpetas
from connect import get_mongo, get_cassandra, get_dgraph
from Mongo.doctor_service import registrar_doctor
from Mongo.pacientes_service import registrar_paciente
from Mongo.expediente_service import crear_expediente, agregar_padecimiento
from Cassandra import model
from Dgraph import dgraph as dg_utils # Asumiendo que las funciones de creación están aquí

fake = Faker('es_MX')

# --- CONFIGURACIÓN DE DATOS MAESTROS (Para consistencia) ---
ESPECIALIDADES = ["Cardiología", "Pediatría", "Medicina General", "Neurología", "Dermatología"]
PADECIMIENTOS = ["Diabetes Tipo 2", "Hipertensión", "Asma", "Migraña Crónica", "Artritis"]
MEDICAMENTOS = [
    {"nombre": "Paracetamol", "dosis": "500mg"},
    {"nombre": "Ibuprofeno", "dosis": "400mg"},
    {"nombre": "Metformina", "dosis": "850mg"},  # Para Diabetes
    {"nombre": "Losartán", "dosis": "50mg"},     # Para Hipertensión
    {"nombre": "Salbutamol", "dosis": "100mcg"}  # Para Asma
]

def poblar_todo():
    print("🚀 Iniciando población de datos...")

    # 1. Conexiones
    db_mongo = get_mongo()
    session_cass = get_cassandra()
    client_dgraph = get_dgraph()

    if db_mongo == None and session_cass == None and client_dgraph == None:
        print("❌ Error: No se pudo conectar a todas las bases de datos.")
        return

    # Limpiar Dgraph (Opcional, para no duplicar en pruebas)
    op = pydgraph.Operation(drop_all=True)
    client_dgraph.alter(op)
    dg_utils.set_schema() # Recargar schema después de borrar

    # ==========================================
    # FASE 1: MONDONGO (Doctores y Pacientes)
    # ==========================================
    print("\n--- Fase 1: MongoDB (Usuarios Base) ---")

    lista_doctores = []
    lista_pacientes = []

    # 1.1 Crear Doctores
    for esp in ESPECIALIDADES:
        # Creamos 2 doctores por especialidad
        for _ in range(2):
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
            lista_doctores.append({**doc_data, "_id": str(doc_id)})

            # Sincronizar con Dgraph inmediatamente
            dg_doc_uid = dg_utils.crear_doctor(client_dgraph, doc_data["nombre"], str(doc_id), esp)
            lista_doctores[-1]["dgraph_uid"] = dg_doc_uid

    # 1.2 Crear Pacientes y Expedientes
    # Generamos 20 pacientes con edades variadas para probar los buckets
    for i in range(20):
        fecha_nac = fake.date_of_birth(minimum_age=5, maximum_age=80)
        pac_data = {
            "nombre": fake.first_name() + " " + fake.last_name(),
            "fecha_nac": fecha_nac.isoformat(), # String YYYY-MM-DD
            "sexo": random.choice(["M", "F"]),
            "telefono": fake.phone_number(),
            "correo": fake.email(),
            "cont_eme": fake.name(),
            "direccion": fake.address(),
            "seguro": "GNP" if random.random() > 0.5 else "AXA",
            "poliza": str(fake.random_number(digits=10))
        }
        pac_id = registrar_paciente(db_mongo, pac_data)
        str_pac_id = str(pac_id)

        # Calcular edad para Dgraph
        edad = (date.today() - fecha_nac).days // 365

        # Sincronizar con Dgraph
        dg_pac_uid = dg_utils.crear_paciente(client_dgraph, pac_data["nombre"], str_pac_id, edad, pac_data["direccion"])

        lista_pacientes.append({**pac_data, "_id": str_pac_id, "dgraph_uid": dg_pac_uid})

        # 1.3 Crear Expediente en Mongo
        # Asignar padecimientos específicos para probar aggregations
        padecimientos_paciente = []
        if i < 5: padecimientos_paciente.append("Diabetes Tipo 2") # 5 diabéticos
        if 5 <= i < 12: padecimientos_paciente.append("Hipertensión") # 7 hipertensos (varias edades)

        tratamientos_paciente = []
        if "Diabetes Tipo 2" in padecimientos_paciente:
            tratamientos_paciente.append("Metformina")

        exp_data = {
            "paciente_id": pac_id, # ObjectId
            "alergias": [fake.word() for _ in range(random.randint(0, 2))],
            "padecimientos": padecimientos_paciente,
            "tratamientos": tratamientos_paciente
        }
        crear_expediente(db_mongo, exp_data)

    print(f"✅ Generados {len(lista_doctores)} doctores y {len(lista_pacientes)} pacientes.")


# ==========================================
    # FASE 2: CASSANDRA (Historial Médico)
    # ==========================================
    print("\n--- Fase 2: Cassandra (Visitas y Recetas) ---")

    # 1. PREPARAR STATEMENTS (Una sola vez antes del loop)
    # Usamos las variables de texto que definimos en model.py
    try:
        stmt_historia = session_cass.prepare(model.inicio_visita_stmt)
        stmt_agenda   = session_cass.prepare(model.INSERT_VISITA_DEL_DIA)
        stmt_receta   = session_cass.prepare(model.recete_medica_registro_stmt)
        stmt_diag     = session_cass.prepare(model.INSERT_DIAGNOSTICO)
    except Exception as e:
        print(f"❌ Error preparando queries de Cassandra: {e}")
        return # Salir si falla esto, para no llenar de errores la consola

    # 2. GENERAR DATOS
    for paciente in lista_pacientes:
        # Generar entre 1 y 3 visitas pasadas por paciente
        num_visitas = random.randint(1, 3)

        # Elegimos un doctor random de la lista que generamos en Fase 1
        doctor_asignado = random.choice(lista_doctores)

        for _ in range(num_visitas):
            fecha_visita = fake.date_between(start_date='-1y', end_date='today')
            hora_inicio_uuid = uuid.uuid1() # TimeUUID para Cassandra
            hora_fin_uuid = uuid.uuid1()    # Simulamos que ya terminó

            # A) Insertar en Historial (visitas_por_paciente)
            # Schema: paciente_id, doctor_id, timestamp_inicio, timestamp_fin
            session_cass.execute(stmt_historia, [
                paciente["_id"],
                doctor_asignado["_id"],
                hora_inicio_uuid,
                hora_fin_uuid
            ])

            # B) Insertar en Agenda (visitas_del_dia)
            # Schema: fecha, tipo_visita, paciente_id, doctor_id, hora_inicio, hora_fin
            tipo = random.choice(["Consulta General", "Urgencia", "Seguimiento"])
            session_cass.execute(stmt_agenda, [
                fecha_visita,
                tipo,
                paciente["_id"],
                doctor_asignado["_id"],
                hora_inicio_uuid,
                hora_fin_uuid
            ])

            # C) Generar Receta (50% probabilidad)
            if random.random() > 0.5:
                receta_texto = f"{random.choice(MEDICAMENTOS)['nombre']} cada 8 horas."

                # Schema: paciente_id, doctor_id, visita_id, receta
                # OJO: visita_id es TEXT en esta tabla, así que usamos str(hora_inicio_uuid)
                session_cass.execute(stmt_receta, [
                    paciente["_id"],
                    doctor_asignado["_id"],
                    str(hora_inicio_uuid),
                    receta_texto
                ])

                # D) Generar Diagnóstico asociado
                diag_texto = random.choice(PADECIMIENTOS)

                # Schema: paciente_id, doctor_id, visita_id, diagnostico, fecha
                session_cass.execute(stmt_diag, [
                    paciente["_id"],
                    doctor_asignado["_id"],
                    str(hora_inicio_uuid),
                    diag_texto,
                    fecha_visita
                ])

    print("✅ Historial de visitas generado en Cassandra.")


    # ==========================================
    # FASE 3: DGRAPH (Conocimiento y Relaciones)
    # ==========================================
    print("\n--- Fase 3: Dgraph (Grafo de Conocimiento) ---")

    # 3.1 Crear Nodos Base (Medicamentos y Condiciones)
    mapa_condiciones = {} # nombre -> uid
    for cond_nombre in PADECIMIENTOS:
        es_contagioso = True if cond_nombre == "Gripe" else False # Ejemplo simple
        uid = dg_utils.crear_condicion(client_dgraph, cond_nombre, es_contagioso)
        mapa_condiciones[cond_nombre] = uid

    mapa_medicamentos = {}
    for med in MEDICAMENTOS:
        uid = dg_utils.crear_medicamento(client_dgraph, med["nombre"], med["dosis"])
        mapa_medicamentos[med["nombre"]] = uid

    # 3.2 Crear Relación de Interacción (Para probar query de conflictos)
    # Losartán interactúa con Ibuprofeno (ejemplo ficticio para prueba)
    uid_losartan = mapa_medicamentos.get("Losartán")
    uid_ibu = mapa_medicamentos.get("Ibuprofeno")

    if uid_losartan and uid_ibu:
        txn = client_dgraph.txn()
        try:
            # Crear relación bidireccional interactua_con
            data = {"uid": uid_losartan, "interactua_con": [{"uid": uid_ibu}]}
            txn.mutate(set_obj=data)
            txn.commit()
            print("   🔗 Interacción creada: Losartán <-> Ibuprofeno")
        finally:
            txn.discard()

    # 3.3 Relacionar Pacientes con Condiciones y Doctores
    # Usamos los UIDs que guardamos en la fase 1
    for paciente in lista_pacientes:
        # Recuperar datos de mongo para saber qué padecimientos tenía
        # (En un script real, leerías de mongo, aquí usamos la lógica de creación)
        # Asignamos aleatoriamente relaciones para el grafo

        # Paciente -> Diagnosticado con -> Condicion
        cond_random = random.choice(list(mapa_condiciones.keys()))
        uid_cond = mapa_condiciones[cond_random]
        dg_utils.relacionar_paciente_condicion(client_dgraph, paciente["dgraph_uid"], uid_cond)

        # Doctor -> Atiende -> Paciente
        doc_random = random.choice(lista_doctores)
        dg_utils.relacionar_doctor_atiende(client_dgraph, doc_random["dgraph_uid"], paciente["dgraph_uid"])

        # Doctor -> Tiene Especialidad (Crear nodo especialidad si no existe)
        # (Esto requeriría una función helper extra, la simulamos)

        # CASO DE PRUEBA: PACIENTE CON RIESGO
        # Si el paciente tiene Hipertensión (Losartán) y le recetamos Ibuprofeno -> Conflicto
        if cond_random == "Hipertensión":
            # Asignar tratamiento Losartán
            pass # Lógica de crear nodo tratamiento y ligarlo

    print("✅ Grafo poblado con relaciones complejas.")
    print("\n✨ ¡Población finalizada! Base de datos lista para pruebas.")

if __name__ == "__main__":
    poblar_todo()