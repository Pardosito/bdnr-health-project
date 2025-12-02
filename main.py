from connect import get_mongo, get_cassandra, get_dgraph

#servicios de mondongo
from Mongo.doctors_service import (
    registrar_doctor,
    buscar_doctor_por_id,
    buscar_doctor_por_nombre,
    buscar_por_especialidad
)

from Mongo.pacientes_service import (
    registrar_paciente,
    consultar_paciente,
)

from Mongo.expediente_service import (
    crear_expediente,
    obtener_expediente,
    consultar_historial,
    agregar_padecimiento
)

from Mongo.pipelines import (
    pipeline_buckets_edad,
    pipeline_diagnostico_stats
)

#servicios de cassandra
from Cassandra.cassandra import (
    registro_inicio_visita,
    registro_fin_visita,
    obtener_visitas_del_dia,
    registrar_signo_vital,
    registrar_receta_por_visita,
    consultar_recetas_por_doctor,
    obtener_diagnostico_tratamiento_paciente,
    verificar_disponibilidad_doctor
)

#dgraph servicios
from Dgraph.queries import (
    meds_recetados_juntos,
    sugerir_segunda_opinion,
    detectar_conflictos_tratamiento,
    pacientes_polifarmacia,
    analizar_propagacion_contagiosa,
    detectar_sobredosis,
    analizar_red_doctor,
    padecimientos_por_especialidad,

)




def main():

    print("Conectando a bases de datos...")
    mongo = get_mongo()
    cassandra = get_cassandra()
    dgraph = get_dgraph()

    print("\n=== Plataforma de Integración de Datos de Salud ===")

    while True:

        #mondongo
        print("\n--- MONDONGO ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por nombre")
        print("3. Buscar doctor por especialidad")
        print("4. Registrar nuevo paciente")
        print("5. Crear expediente para paciente")
        print("6. Consultar paciente por nombre")
        print("7. Filtrar pacientes")
        print("8. Mostrar info médica del paciente")
        print("9. Añadir padecimiento a paciente")
        print("10. Pipeline — edad promedio + frecuencia medicamentos")
        print("11. Pipeline — buckets de edad")

        #cassandra
        print("\n--- Cassandra ---")
        print("12. Registrar inicio/fin de visita médica")
        print("13. Consultar historial de visitas")
        print("14. Consultar visitas programadas por día")
        print("15. Registrar signo vital")
        print("16. Historial de signo vital")
        print("17. Guardar receta médica")
        print("18. Consultar recetas por rango")
        print("19. Historial de accesos")
        print("20. Diagnósticos emitidos por doctor en fecha")
        print("21. Diagnóstico + tratamiento por fecha")
        print("22. Disponibilidad del doctor")

        #dgraph
        print("\n--- Dgraph ---")
        print("23. Pacientes de un doctor que vio otro especialista")
        print("24. Medicamentos recetados juntos")
        print("25. Sugerir especialista para segunda opinión")
        print("26. Detectar conflictos de tratamiento")
        print("27. Analizar red de un doctor")
        print("28. Ruta de tratamiento de un paciente")
        print("29. Pacientes con muchos medicamentos")
        print("30. Posibles sobredosis")
        print("31. Referencias entre doctores")
        print("32. Frecuencia de tratamientos por especialidad")
        print("33. Padecimientos más comunes por especialidad")

        print("\n0. Salir\n")

        choice = int(input("Seleccione una opción: "))

        match choice:

            #mondongo
            case 1:
                print("\n--- Registrar nuevo doctor (MongoDB) ---")
                data = {
                    "nombre": input("Nombre: "),
                    "especialidad": input("Especialidad: "),
                    "subespecialidad": input("Subespecialidad: "),
                    "cedula": input("Cédula: "),
                    "telefono": input("Teléfono: "),
                    "correo": input("Correo: "),
                    "consultorio": input("Consultorio: ")
                }
                print("ID generado:", registrar_doctor(mongo, data))

            case 2:
                print("\n--- Buscar doctor por nombre (MongoDB — búsqueda parcial) ---")
                nombre = input("Nombre o ID del doctor: ")
                if mongo is None:
                    print("[ERROR] MongoDB no está conectado.")
                else:
                    print(buscar_doctor_por_nombre(mongo, nombre))

            case 3:
                esp = input("Especialidad: ")
                print("(MongoDB) Resultados de búsqueda por especialidad:")
                print(buscar_por_especialidad(mongo, esp))

            case 4:
                print("\n--- Registrar nuevo paciente (MongoDB) ---")
                data = {
                    "nombre": input("Nombre: "),
                    "fecha_nac": input("Fecha nacimiento (YYYY-MM-DD): "),
                    "sexo": input("Sexo: "),
                    "telefono": input("Teléfono: "),
                    "correo": input("Correo: "),
                    "cont_eme": input("Contacto emergencia: "),
                    "direccion": input("Dirección: "),
                    "seguro": input("Seguro: "),
                    "poliza": input("Póliza: ")
                }
                print("ID generado:", registrar_paciente(mongo, data))

            case 5:
                print("\n--- Crear expediente para paciente (MongoDB) ---")
                pid = input("ID del paciente: ")
                print(crear_expediente(pid))

            case 6:
                print("\n--- Consultar paciente y expediente (MongoDB) ---")
                nombre = input("Nombre o ID del paciente: ")
                print(consultar_paciente(mongo, nombre))

            case 7:
                print("\n--- Filtrar pacientes (MongoDB) ---")
                sexo = input("Sexo (ENTER para ignorar): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(consultar_paciente(mongo, filtros))

            case 8:
                print("\n--- Obtener expediente médico del paciente (MongoDB) ---")
                nombre = input("Nombre o ID: ")
                print(obtener_expediente(mongo, nombre))

            case 9:
                print("\n--- Añadir padecimiento al expediente (MongoDB) ---")
                pid = input("ID paciente: ")
                pade = input("Padecimiento: ")
                print(agregar_padecimiento(mongo, pid, pade))

            case 10:
                print("\n--- Pipeline: edad promedio + frecuencia medicamentos (MongoDB aggregation) ---")
                diag = input("Padecimiento: ")
                print(pipeline_diagnostico_stats(mongo, diag))

            case 11:
                print("\n--- Pipeline: buckets de edad por padecimiento (MongoDB aggregation) ---")
                diag = input("Padecimiento: ")
                print(pipeline_buckets_edad(mongo, diag))



            #cassandra
            case 12:
                print("\n--- Registrar inicio de visita (Cassandra: visitas_por_paciente) ---")
                paciente_nombre = input("Nombre del paciente: ")
                doctor_nombre = input("Nombre del doctor: ")
                registro_inicio_visita(paciente_nombre, doctor_nombre)

            case 13:
                print("\n--- Registrar fin de visita (Cassandra: actualizar timestamp_fin) ---")
                paciente_nombre = input("Nombre del paciente: ")
                registro_fin_visita(paciente_nombre)

            case 14:
                print("\n--- Obtener visitas programadas para un día (Cassandra: visitas_del_dia) ---")
                fecha = str(input("Ingresa la fecha: "))
                obtener_visitas_del_dia(fecha)

            case 15:
                print("\n--- Registrar signo vital (Cassandra: signos_vitales_por_visita) ---")
                paciente_nombre = input("Nombre del paciente: ")
                doctor_nombre = input("Nombre del doctor: ")
                tipo = input("Tipo de medición: ")
                valor = input("Valor: ")
                registrar_signo_vital(paciente_nombre, doctor_nombre, tipo, valor)

            case 16:
                print("\n--- Historial de signos vitales (Cassandra) — no implementado ---")
                print("Funcionalidad no disponible en el módulo de Cassandra actual.")

            case 17:
                print("\n--- Guardar receta médica (Cassandra: recetas_por_visita) ---")
                paciente_nombre = input("Nombre del paciente: ")
                doctor_nombre = input("Nombre del doctor: ")
                visita_id = input("Visita ID (opcional): ")
                receta = input("Texto de la receta: ")
                registrar_receta_por_visita(paciente_nombre, doctor_nombre, visita_id, receta)

            case 18:
                print("\n--- Consultar recetas por doctor ---")
                doctor_nombre = input("Nombre del doctor: ")
                consultar_recetas_por_doctor(doctor_nombre)

            case 19:
                print("\n--- Historial de accesos (Cassandra) — no implementado ---")
                print("Funcionalidad no disponible en el módulo de Cassandra actual.")

            case 20:
                print("\n--- Consultar diagnósticos por doctor en una fecha (Cassandra) ---")
                doctor_nombre = input("Nombre del doctor: ")
                paciente_nombre = input("Nombre del paciente (dejar vacío para todos): ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_diagnostico_tratamiento_paciente(doctor_nombre, paciente_nombre or None, fecha)

            case 21:
                print("\n--- Obtener diagnóstico y tratamiento por fecha (Cassandra) ---")
                doctor_nombre = input("Nombre del doctor: ")
                paciente_nombre = input("Nombre del paciente: ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                obtener_diagnostico_tratamiento_paciente(doctor_nombre, paciente_nombre, fecha)

            case 22:
                print("\n--- Consultar disponibilidad del doctor (Cassandra: visitas_del_dia) ---")
                doctor_nombre = input("Nombre del doctor: ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                verificar_disponibilidad_doctor(doctor_nombre, fecha)



            # #dgraph
            case 23:
                # Analizar propagación / pacientes en riesgo (sin parámetros)
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(analizar_propagacion_contagiosa(dgraph))

            case 24:
                cond = input("Condición médica: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(meds_recetados_juntos(dgraph, cond))

            case 25:
                pid = input("Paciente ID: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(sugerir_segunda_opinion(dgraph, pid))

            case 26:
                pid = input("Paciente ID: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(detectar_conflictos_tratamiento(dgraph, pid))

            case 27:
                did = input("Doctor ID: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(analizar_red_doctor(dgraph, did))

            case 28:
                pid = input("Paciente ID: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    # 'ruta_tratamiento_paciente' no está implementada en queries.py;
                    # mostramos los tratamientos/medicamentos actuales como aproximación
                    print("Funcionalidad 'ruta de tratamiento' no implementada; mostrando tratamientos actuales:")
                    print(detectar_conflictos_tratamiento(dgraph, pid))

            case 29:
                umbral = input("Umbral (número mínimo de tratamientos, ENTER=3): ")
                try:
                    umbral_val = int(umbral) if umbral else 3
                except ValueError:
                    umbral_val = 3
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(pacientes_polifarmacia(dgraph, umbral_val))

            case 30:
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(detectar_sobredosis(dgraph))

            case 31:
                did = input("Doctor ID: ")
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    # Usamos el análisis de red para mostrar referencias/colaboraciones
                    print(analizar_red_doctor(dgraph, did))

            case 32:
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    # 'frecuencia_tratamientos_por_especialidad' se cubre con padecimientos_por_especialidad
                    print(padecimientos_por_especialidad(dgraph))

            case 33:
                if dgraph is None:
                    print("[ERROR] Dgraph no está conectado.")
                else:
                    print(padecimientos_por_especialidad(dgraph))

            #salir
            case 0:
                break

            case _:
                print("Error, seleccione opción válida")
if __name__ == "__main__":
    main()
