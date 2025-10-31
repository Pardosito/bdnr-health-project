def main():
    while True:
        print("\n=== Plataforma de Integración de Datos de Salud ===")
        print("\n--- MongoDB ---")
        print("1. Registrar nuevo doctor")
        print("2. Buscar doctor por especialidad")
        print("3. Registrar nuevo paciente")
        print("4. Consultar perfil de paciente")
        print("5. Crear expediente de paciente")
        print("6. Buscar alergias/padecimientos de un paciente")

        print("\n--- Cassandra ---")
        print("7. Registrar inicio/fin de visita médica")
        print("8. Consultar historial de visitas de un paciente")
        print("9. Consultar visitas programadas para un día")
        print("10. Registrar receta médica para una visita")
        print("11. Registrar signos vitales para una visita")
        print("12. Registrar acceso de auditoría a expediente")

        print("\n--- Dgraph ---")
        print("13. Encontrar pacientes de un doctor tratados por otro especialista")
        print("14. Identificar medicamentos recetados juntos para una condición")
        print("15. Sugerir doctor para segunda opinión")
        print("16. Analizar red de un doctor")

        print("\n")
        print("0. Salir")

        choice = input("Seleccione opción: ")

        if choice == "1":
            print("Registrando nuevo doctor\n")
            pass
        elif choice == "2":
            print("Buscando doctores por especialidad\n")
            pass
        elif choice == "3":
            print("Registrando nuevo paciente\n")
            pass
        elif choice == "4":
            print("Consultando paciente y expediente\n")
            pass
        elif choice == "5":
            print("Añadiendo diagnóstico a expendiente\n")
            pass
        elif choice == "6":
            print("Consultando padecimientos\n")
            pass
        elif choice == "7":
            print("Registrando visita médica\n")
            pass
        elif choice == "8":
            print("Consultando historial de visitas\n")
            pass
        elif choice == "9":
            print("Consultando visitas del día\n")
            pass
        elif choice == "10":
            print("Registrando visita médica\n")
            pass
        elif choice == "11":
            print("Registrando signos vitales\n")
            pass
        elif choice == "12":
            print("Registrando acceso para auditorías\n")
            pass
        elif choice == "13":
            print("Analizando pacientes comúnes entre doctores\n")
            pass
        elif choice == "14":
            print("Buscando múltiples preescripciones de medicamentos\n")
            pass
        elif choice == "15":
            print("Buscando segunda opinión\n")
            pass
        elif choice == "16":
            print("Analizando red de doctor\n")
            pass
        elif choice == '0':
            print("Saliendo del sistema.")
            break
        else:
            print("Opción inválida. Intente de nuevo.")


if __name__ == "__main__":
    main()
