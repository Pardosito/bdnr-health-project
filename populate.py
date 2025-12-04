import uuid
from datetime import date
import pydgraph

# Imports
from connect import get_mongo, get_cassandra, get_dgraph
from Mongo.services.doctors_service import registrar_doctor
from Mongo.services.pacientes_service import registrar_paciente
from Mongo.services.expediente_service import crear_expediente
from Mongo.services.expediente_service import agregar_alergia, agregar_padecimiento
from Cassandra import model
from Dgraph import dgraph as dg_utils
from Mongo.utils import get_doctor_by_id, get_paciente_by_id

# --- DATOS HARDCODEADOS PARA PRUEBAS DGRAPH ---

HARDCODED_DOCTORS = [
    {"nombre": "Dr. Ana Torres", "especialidad": "Cardiología", "id_code": "D001"},
    {"nombre": "Dr. Juan Pérez", "especialidad": "Medicina General", "id_code": "D002"},
    {"nombre": "Dr. Sofía Ruiz", "especialidad": "Neurología", "id_code": "D003"},
    {"nombre": "Dr. Carlos Lima", "especialidad": "Neurología", "id_code": "D004"},
]

HARDCODED_PACIENTES = [
    # Caso para Sugerencia de 2da Opinión, Red de Doctores, y Exposición a Contagio
    {"nombre": "Luis Gómez", "fecha_nac": "1998-05-15", "sexo": "M", "alergias": ["Ibuprofeno"], "diagnostico": "Migraña", "id_code": "P001"},
    # Caso para Sobredosis y Propagación Contagiosa (tiene Gripe)
    {"nombre": "María López", "fecha_nac": "1985-11-20", "sexo": "F", "alergias": [], "diagnostico": "Gripe", "id_code": "P002"},
    # Caso para Conflictos de Tratamiento (alergia + interacción) y Polifarmacia
    {"nombre": "Pedro Díaz", "fecha_nac": "1970-01-01", "sexo": "M", "alergias": ["Losartán"], "diagnostico": "Hipertensión", "id_code": "P003"},
]

HARDCODED_MEDICAMENTOS = [
    {"nombre": "Losartán", "dosis": "50mg", "interacciones": ["Ibuprofeno"]},
    {"nombre": "Ibuprofeno", "dosis": "400mg", "interacciones": ["Losartán"]},
    {"nombre": "Paracetamol", "dosis": "500mg", "interacciones": []},
    {"nombre": "Amoxicilina", "dosis": "500mg", "interacciones": []},
    {"nombre": "Vitaminas", "dosis": "1p/día", "interacciones": []},
]

# Helper para relacionar doctor-tratamiento en Dgraph (prescribe)
def relacionar_doctor_tratamiento(client, doctor_uid, tratamiento_uid):
    txn = client.txn()
    try:
        txn.mutate(set_obj={"uid": doctor_uid, "prescribe": [{"uid": tratamiento_uid}]})
        txn.commit()
    finally:
        txn.discard()

# Helper para relacionar tratamiento-condicion (para)
def relacionar_tratamiento_condicion(client, tratamiento_uid, condicion_uid):
    """Tratamiento -> para -> Condicion"""
    txn = client.txn()
    try:
        data = {"uid": tratamiento_uid, "para": [{"uid": condicion_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        return tratamiento_uid
    except Exception as e:
        print("Error tratamiento-condicion:", e)
    finally:
        txn.discard()

# Helper para relacionar paciente-alergia (es_alergico)
def relacionar_paciente_alergia(client, paciente_uid, medicamento_uid):
    """Paciente -> es_alergico -> Medicamento"""
    txn = client.txn()
    try:
        data = {"uid": paciente_uid, "es_alergico": [{"uid": medicamento_uid}]}
        txn.mutate(set_obj=data)
        txn.commit()
        return paciente_uid
    except Exception as e:
        print("Error paciente-alergia:", e)
    finally:
        txn.discard()


# Función principal modificada
def poblar_todo():
    print("🚀 Iniciando población HARDCODEADA (Mongo + Cassandra + Dgraph)...")

    # conexiones
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    if mongo is None:
        print("❌ Mongo no conectado")
        return

    # --- RESET DGRAPH ---
    if dgraph:
        print("\n🧨 Reseteando Dgraph y cargando esquema...")
        dgraph.alter(pydgraph.Operation(drop_all=True))
        dg_utils.set_schema()

    # ==========================================================
    # 1. MONDONGO
    # ==========================================================
    print("\n=== MONGO (Datos de prueba) ===")

    lista_doctores = []
    lista_pacientes = []

    # Doctores
    for doc_data in HARDCODED_DOCTORS:
        doc = {
            "nombre": doc_data["nombre"],
            "especialidad": doc_data["especialidad"],
            "subespecialidad": "N/A",
            "cedula": doc_data["id_code"],
            "telefono": "555-1234",
            "correo": f"{doc_data['id_code'].lower()}@test.com",
            "consultorio": doc_data["id_code"]
        }
        doc_id = registrar_doctor(doc)
        doc["_id"] = str(doc_id)

        # Crear en Dgraph
        if dgraph:
            uid = dg_utils.crear_doctor(dgraph, doc["nombre"], str(doc_id), doc["especialidad"])
            doc["dgraph_uid"] = uid

        lista_doctores.append(doc)
        print(f"🩺 Doctor creado: {doc['nombre']} (Mongo ID: {doc_id})")

    # Pacientes
    for pac_data in HARDCODED_PACIENTES:
        pac = {
            "nombre": pac_data["nombre"],
            "fecha_nac": pac_data["fecha_nac"],
            "sexo": pac_data["sexo"],
            "telefono": "555-4321",
            "correo": f"{pac_data['id_code'].lower()}@test.com",
            "cont_eme": "Familiar",
            "direccion": "Calle Falsa 123",
            "seguro": "AXA",
            "poliza": "POL-123"
        }

        pac_id = registrar_paciente(pac)
        pac["_id"] = str(pac_id)

        # Crear expediente y añadir datos iniciales en Mongo/Cassandra
        crear_expediente(pac_id)
        # Añadir alergias en Mongo
        for alergia in pac_data["alergias"]:
            agregar_alergia(pac_id, alergia)
        # Añadir padecimiento en Mongo/Cassandra (Dr. Ana Torres)
        doc_ana_nombre = lista_doctores[0]['nombre']
        agregar_padecimiento(pac_data["nombre"], pac_data["diagnostico"], doc_ana_nombre)

        # Crear en Dgraph
        if dgraph:
            # Edad fija para simplificar la prueba de Dgraph
            uid = dg_utils.crear_paciente(dgraph, pac["nombre"], str(pac_id), edad=50, direccion=pac["direccion"])
            pac["dgraph_uid"] = uid

        lista_pacientes.append(pac)
        print(f"🧍 Paciente creado: {pac['nombre']} (Mongo ID: {pac_id})")

    # ==========================================================
    # 2. CASSANDRA (Mínimo requerido)
    # ==========================================================
    if cassandra:
        print("\n=== CASSANDRA (Estructura lista, puedes añadir más datos aquí si lo necesitas) ===")

    # ==========================================================
    # 3. DGRAPH → CASOS DE PRUEBA ESPECÍFICOS
    # ==========================================================
    if dgraph:
        print("\n=== DGRAPH (Escenarios de prueba) ===")

        # UIDS de nodos ya creados (para simplificar)
        d_ana = lista_doctores[0]["dgraph_uid"]
        d_juan = lista_doctores[1]["dgraph_uid"]
        d_sofia = lista_doctores[2]["dgraph_uid"]
        d_carlos = lista_doctores[3]["dgraph_uid"]

        p_luis = lista_pacientes[0]["dgraph_uid"]
        p_maria = lista_pacientes[1]["dgraph_uid"]
        p_pedro = lista_pacientes[2]["dgraph_uid"]

        # --- Nodos de Condicion y Medicamento ---
        mapa_cond = {}
        for c in ["Migraña", "Gripe", "Hipertensión"]:
            mapa_cond[c] = dg_utils.crear_condicion(dgraph, c, c == "Gripe")

        mapa_med = {}
        for m_data in HARDCODED_MEDICAMENTOS:
            mapa_med[m_data["nombre"]] = dg_utils.crear_medicamento(
                dgraph,
                m_data["nombre"],
                m_data["dosis"]
            )

        # --- Alergias (Luis: Ibuprofeno, Pedro: Losartán) ---
        relacionar_paciente_alergia(dgraph, p_luis, mapa_med["Ibuprofeno"])
        relacionar_paciente_alergia(dgraph, p_pedro, mapa_med["Losartán"])


        # --- Interacciones (Losartán <-> Ibuprofeno) ---
        dg_utils.crear_interaccion(dgraph, mapa_med["Losartán"], mapa_med["Ibuprofeno"])
        print("💊 Interacción Losartán <-> Ibuprofeno creada.")


        # 1. Relaciones base de atención (Doctor atiende Paciente)
        dg_utils.relacionar_doctor_atiende(dgraph, d_ana, p_luis)
        dg_utils.relacionar_doctor_atiende(dgraph, d_ana, p_pedro)
        dg_utils.relacionar_doctor_atiende(dgraph, d_juan, p_maria)
        # Doctor Juan también atiende a Luis (Para prueba de Propagación Contagiosa y Red de Doctores)
        dg_utils.relacionar_doctor_atiende(dgraph, d_juan, p_luis)
        # Doctor Carlos atiende a Pedro (Para prueba de Red de Doctores)
        dg_utils.relacionar_doctor_atiende(dgraph, d_carlos, p_pedro)

        # 2. Relaciones Condición (Paciente diagnosticado_con Condición)
        dg_utils.relacionar_paciente_condicion(dgraph, p_luis, mapa_cond["Migraña"])
        dg_utils.relacionar_paciente_condicion(dgraph, p_maria, mapa_cond["Gripe"])
        dg_utils.relacionar_paciente_condicion(dgraph, p_pedro, mapa_cond["Hipertensión"])


        # --- ESCENARIOS DE PRUEBA ---

        # ESCENARIO 1: Conflicto de Tratamiento (Pedro Díaz - P003)
        # Recibe Tratamiento que incluye Losartán (alergia) y Ibuprofeno (interacción)
        t_conflicto = dg_utils.crear_tratamiento(dgraph, "HTA y Dolor", "Permanente")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, mapa_med["Losartán"])
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_conflicto, mapa_med["Ibuprofeno"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_pedro, t_conflicto)
        relacionar_doctor_tratamiento(dgraph, d_ana, t_conflicto)
        print("⚠ Escenario Conflicto (P003) creado.")

        # ESCENARIO 2: Sobredosis (María López - P002)
        # Recibe Paracetamol de D. Juan y Paracetamol de D. Ana
        t_sobre_a = dg_utils.crear_tratamiento(dgraph, "Dolor Gral A", "5 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_a, mapa_med["Paracetamol"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_maria, t_sobre_a)
        relacionar_doctor_tratamiento(dgraph, d_juan, t_sobre_a)

        t_sobre_b = dg_utils.crear_tratamiento(dgraph, "Dolor Gral B", "5 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_sobre_b, mapa_med["Paracetamol"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_maria, t_sobre_b)
        relacionar_doctor_tratamiento(dgraph, d_ana, t_sobre_b)
        print("⚠ Escenario Sobredosis (P002) creado.")

        # ESCENARIO 3: Sugerencia de Segunda Opinión (Luis Gómez - P001)
        # Luis tiene Migraña (D. Ana). D. Sofía (Neurología) debe ser sugerida.

        # Tratamiento de Ana (actual)
        t_mig_ana = dg_utils.crear_tratamiento(dgraph, "Trat. Migraña A", "30 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_mig_ana, mapa_med["Ibuprofeno"])
        relacionar_tratamiento_condicion(dgraph, t_mig_ana, mapa_cond["Migraña"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_luis, t_mig_ana)
        relacionar_doctor_tratamiento(dgraph, d_ana, t_mig_ana)

        # Tratamiento de Sofía (sugerencia)
        t_mig_sofia = dg_utils.crear_tratamiento(dgraph, "Trat. Migraña B", "30 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_mig_sofia, mapa_med["Paracetamol"])
        relacionar_tratamiento_condicion(dgraph, t_mig_sofia, mapa_cond["Migraña"])
        relacionar_doctor_tratamiento(dgraph, d_sofia, t_mig_sofia)
        print("💡 Escenario Segunda Opinión (P001) creado.")

        # ESCENARIO 4: Propagación Contagiosa (Gripe de María - P002)
        # Gripe (Contagious: True) -> T_GRIP_01 -> Dr. Juan Pérez.
        # Paciente expuesto: Luis Gómez (P001), porque Dr. Juan Pérez lo atiende.
        t_gripe = dg_utils.crear_tratamiento(dgraph, "Trat. Gripe", "7 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_gripe, mapa_med["Amoxicilina"])
        relacionar_tratamiento_condicion(dgraph, t_gripe, mapa_cond["Gripe"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_maria, t_gripe)
        relacionar_doctor_tratamiento(dgraph, d_juan, t_gripe)
        print("🦠 Escenario Propagación Contagiosa creado. (P001 expuesto)")

        # ESCENARIO 5: Polifarmacia (Pedro Díaz - P003)
        # Ya tiene T_Conflicto, necesita 2 más para cumplir umbral=3

        t_poli_a = dg_utils.crear_tratamiento(dgraph, "Vitaminas", "60 días")
        dg_utils.relacionar_tratamiento_medicamento(dgraph, t_poli_a, mapa_med["Vitaminas"])
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_pedro, t_poli_a)
        relacionar_doctor_tratamiento(dgraph, d_ana, t_poli_a)

        t_poli_b = dg_utils.crear_tratamiento(dgraph, "Ejercicio", "Indefinido")
        dg_utils.relacionar_paciente_tratamiento(dgraph, p_pedro, t_poli_b)
        relacionar_doctor_tratamiento(dgraph, d_ana, t_poli_b)

        print("📈 Escenario Polifarmacia (P003, 3 tratamientos) creado.")


    print("\n✨ POBLACIÓN COMPLETADA")


if __name__ == "__main__":
    poblar_todo()