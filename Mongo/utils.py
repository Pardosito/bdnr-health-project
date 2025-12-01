from mongo import pacientes, doctores

def get_paciente_id(nombre):
  try:
    paciente = pacientes.find_one({ "nombre": nombre})
    id = paciente["_id"]
    if id:
      return id
    else:
      return None

  except Exception as e:
    print("Errorsito: {e}")


def get_doctor_id(nombre):
    try:
      doctor = doctores.find_one({ "nombre": nombre})
      id = doctor["_id"]
      if id:
        return id
      else:
        return None

    except Exception as e:
      print("Errorsito: {e}")

def get_paciente_by_id(id):
  try:
    paciente = pacientes.find_one({ "_id": id })
    nombre = paciente["nombre"]
    if nombre:
      return nombre
    else:
      return None

  except Exception as e:
    print(f"Id no encontrado: {e}")

def get_doctor_by_id(id):
  try:
    doctor = doctores.find_one({ "_id": id })
    nombre = doctor["nombre"]
    if nombre:
      return nombre
    else:
      return None

  except Exception as e:
    print(f"Id no encontrado: {e}")