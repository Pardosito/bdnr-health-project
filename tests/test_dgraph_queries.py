import json
from unittest.mock import MagicMock, patch
import pytest


def _make_client(response_data: dict):
    client = MagicMock()
    txn = MagicMock()
    txn.query.return_value.json = json.dumps(response_data)
    client.txn.return_value = txn
    return client


class TestMedsRecetadosJuntos:
    def test_returns_empty_list_when_no_data(self):
        client = _make_client({"data": []})
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "Asma")
        assert result == []

    def test_returns_meds_by_name(self, capsys):
        data = {"data": [{"uid": "0x1", "nombre": "Asma", "~para": [
            {"uid": "0x2", "incluye": [{"nombre": "Paracetamol"}, {"nombre": "Ibuprofeno"}]}
        ]}]}
        client = _make_client(data)
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "Asma")
        assert result is not None
        captured = capsys.readouterr()
        assert "Paracetamol" in captured.out

    def test_returns_meds_by_uid(self, capsys):
        data = {"data": [{"uid": "0x1", "nombre": "Asma", "~para": [
            {"uid": "0x2", "incluye": [{"nombre": "Metformina"}]}
        ]}]}
        client = _make_client(data)
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "0x1a2b")

    def test_falls_back_to_regex_query(self, capsys):
        # First two queries return empty, third (regex) returns data
        client = MagicMock()
        txn = MagicMock()
        client.txn.return_value = txn
        empty = json.dumps({"data": []})
        regex_data = json.dumps({"data": [{"uid": "0x1", "~para": [
            {"uid": "0x2", "incluye": [{"nombre": "Losartán"}]}
        ]}]})
        txn.query.side_effect = [
            MagicMock(json=empty),
            MagicMock(json=regex_data),
        ]
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "Hipertensión")

    def test_handles_query_exception(self):
        client = MagicMock()
        client.txn.return_value.query.side_effect = Exception("fail")
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "Asma")
        assert result is None

    def test_handles_uid_query_exception_falls_back(self):
        client = MagicMock()
        txn = MagicMock()
        client.txn.return_value = txn
        import json as _json
        txn.query.side_effect = [
            Exception("uid query fail"),
            MagicMock(json=_json.dumps({"data": []})),
        ]
        from Dgraph.queries import meds_recetados_juntos
        result = meds_recetados_juntos(client, "0x1a2b")


class TestSugerirSegundaOpinion:
    def test_prints_candidatos(self, capsys):
        data = {"sugerencias": [
            {"nombre": "Dr. López", "especialidad": "Cardiología", "prescribe": [{"uid": "0x1"}]},
            {"nombre": "Dr. Ruiz", "especialidad": "Cardiología", "prescribe": []},
        ]}
        client = _make_client(data)
        from Dgraph.queries import sugerir_segunda_opinion
        sugerir_segunda_opinion(client, "pac123")
        captured = capsys.readouterr()
        assert "Dr. López" in captured.out

    def test_prints_nothing_when_no_candidates(self, capsys):
        client = _make_client({"sugerencias": []})
        from Dgraph.queries import sugerir_segunda_opinion
        sugerir_segunda_opinion(client, "pac123")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestDetectarConflictosTratamiento:
    def test_returns_not_found_when_no_patient(self):
        client = _make_client({"paciente": []})
        from Dgraph.queries import detectar_conflictos_tratamiento
        result = detectar_conflictos_tratamiento(client, "pac123")
        assert result == "Paciente no encontrado"

    def test_returns_no_conflicts(self):
        data = {"paciente": [{"nombre": "Juan", "recibe": [], "es_alergico": []}]}
        client = _make_client(data)
        from Dgraph.queries import detectar_conflictos_tratamiento
        result = detectar_conflictos_tratamiento(client, "pac123")
        assert result == "No se detectaron conflictos."

    def test_detects_interaction(self, capsys):
        data = {"paciente": [{"nombre": "Juan", "recibe": [
            {"incluye": [
                {"uid": "0x1", "nombre": "Paracetamol", "interactua_con": [{"uid": "0x2", "nombre": "Ibuprofeno"}]},
                {"uid": "0x2", "nombre": "Ibuprofeno", "interactua_con": []},
            ]}
        ], "es_alergico": []}]}
        client = _make_client(data)
        from Dgraph.queries import detectar_conflictos_tratamiento
        detectar_conflictos_tratamiento(client, "pac123")
        captured = capsys.readouterr()
        assert "INTERACCIÓN" in captured.out

    def test_detects_allergy(self, capsys):
        data = {"paciente": [{"nombre": "Juan", "recibe": [
            {"incluye": [{"uid": "0x1", "nombre": "Penicilina", "interactua_con": []}]}
        ], "es_alergico": [{"uid": "0x1", "nombre": "Penicilina"}]}]}
        client = _make_client(data)
        from Dgraph.queries import detectar_conflictos_tratamiento
        detectar_conflictos_tratamiento(client, "pac123")
        captured = capsys.readouterr()
        assert "ALERGIA" in captured.out


class TestPacientesPolifarmacia:
    def test_prints_patients_above_threshold(self, capsys):
        data = {"pacientes": [
            {"nombre": "Juan", "id": "p1", "count(recibe)": 5},
            {"nombre": "Ana", "id": "p2", "count(recibe)": 1},
        ]}
        client = _make_client(data)
        from Dgraph.queries import pacientes_polifarmacia
        pacientes_polifarmacia(client, umbral=3)
        captured = capsys.readouterr()
        assert "Juan" in captured.out
        assert "Ana" not in captured.out

    def test_uses_default_umbral(self, capsys):
        data = {"pacientes": [{"nombre": "Pedro", "id": "p3", "count(recibe)": 3}]}
        client = _make_client(data)
        from Dgraph.queries import pacientes_polifarmacia
        pacientes_polifarmacia(client)
        captured = capsys.readouterr()
        assert "Pedro" in captured.out


class TestAnalizarPropagacionContagiosa:
    def test_prints_propagation(self, capsys):
        data = {"pacientes_riesgo": [
            {"nombre_doctor": "Dr. Vega", "id": "d1", "pacientes_expuestos": [
                {"nombre": "Luis", "id": "p1"},
            ]}
        ]}
        client = _make_client(data)
        from Dgraph.queries import analizar_propagacion_contagiosa
        analizar_propagacion_contagiosa(client)
        captured = capsys.readouterr()
        assert "Dr. Vega" in captured.out
        assert "Luis" in captured.out

    def test_prints_nothing_when_no_risk(self, capsys):
        client = _make_client({"pacientes_riesgo": []})
        from Dgraph.queries import analizar_propagacion_contagiosa
        analizar_propagacion_contagiosa(client)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestDetectarSobredosis:
    def test_prints_overdose_alert(self, capsys):
        data = {"pacientes": [
            {"nombre": "Mario", "recibe": [
                {"~prescribe": [{"nombre": "Dr. A"}], "incluye": [{"nombre": "Paracetamol"}]},
                {"~prescribe": [{"nombre": "Dr. B"}], "incluye": [{"nombre": "Paracetamol"}]},
            ]}
        ]}
        client = _make_client(data)
        from Dgraph.queries import detectar_sobredosis
        detectar_sobredosis(client)
        captured = capsys.readouterr()
        assert "Mario" in captured.out
        assert "Paracetamol" in captured.out

    def test_no_alert_when_same_doctor(self, capsys):
        data = {"pacientes": [
            {"nombre": "Mario", "recibe": [
                {"~prescribe": [{"nombre": "Dr. A"}], "incluye": [{"nombre": "Paracetamol"}]},
                {"~prescribe": [{"nombre": "Dr. A"}], "incluye": [{"nombre": "Paracetamol"}]},
            ]}
        ]}
        client = _make_client(data)
        from Dgraph.queries import detectar_sobredosis
        detectar_sobredosis(client)
        captured = capsys.readouterr()
        assert "Mario" not in captured.out


class TestAnalizarRedDoctor:
    def test_prints_colleagues(self, capsys):
        data = {"doctor": [{"nombre": "Dr. Central", "atiende": [
            {"nombre": "Paciente1", "~atiende": [
                {"nombre": "Dr. Colega1", "id": "d2", "especialidad": "Cardiología"}
            ]}
        ]}]}
        client = _make_client(data)
        from Dgraph.queries import analizar_red_doctor
        analizar_red_doctor(client, "doc123")
        captured = capsys.readouterr()
        assert "Dr. Colega1" in captured.out

    def test_handles_empty_result(self, capsys):
        client = _make_client({"doctor": []})
        from Dgraph.queries import analizar_red_doctor
        analizar_red_doctor(client, "doc123")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestPadecimientosPorEspecialidad:
    def test_prints_report(self, capsys):
        data = {"especialidades": [
            {"nombre": "Cardiología", "~tiene_especialidad": [
                {"prescribe": [{"para": [{"nombre": "Hipertensión"}]}]}
            ]}
        ]}
        client = _make_client(data)
        from Dgraph.queries import padecimientos_por_especialidad
        padecimientos_por_especialidad(client)
        captured = capsys.readouterr()
        assert "Cardiología" in captured.out

    def test_handles_empty_specialties(self, capsys):
        client = _make_client({"especialidades": []})
        from Dgraph.queries import padecimientos_por_especialidad
        padecimientos_por_especialidad(client)


class TestRelacionarDoctorTratamientoQuery:
    def test_calls_commit(self):
        client = MagicMock()
        txn = MagicMock()
        client.txn.return_value = txn
        from Dgraph.queries import relacionar_doctor_tratamiento
        relacionar_doctor_tratamiento(client, "doc_uid", "trat_uid")
        txn.commit.assert_called_once()

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.queries import relacionar_doctor_tratamiento
        relacionar_doctor_tratamiento(client, "doc_uid", "trat_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out
