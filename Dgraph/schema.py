schema = """

#types

type Doctor {
    nombre
    id
    especialidad
    atiende
    prescribe
    tiene_especialidad
}

type Paciente {
    nombre
    id
    edad
    direccion
    diagnosticado_con
    recibe
    es_alergico
}

type Tratamiento {
    duracion
    tipo
    incluye
    para
    recetado_por
}

type Medicamento {
    nombre
    dosis
    interactua_con
}

type Condicion {
    nombre
    contagioso
}

type Especialidad {
    nombre
}

#indexes

nombre: string @index(exact, term) .
id: string @index(exact) .
especialidad: string @index(term) .
edad: int .
direccion: string .
dosis: string .
contagioso: bool @index(bool) .


#relaciones con @reverse

atiende: [uid] @reverse .
tiene_especialidad: [uid] @reverse .
prescribe: [uid] @reverse .

recetado_por: [uid] @reverse .
diagnosticado_con: [uid] @reverse .
recibe: [uid] @reverse .
es_alergico: [uid] @reverse .

incluye: [uid] @reverse .
para: [uid] @reverse .

interactua_con: [uid] @reverse .
"""
