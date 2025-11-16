from connect import get_mongo, get_cassandra, get_dgraph
# from db_tests import (
#     mongo_registrar_doctor,
#     mongo_buscar_por_especialidad,
#     mongo_registrar_paciente,
#     mongo_consultar_paciente,

#     cassandra_registrar_visita,
#     cassandra_historial_visitas,
#     cassandra_visitas_del_dia
# )


def main():

    print("Conectando a bases de datos...")
    get_mongo()
    get_cassandra()
    get_dgraph()

    print("\n=== Plataforma de Integración de Datos de Salud ===")

    while True:
        print("SE ELIMINARÁN LAS DIVISIONES DE LAS DB, DE MOMENTO ESTÁN PARA FACILITAR LA CODIFICACÍON DEL PROYECTO")
        print("\n--- mondongo de be AKA MongoDB ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por nombre")
        print("3. Buscar doctor por especialidad")
        print("4. Registrar nuevo paciente")
        print("5. Crear expediente para paciente")
        print("6. Buscar paciente por nombre")
        print("7. Buscar pacientes por sexo, rango de edad, medicamentos")
        print("8. Mostrar padecimientos, alergias y tratamientos de un paciente")
        print("9. Añadir padecimiento a expediente de un paciente")
        print("10. Mostrar ocurrencias y tratamientos de padecimientos")
        print("11. Calcular grupos de edades de pacientes que padecen cierto padecimiento")


        print("\n--- trashy de be AKA Cassandra ---")
        print("12. Registrar inicio/fin de visita médica")
        print("13. Consultar historial de visitas de un paciente")
        print("14. Consultar visitas programadas para un día")
        print("15. Registrar medición de signos vitales")
        print("16. Mostrar historial de signo vital particular para un paciente")
        print("17. Guardar receta médica de una visita")
        print("18. Consultar todas las recetas de un doctor en rango de fecha")
        print("19. Observar historial de accesos y registros a expedientes")
        print("20. Consultar todos los diágnosticos de un doctor en rango de fecha")
        print("21. Obtener diágnostico y tratamiento de paciente en fecha específica")
        print("22. Consultar disponibilidad de doctor en fecha")


        print("\n--- Dgraph ---")
        print("23. Mostrar pacientes de un doctor que han sido vistos por otro especialista")
        print("24. Identificar medicamentos recetados en conjunto para tratar padecimientos")
        print("25. Sugerir especialista para una segunda opinión")
        print("26. Detectar posibles conflictos en tratamiento de paciente")
        print("27. Analizar red de un doctor")
        print("28. Consultar historial de tratamiento de un paciente")
        print("29. Identificar pacientes que reciben alta cantidad de medicamentos")
        print("30. Identificar posibles sobredosis")
        print("31. Mostrar referencias entre doctores según pacientes en común")
        print("32. Mostrar frecuencias de tratamientos de ciertos padecimientos por ciertas especialidades")
        print("33. Generar reporte de padecimientos más comúnes por especialidad")


        print("\n0. Salir\n")

        choice = int(input("Seleccione una opción: "))

        match choice:
            case 1:
                print("1. Registrar nuevo doctor")
            case 2:
                print("2. Buscar doctor por nombre")
            case 3:
                print("3. Buscar doctor por especialidad")
            case 4:
                print("4. Registrar nuevo paciente")
            case 5:
                print("5. Crear expediente para paciente")
            case 6:
                print("6. Buscar paciente por nombre")
            case 7:
                print("7. Buscar pacientes por sexo, rango de edad, medicamentos")
            case 8:
                print("8. Mostrar padecimientos, alergias y tratamientos de un paciente")
            case 9:
                print("9. Añadir padecimiento a expediente de un paciente")
            case 10:
                print("10. Mostrar ocurrencias y tratamientos de padecimientos")
            case 11:
                print("11. Calcular grupos de edades de pacientes que padecen cierto padecimiento")
            case 12:
                print("12. Registrar inicio/fin de visita médica")
            case 13:
                print("13. Consultar historial de visitas de un paciente")
            case 14:
                print("14. Consultar visitas programadas para un día")
            case 15:
                print("15. Registrar medición de signos vitales")
            case 16:
                print("16. Mostrar historial de signo vital particular para un paciente")
            case 17:
                print("17. Guardar receta médica de una visita")
            case 18:
                print("18. Consultar todas las recetas de un doctor en rango de fecha")
            case 19:
                print("19. Observar historial de accesos y registros a expedientes")
            case 20:
                print("20. Consultar todos los diágnosticos de un doctor en rango de fecha")
            case 21:
                print("21. Obtener diágnostico y tratamiento de paciente en fecha específica")
            case 22:
                print("22. Consultar disponibilidad de doctor en fecha")
            case 23:
                print("23. Mostrar pacientes de un doctor que han sido vistos por otro especialista")
            case 24:
                print("24. Identificar medicamentos recetados en conjunto para tratar padecimientos")
            case 25:
                print("25. Sugerir especialista para una segunda opinión")
            case 26:
                print("26. Detectar posibles conflictos en tratamiento de paciente")
            case 27:
                print("27. Analizar red de un doctor")
            case 28:
                print("28. Consultar historial de tratamiento de un paciente")
            case 29:
                print("29. Identificar pacientes que reciben alta cantidad de medicamentos")
            case 30:
                print("30. Identificar posibles sobredosis")
            case 31:
                print("31. Mostrar referencias entre doctores según pacientes en común")
            case 32:
                print("32. Mostrar frecuencias de tratamientos de ciertos padecimientos por ciertas especialidades")
            case 33:
                print("33. Generar reporte de padecimientos más comúnes por especialidad")
            case 0:
                break
            case _:
                print("Error, escoga opción válida")

if __name__ == "__main__":
    main()

