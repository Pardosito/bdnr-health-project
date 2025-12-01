from connect import get_mongo, get_cassandra, get_dgraph

#servicios de mondongo
from Mongo.doctor_service import (
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
from Cassandra.visitas_service import (
    registrar_visita,
    historial_visitas,
    visitas_por_dia,
    registrar_signos_vitales,
    historial_signos,
    guardar_receta,
    recetas_por_rango,
    historial_accesos,
    diagnosticos_doctor_dia,
    diagnostico_y_tratamiento_por_fecha,
    disponibilidad_doctor
)

#dgraph servicios
from dgraph_queries import (
    pacientes_vistos_por_otro_especialista,
    meds_recetados_juntos,
    sugerir_segunda_opinion,
    detectar_conflictos_tratamiento,
    analizar_red_doctor,
    ruta_tratamiento_paciente,
    pacientes_polifarmacia,
    detectar_sobredosis,
    referencias_doctores,
    frecuencia_tratamientos_por_especialidad,
    padecimientos_por_especialidad
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
                print("\n--- Registrar nuevo doctor ---")
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
                nombre = input("Nombre del doctor: ")
                print(buscar_doctor_por_nombre(mongo, nombre))

            case 3:
                esp = input("Especialidad: ")
                print(buscar_por_especialidad(mongo, esp))

            case 4:
                print("\n--- Registrar nuevo paciente ---")
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
                pid = input("ID del paciente: ")
                print(crear_expediente(pid))

            case 6:
                nombre = input("Nombre o ID del paciente: ")
                print(consultar_paciente(mongo, nombre))

            case 7:
                sexo = input("Sexo (ENTER para ignorar): ")
                filtros = {}
                if sexo:
                    filtros["sexo"] = sexo
                print(consultar_paciente(mongo, filtros))

            case 8:
                nombre = input("Nombre o ID: ")
                print(obtener_expediente(mongo, nombre))

            case 9:
                pid = input("ID paciente: ")
                pade = input("Padecimiento: ")
                print(agregar_padecimiento(mongo, pid, pade))

            case 10:
                diag = input("Padecimiento: ")
                print(pipeline_diagnostico_stats(mongo, diag))

            case 11:
                diag = input("Padecimiento: ")
                print(pipeline_buckets_edad(mongo, diag))



            #cassandra
            case 12:
                print("\n--- Registrar visita médica ---")
                pid = input("Paciente ID: ")
                did = input("Doctor ID: ")
                motivo = input("Motivo: ")
                print(registrar_visita(cassandra, pid, did, motivo))

            case 13:
                pid = input("Paciente ID: ")
                print(historial_visitas(cassandra, pid))

            case 14:
                fecha = input("Fecha (YYYY-MM-DD): ")
                print(visitas_por_dia(cassandra, fecha))

            case 15:
                pid = input("Paciente ID: ")
                tipo = input("Tipo signo: ")
                valor = input("Valor: ")
                print(registrar_signos_vitales(cassandra, pid, tipo, valor))

            case 16:
                pid = input("Paciente ID: ")
                signo = input("Tipo signo vital: ")
                print(historial_signos(cassandra, pid, signo))

            case 17:
                pid = input("Paciente ID: ")
                receta = input("Receta: ")
                print(guardar_receta(cassandra, pid, receta))

            case 18:
                did = input("Doctor ID: ")
                f1 = input("Inicio: ")
                f2 = input("Fin: ")
                print(recetas_por_rango(cassandra, did, f1, f2))

            case 19:
                print(historial_accesos(cassandra))

            case 20:
                did = input("Doctor ID: ")
                fecha = input("Fecha: ")
                print(diagnosticos_doctor_dia(cassandra, did, fecha))

            case 21:
                pid = input("Paciente ID: ")
                fecha = input("Fecha: ")
                print(diagnostico_y_tratamiento_por_fecha(cassandra, pid, fecha))

            case 22:
                did = input("Doctor ID: ")
                fecha = input("Fecha: ")
                print(disponibilidad_doctor(cassandra, did, fecha))



            #dgraph
            case 23:
                did = input("Doctor ID: ")
                print(pacientes_vistos_por_otro_especialista(dgraph, did))

            case 24:
                cond = input("Condición médica: ")
                print(meds_recetados_juntos(dgraph, cond))

            case 25:
                diag = input("Diagnóstico: ")
                print(sugerir_segunda_opinion(dgraph, diag))

            case 26:
                pid = input("Paciente ID: ")
                print(detectar_conflictos_tratamiento(dgraph, pid))

            case 27:
                did = input("Doctor ID: ")
                print(analizar_red_doctor(dgraph, did))

            case 28:
                pid = input("Paciente ID: ")
                print(ruta_tratamiento_paciente(dgraph, pid))

            case 29:
                print(pacientes_polifarmacia(dgraph))

            case 30:
                print(detectar_sobredosis(dgraph))

            case 31:
                print(referencias_doctores(dgraph))

            case 32:
                print(frecuencia_tratamientos_por_especialidad(dgraph))

            case 33:
                print(padecimientos_por_especialidad(dgraph))

            #salir
            case 0:
                break

            case _:
                print("Error, seleccione opción válida")
if __name__ == "__main__":
    main()
