from unittest.mock import MagicMock, patch
import pytest


def _make_client(uid_key="node"):
    client = MagicMock()
    txn = MagicMock()
    res = MagicMock()
    res.uids.get.return_value = "uid_abc"
    txn.mutate.return_value = res
    client.txn.return_value = txn
    return client, txn, res


class TestCrearDoctor:
    def test_returns_uid(self):
        client, txn, res = _make_client("doctor")
        res.uids.get.return_value = "doc_uid"
        from Dgraph.dgraph import crear_doctor
        result = crear_doctor(client, "Dr. Test", "mongo123", "Cardiología")
        assert result == "doc_uid"
        txn.commit.assert_called_once()
        txn.discard.assert_called_once()

    def test_returns_none_on_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_doctor
        result = crear_doctor(client, "Dr. Test", "mongo123", "Cardiología")
        assert result is None
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestCrearPaciente:
    def test_returns_uid(self):
        client, txn, res = _make_client("paciente")
        res.uids.get.return_value = "pac_uid"
        from Dgraph.dgraph import crear_paciente
        result = crear_paciente(client, "Juan", "mongo123", 35, "Calle 1")
        assert result == "pac_uid"

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_paciente
        result = crear_paciente(client, "Juan", "mongo123", 35, "Calle 1")
        assert result is None


class TestCrearCondicion:
    def test_returns_uid_contagious(self):
        client, txn, res = _make_client()
        res.uids.get.return_value = "cond_uid"
        from Dgraph.dgraph import crear_condicion
        result = crear_condicion(client, "Gripe", contagioso=True)
        assert result == "cond_uid"

    def test_returns_uid_non_contagious(self):
        client, txn, res = _make_client()
        res.uids.get.return_value = "cond_uid"
        from Dgraph.dgraph import crear_condicion
        result = crear_condicion(client, "Artritis")
        assert result == "cond_uid"

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_condicion
        result = crear_condicion(client, "Artritis")
        assert result is None


class TestCrearMedicamento:
    def test_returns_uid(self):
        client, txn, res = _make_client()
        res.uids.get.return_value = "med_uid"
        from Dgraph.dgraph import crear_medicamento
        result = crear_medicamento(client, "Paracetamol", "500mg")
        assert result == "med_uid"

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_medicamento
        result = crear_medicamento(client, "Paracetamol", "500mg")
        assert result is None


class TestCrearTratamiento:
    def test_returns_uid(self):
        client, txn, res = _make_client()
        res.uids.get.return_value = "trat_uid"
        from Dgraph.dgraph import crear_tratamiento
        result = crear_tratamiento(client, "Control presión", "30 días")
        assert result == "trat_uid"

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_tratamiento
        result = crear_tratamiento(client, "Control presión", "30 días")
        assert result is None


class TestCrearEspecialidad:
    def test_returns_uid(self):
        client, txn, res = _make_client()
        res.uids.get.return_value = "esp_uid"
        from Dgraph.dgraph import crear_especialidad
        result = crear_especialidad(client, "Cardiología")
        assert result == "esp_uid"

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_especialidad
        result = crear_especialidad(client, "Cardiología")
        assert result is None




class TestRelaciones:
    def test_relacionar_doctor_atiende(self, capsys):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import relacionar_doctor_atiende
        relacionar_doctor_atiende(client, "doc_uid", "pac_uid")
        txn.commit.assert_called_once()

    def test_relacionar_doctor_atiende_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import relacionar_doctor_atiende
        relacionar_doctor_atiende(client, "doc_uid", "pac_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_relacionar_paciente_condicion(self):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import relacionar_paciente_condicion
        relacionar_paciente_condicion(client, "pac_uid", "cond_uid")
        txn.commit.assert_called_once()

    def test_relacionar_paciente_condicion_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import relacionar_paciente_condicion
        relacionar_paciente_condicion(client, "pac_uid", "cond_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_relacionar_tratamiento_medicamento(self):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import relacionar_tratamiento_medicamento
        relacionar_tratamiento_medicamento(client, "trat_uid", "med_uid")
        txn.commit.assert_called_once()

    def test_relacionar_tratamiento_medicamento_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import relacionar_tratamiento_medicamento
        relacionar_tratamiento_medicamento(client, "trat_uid", "med_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_relacionar_paciente_tratamiento(self):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import relacionar_paciente_tratamiento
        relacionar_paciente_tratamiento(client, "pac_uid", "trat_uid")
        txn.commit.assert_called_once()

    def test_relacionar_paciente_tratamiento_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import relacionar_paciente_tratamiento
        relacionar_paciente_tratamiento(client, "pac_uid", "trat_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_relacionar_doctor_especialidad(self):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import relacionar_doctor_especialidad
        relacionar_doctor_especialidad(client, "doc_uid", "esp_uid")
        txn.commit.assert_called_once()

    def test_relacionar_doctor_especialidad_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import relacionar_doctor_especialidad
        relacionar_doctor_especialidad(client, "doc_uid", "esp_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out



class TestCrearInteraccion:
    def test_creates_bidirectional_interaction(self):
        client, txn, _ = _make_client()
        from Dgraph.dgraph import crear_interaccion
        crear_interaccion(client, "med1_uid", "med2_uid")
        assert txn.mutate.call_count == 2
        txn.commit.assert_called_once()

    def test_handles_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.mutate.side_effect = Exception("fail")
        from Dgraph.dgraph import crear_interaccion
        crear_interaccion(client, "med1_uid", "med2_uid")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestObtenerUidPorIdMongo:
    def test_returns_uid_when_found(self):
        import json
        client = MagicMock()
        txn = MagicMock()
        client.txn.return_value = txn
        txn.query.return_value.json = json.dumps({"nodo": [{"uid": "0x1"}]})
        from Dgraph.dgraph import obtener_uid_por_id_mongo
        result = obtener_uid_por_id_mongo(client, "mongo123")
        assert result == "0x1"

    def test_returns_none_when_not_found(self):
        import json
        client = MagicMock()
        txn = MagicMock()
        client.txn.return_value = txn
        txn.query.return_value.json = json.dumps({"nodo": []})
        from Dgraph.dgraph import obtener_uid_por_id_mongo
        result = obtener_uid_por_id_mongo(client, "mongo123")
        assert result is None

    def test_returns_none_on_exception(self, capsys):
        client = MagicMock()
        client.txn.return_value.query.side_effect = Exception("fail")
        from Dgraph.dgraph import obtener_uid_por_id_mongo
        result = obtener_uid_por_id_mongo(client, "mongo123")
        assert result is None


class TestSetSchema:
    def test_calls_alter(self, capsys):
        with patch("Dgraph.dgraph.get_dgraph") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            from Dgraph.dgraph import set_schema
            set_schema()
        mock_client.alter.assert_called_once()
        captured = capsys.readouterr()
        assert "SCHEMA" in captured.out


class TestCargarDatosEjemplo:
    def test_loads_example_data(self, capsys):
        import Dgraph.dgraph as dg
        mock_client = MagicMock()
        mock_txn = MagicMock()
        mock_res = MagicMock()
        mock_res.uids.get.return_value = "uid1"
        mock_txn.mutate.return_value = mock_res
        mock_client.txn.return_value = mock_txn

        with patch.object(dg, "get_dgraph", return_value=mock_client):
            dg.cargar_datos_ejemplo()
        captured = capsys.readouterr()
        assert "cargados" in captured.out
