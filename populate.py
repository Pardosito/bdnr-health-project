import random
import uuid
from datetime import datetime, timedelta, date
from faker import Faker
import pydgraph
from cassandra.util import uuid_from_time

from connect import get_mongo, get_cassandra, get_dgraph
from Mongo.services.doctors_service import registrar_doctor
from Mongo.services.pacientes_service import registrar_paciente
from Mongo.services.expediente_service import crear_expediente
from Mongo.services.expediente_service import agregar_padecimiento, agregar_alergia, obtener_expediente
from Dgraph import dgraph as dg_utils
from Mongo.utils import get_doctor_by_id, get_paciente_by_id

from Cassandra import model
from Cassandra.utils import medicionesEnum
from Cassandra.cassandra import (
    registro_inicio_visita,
    registro_fin_visita,
    registrar_signo_vital,
    registrar_receta_por_visita,
    registrar_diagnostico_por_visita
)

fake = Faker('es_MX')

# Opciones para poblar aleatoriamente
ESPECIALIDADES = ["Cardiología", "Pediatría", "Medicina General", "Neurología", "Dermatología", "Urgencias"]
PADECIMIENTOS = ["Diabetes Tipo 2", "Hipertensión", "Asma", "Migraña", "Artritis", "Gripe", "Infección Estomacal"]
CONTAGIOSOS = ["Gripe", "Infección Estomacal"]

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

# Creaciones de relaciones (traficando rimas)

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


# Escenarios dgraph

def poblar_dgraph_escenarios(dgraph, lista_doctores, lista_pacientes, mapa_med, mapa_cond):
    print("\n=== DGRAPH - Creando Escenarios de Prueba ===")

    # Escenario 0: meds recetados juntos
    for i in range(1, 5):
        nombre_cond = random.choice(list(mapa_cond.keys()))
        cond_uid = mapa_cond[nombre_cond]["dgraph_uid"]

        t_combo = dg_utils.crear_tratamiento(dgraph, f"Combo para {nombre_cond}", f"{random.randint(1,15)} días")

        med_info = random.choice(MEDICAMENTOS)
        med_nombre = med_info["nombre"]
        med_uid = mapa_med[med_nombre]["dgraph_uid"]

        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_combo, med_uid)

        med_extra = random.choice(MEDICAMENTOS)
        med_extra_uid = mapa_med[med_extra["nombre"]]["dgraph_uid"]
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_combo, med_extra_uid)

        relacionar_tratamiento_condicion(dgraph, t_combo, cond_uid)
        print(f"Combinación creada para Query 'Meds recetados juntos' ({nombre_cond})")

    # Escenario 1: Conflictos
    for i in range(1,5):
        med_A_info = random.choice(MEDICAMENTOS)
        med_B_info = random.choice(MEDICAMENTOS)

        while med_B_info == med_A_info:
             med_B_info = random.choice(MEDICAMENTOS)

        med_A_nombre = med_A_info["nombre"]
        med_B_nombre = med_B_info["nombre"]

        med_A_uid = mapa_med[med_A_nombre]["dgraph_uid"]
        med_B_uid = mapa_med[med_B_nombre]["dgraph_uid"]

        dg_utils.crear_interaccion(dgraph, med_A_uid, med_B_uid)

        paciente_conflicto = random.choice(lista_pacientes)
        doc_conflicto = random.choice(lista_doctores)

        relacionar_paciente_alergia(dgraph, paciente_conflicto["dgraph_uid"], med_A_uid)

        agregar_alergia(paciente_conflicto["_id"], med_A_nombre)

        t_conflicto = dg_utils.crear_tratamiento(dgraph, "Trat. Conflicto Aleatorio", f"{random.randint(1,15)} días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_A_uid)
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, med_B_uid)

        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_conflicto["dgraph_uid"], t_conflicto)
        relacionar_doctor_tratamiento(dgraph, doc_conflicto["dgraph_uid"], t_conflicto)
        print(f"Conflicto para: {paciente_conflicto['nombre']}")

    # Escenario 2: Sobredosis
    for i in range(1,3):
        paciente_sobredosis = random.choice(lista_pacientes)

        doc_sobredosis_A = lista_doctores[0]
        doc_sobredosis_B = lista_doctores[1]

        med_info = random.choice(MEDICAMENTOS)
        med_uid = mapa_med[med_info["nombre"]]["dgraph_uid"]

        t_sobre_a = dg_utils.crear_tratamiento(dgraph, "Sobredosis A", f"{random.randint(1,15)} días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_a, med_uid)
        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_a)
        relacionar_doctor_tratamiento(dgraph, doc_sobredosis_A["dgraph_uid"], t_sobre_a)

        t_sobre_b = dg_utils.crear_tratamiento(dgraph, "Sobredosis B", f"{random.randint(1,15)} días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_b, med_uid)
        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_sobredosis["dgraph_uid"], t_sobre_b)
        relacionar_doctor_tratamiento(dgraph, doc_sobredosis_B["dgraph_uid"], t_sobre_b)

        print(f"Caso Sobredosis para: {paciente_sobredosis['nombre']}")

    # Escenario 3: Sugerenica
    casos_generados = 0
    for p in lista_pacientes:
        cond_nombre = None
        try:
            exp = obtener_expediente(p["_id"])
            if exp and "padecimientos" in exp and len(exp["padecimientos"]) > 0:
                cond_nombre = random.choice(exp["padecimientos"])
        except Exception:
            pass

        if not cond_nombre:
            cond_nombre = random.choice(list(mapa_cond.keys()))

        cond_uid = mapa_cond[cond_nombre]["dgraph_uid"]

        doc_actual = random.choice(lista_doctores)
        especialidad_actual = doc_actual["especialidad"]

        dg_utils.relacionar_paciente_condicion(dgraph, p["dgraph_uid"], cond_uid)
        dg_utils.relacionar_doctor_atiende(dgraph, doc_actual["dgraph_uid"], p["dgraph_uid"])

        colegas = [d for d in lista_doctores
                   if d["especialidad"] == especialidad_actual
                   and d["_id"] != doc_actual["_id"]]

        if colegas:
            doc_sugerido = random.choice(colegas)
            t_sugerencia = dg_utils.crear_tratamiento(dgraph, f"Segunda Opinión: {cond_nombre}", "Revisión")
            relacionar_tratamiento_condicion(dgraph, t_sugerencia, cond_uid)
            relacionar_doctor_tratamiento(dgraph, doc_sugerido["dgraph_uid"], t_sugerencia)

            print(f"Sugerencia: {p['nombre']} (Cond: {cond_nombre}) atendido por {doc_actual['nombre']} ({especialidad_actual}) -> Sugerencia posible: {doc_sugerido['nombre']}")

            casos_generados += 1
        if casos_generados >= 5:
            break

    # Escenario 4: Propagación
    for i in range(1,3):
        nombre_cond = random.choice(list(mapa_cond.keys()))
        cond_contagiosa_uid = mapa_cond[nombre_cond]["dgraph_uid"]

        doc_contagioso = random.choice(lista_doctores)
        t_contagioso = dg_utils.crear_tratamiento(dgraph, f"Tratamiento para contagio", f"{random.randint(1,7)} días")
        relacionar_tratamiento_condicion(dgraph, t_contagioso, cond_contagiosa_uid)
        relacionar_doctor_tratamiento(dgraph, doc_contagioso["dgraph_uid"], t_contagioso)

        paciente_contagiado = random.choice(lista_pacientes)
        dg_utils.relacionar_paciente_condicion(dgraph, paciente_contagiado["dgraph_uid"], cond_contagiosa_uid)
        dg_utils.relacionar_doctor_atiende(dgraph, doc_contagioso["dgraph_uid"], paciente_contagiado["dgraph_uid"])

        paciente_riesgo = random.choice([p for p in lista_pacientes if p != paciente_contagiado])
        dg_utils.relacionar_doctor_atiende(dgraph, doc_contagioso["dgraph_uid"], paciente_riesgo["dgraph_uid"])
        print(f"Propagación: {doc_contagioso['nombre']} atiende a {paciente_contagiado['nombre']} y {paciente_riesgo['nombre']}")

    # Escenario 5: Polimeds
    paciente_poli = random.choice(lista_pacientes)
    for i in range(4):
        med_nombre = random.choice(MEDICAMENTOS)["nombre"]
        t_poli = dg_utils.crear_tratamiento(dgraph, med_nombre, f"{random.randint(1,7)} días")
        dg_utils.relacionar_paciente_tratamiento(dgraph, paciente_poli["dgraph_uid"], t_poli)
    print(f"Polimeds para: {paciente_poli['nombre']}")

    # Escenario 6: Red doctorin rin rin
    if len(lista_doctores) >= 3 and len(lista_pacientes) >= 2:
        doc_central = lista_doctores[0]
        doc_colega1 = lista_doctores[1]
        doc_colega2 = lista_doctores[2]
        p_shared_1 = lista_pacientes[0]
        p_shared_2 = lista_pacientes[1]

        dg_utils.relacionar_doctor_atiende(dgraph, doc_central["dgraph_uid"], p_shared_1["dgraph_uid"])
        dg_utils.relacionar_doctor_atiende(dgraph, doc_colega1["dgraph_uid"], p_shared_1["dgraph_uid"])

        dg_utils.relacionar_doctor_atiende(dgraph, doc_central["dgraph_uid"], p_shared_2["dgraph_uid"])
        dg_utils.relacionar_doctor_atiende(dgraph, doc_colega2["dgraph_uid"], p_shared_2["dgraph_uid"])
        print(f"Red Doctor: {doc_central['nombre']} comparte pacientes con {doc_colega1['nombre']} y {doc_colega2['nombre']}.")


def poblar_todo():
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    if mongo is None:
        print("Mongo no conectado")
        return

    # --- RESET DGRAPH ---
    if dgraph:
        print("\neseteando Dgraph...")
        dgraph.alter(pydgraph.Operation(drop_all=True))
        dg_utils.set_schema()

    print("\n=== MONGO & DGRAPH BASE ===")

    lista_doctores = []
    lista_pacientes = []
    mapa_especialidades_uid = {}
    mapa_cond = {}
    mapa_med = {}

    if dgraph:
        for esp_nombre in ESPECIALIDADES:
            uid = dg_utils.crear_especialidad(dgraph, esp_nombre)
            mapa_especialidades_uid[esp_nombre] = uid

    # DOCTORES
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
            print(doc_data)
            doc_id = registrar_doctor(doc_data)
            uid = None
            if dgraph:
                uid = dg_utils.crear_doctor(dgraph, doc_data["nombre"], str(doc_id), esp)
                if esp in mapa_especialidades_uid:
                    dg_utils.relacionar_doctor_especialidad(dgraph, uid, mapa_especialidades_uid[esp])
            lista_doctores.append({**doc_data, "_id": str(doc_id), "dgraph_uid": uid})

    # PACIENTES
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
        print(pac)
        pac_id = registrar_paciente(pac)
        crear_expediente(pac_id)
        uid = None
        if dgraph:
            edad = random.randint(5,90)
            uid = dg_utils.crear_paciente(dgraph, pac["nombre"], str(pac_id), edad, pac["direccion"])
        lista_pacientes.append({**pac, "_id": str(pac_id), "dgraph_uid": uid})

    print(f"{len(lista_doctores)} Doctores y {len(lista_pacientes)} Pacientes creados.")

    # CASSANDRA
    if cassandra:
        print("\n=== CASSANDRA - Datos Clínicos y Citas ===")

        for p in lista_pacientes:
            try:
                doctor = random.choice(lista_doctores)
                nombre_doc = doctor["nombre"]

                registro_inicio_visita(p["nombre"], nombre_doc)

                sistolica = random.randint(110, 140)
                diastolica = random.randint(70, 90)
                registrar_signo_vital(p["nombre"], nombre_doc, "PRESION", f"{sistolica}/{diastolica}")
                peso = random.randint(50, 100)
                registrar_signo_vital(p["nombre"], nombre_doc, "PESO", f"{peso} kg")

                diag = random.choice(PADECIMIENTOS)
                registrar_diagnostico_por_visita(nombre_doc, p["nombre"], diag)

                med_info = random.choice(MEDICAMENTOS)
                receta_txt = f"{med_info['nombre']} - {med_info['dosis']}"
                registrar_receta_por_visita(p["nombre"], nombre_doc, receta_txt)

                registro_fin_visita(p["nombre"])
            except Exception as e:
                print(f"Error generando visita simulada: {e}")

        print("\n=== CASSANDRA - Generando Citas Agendadas (Disponibilidad) ===")

        today = date.today()
        dias_futuros = random.sample(range(1, 12), 5)
        fechas_agenda = [today + timedelta(days=d) for d in dias_futuros]
        print(f"Se agendarán citas para los días: {fechas_agenda}")
        try:
            stmt_agenda = cassandra.prepare(model.INSERT_VISITA_DEL_DIA)

            for _ in range(20):
                fecha_cita = random.choice(fechas_agenda)
                print(fecha_cita)
                doc_agenda = random.choice(lista_doctores)
                pac_agenda = random.choice(lista_pacientes)

                hora = random.randint(9, 16)
                minuto = random.choice([0, 30])

                dt_inicio = datetime.combine(fecha_cita, datetime.min.time()).replace(hour=hora, minute=minuto)
                dt_fin = dt_inicio + timedelta(minutes=30)

                uuid_inicio = uuid_from_time(dt_inicio)
                uuid_fin = uuid_from_time(dt_fin)

                cassandra.execute(stmt_agenda, [
                    fecha_cita,
                    "CITA_GENERAL",
                    str(pac_agenda['_id']),
                    str(doc_agenda['_id']),
                    uuid_inicio,
                    uuid_fin
                ])
                print(f"Agendada: {fecha_cita} {hora}:{minuto:02d} - {doc_agenda['nombre']} - {pac_agenda['nombre']}")

        except Exception as e:
            print(f"Error insertando citas: {e}")


    # DGRAPH ESCENARIOS
    if dgraph:
        for c in PADECIMIENTOS:
            uid = dg_utils.crear_condicion(dgraph, c, c == "Gripe")
            mapa_cond[c] = {"nombre": c, "dgraph_uid": uid}
        for m in MEDICAMENTOS:
            uid = dg_utils.crear_medicamento(dgraph, m["nombre"], m["dosis"])
            mapa_med[m["nombre"]] = {"nombre": m["nombre"], "dgraph_uid": uid}

        poblar_dgraph_escenarios(dgraph, lista_doctores, lista_pacientes, mapa_med, mapa_cond)

    print("\nPOBLACIÓN COMPLETADA - LISTO PARA PROBAR TODOS LOS QUERIES")


if __name__ == "__main__":
    poblar_todo()