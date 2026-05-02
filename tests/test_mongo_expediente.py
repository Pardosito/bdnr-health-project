from unittest.mock import MagicMock, patch
from bson import ObjectId
import pytest
import Mongo.services.expediente_service as svc

_VALID_ID = str(ObjectId())


class TestCrearExpediente:
    def test_returns_error_when_patient_not_found(self):
        with patch.object(svc, "get_paciente_id", return_value=None):
            result = svc.crear_expediente("Nonexistent")
        assert "error" in result

    def test_returns_ya_tiene_expediente(self):
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = {"existing": True}
            result = svc.crear_expediente(_VALID_ID)
        assert result["mensaje"] == "El paciente ya tiene expediente."

    def test_creates_expediente_successfully(self):
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = None
            result = svc.crear_expediente(_VALID_ID)
        assert result["mensaje"] == "Expediente creado correctamente."
        mock_exps.insert_one.assert_called_once()

    def test_creates_from_name_lookup(self):
        oid = ObjectId()
        with patch.object(svc, "get_paciente_id", return_value=oid):
            with patch.object(svc, "expedientes") as mock_exps:
                mock_exps.find_one.return_value = None
                result = svc.crear_expediente("Juan")
        assert result["mensaje"] == "Expediente creado correctamente."

    def test_creates_when_get_paciente_returns_dict(self):
        oid = ObjectId()
        with patch.object(svc, "get_paciente_id", return_value={"_id": oid}):
            with patch.object(svc, "expedientes") as mock_exps:
                mock_exps.find_one.return_value = None
                result = svc.crear_expediente("Juan")
        assert result["mensaje"] == "Expediente creado correctamente."


class TestObtenerExpediente:
    def test_returns_error_for_invalid_id(self):
        result = svc.obtener_expediente("not-an-id")
        assert "error" in result

    def test_returns_no_expediente_message(self):
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = None
            result = svc.obtener_expediente(_VALID_ID)
        assert result["mensaje"] == svc._NO_EXPEDIENTE

    def test_returns_expediente_data_as_strings(self):
        mock_exp = {
            "_id": ObjectId(),
            "paciente_id": ObjectId(),
            "alergias": [],
            "padecimientos": [],
            "tratamientos": []
        }
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = mock_exp
            result = svc.obtener_expediente(_VALID_ID)
        assert isinstance(result["_id"], str)
        assert isinstance(result["paciente_id"], str)


class TestAgregarAlergia:
    def test_returns_error_for_invalid_id(self):
        result = svc.agregar_alergia("not-an-id", "Polen")
        assert "error" in result

    def test_returns_error_when_no_expediente(self):
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = None
            result = svc.agregar_alergia(_VALID_ID, "Polen")
        assert "error" in result

    def test_adds_alergia_successfully(self):
        with patch.object(svc, "expedientes") as mock_exps:
            mock_exps.find_one.return_value = {"alergias": []}
            result = svc.agregar_alergia(_VALID_ID, "Polen")
        assert result["mensaje"] == "Alergia agregada."
        mock_exps.update_one.assert_called_once()


class TestAgregarPadecimiento:
    def test_returns_error_when_patient_not_found(self):
        with patch.object(svc, "get_paciente_id", return_value=None):
            result = svc.agregar_padecimiento("Nonexistent", "Asma")
        assert "Error" in result

    def test_returns_error_when_no_expediente(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "expedientes") as mock_exps:
                mock_exps.find_one.return_value = None
                result = svc.agregar_padecimiento("Juan", "Asma")
        assert "no tiene expediente" in result

    def test_adds_padecimiento_without_doctor(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "expedientes") as mock_exps:
                with patch.object(svc, "get_dgraph", return_value=None):
                    mock_exps.find_one.return_value = {"padecimientos": []}
                    result = svc.agregar_padecimiento("Juan", "Asma")
        assert "Juan" in result
        mock_exps.update_one.assert_called_once()

    def test_adds_padecimiento_with_cassandra(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session") as mock_sess:
                        with patch.object(svc, "get_dgraph", return_value=None):
                            mock_exps.find_one.return_value = {"padecimientos": []}
                            mock_sess.prepare.return_value = MagicMock()
                            result = svc.agregar_padecimiento("Juan", "Asma", "Dr. García")
        assert "Juan" in result

    def test_adds_padecimiento_with_dgraph_sync(self):
        mock_client = MagicMock()
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session"):
                        with patch.object(svc, "get_dgraph", return_value=mock_client):
                            with patch.object(svc, "dg_utils") as mock_dg:
                                mock_exps.find_one.return_value = {"padecimientos": []}
                                mock_dg.obtener_uid_por_id_mongo.return_value = "uid1"
                                mock_dg.crear_condicion.return_value = "cond_uid"
                                result = svc.agregar_padecimiento("Juan", "Asma", "Dr. García")
        assert "Dgraph" in result

    def test_handles_dgraph_error(self):
        mock_client = MagicMock()
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session"):
                        with patch.object(svc, "get_dgraph", return_value=mock_client):
                            with patch.object(svc, "dg_utils") as mock_dg:
                                mock_exps.find_one.return_value = {"padecimientos": []}
                                mock_dg.obtener_uid_por_id_mongo.side_effect = Exception("dgraph down")
                                result = svc.agregar_padecimiento("Juan", "Asma", "Dr. García")
        assert "Dgraph Error" in result

    def test_handles_cassandra_error(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session") as mock_sess:
                        with patch.object(svc, "get_dgraph", return_value=None):
                            mock_exps.find_one.return_value = {"padecimientos": []}
                            mock_sess.prepare.side_effect = Exception("cass error")
                            result = svc.agregar_padecimiento("Juan", "Asma", "Dr. García")
        assert "Error Cassandra" in result


class TestAgregarTratamiento:
    def test_returns_error_when_no_tratamiento(self):
        result = svc.agregar_tratamiento("Juan", "Dr. García", "")
        assert "tratamiento" in result

    def test_returns_error_when_patient_not_found(self):
        with patch.object(svc, "get_paciente_id", return_value=None):
            result = svc.agregar_tratamiento("Nonexistent", "Dr. García", "Paracetamol")
        assert "Paciente no encontrado" in result

    def test_returns_error_when_no_expediente(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "expedientes") as mock_exps:
                mock_exps.find_one.return_value = None
                result = svc.agregar_tratamiento("Juan", "Dr. García", "Paracetamol")
        assert "no tiene expediente" in result

    def test_adds_tratamiento_without_doctor(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "expedientes") as mock_exps:
                with patch.object(svc, "get_doctor_id", return_value=None):
                    with patch.object(svc, "get_dgraph", return_value=None):
                        mock_exps.find_one.return_value = {"tratamientos": []}
                        result = svc.agregar_tratamiento("Juan", "Dr. García", "Paracetamol")
        assert "Paracetamol" in result

    def test_adds_tratamiento_with_dgraph(self):
        mock_client = MagicMock()
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session"):
                        with patch.object(svc, "get_dgraph", return_value=mock_client):
                            with patch.object(svc, "dg_utils") as mock_dg:
                                mock_exps.find_one.return_value = {"tratamientos": []}
                                mock_dg.obtener_uid_por_id_mongo.return_value = "uid1"
                                mock_dg.crear_tratamiento.return_value = "trat_uid"
                                mock_dg.crear_medicamento.return_value = "med_uid"
                                result = svc.agregar_tratamiento("Juan", "Dr. García", "Paracetamol")
        assert "Dgraph" in result

    def test_handles_dgraph_error(self):
        mock_client = MagicMock()
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session"):
                        with patch.object(svc, "get_dgraph", return_value=mock_client):
                            with patch.object(svc, "dg_utils") as mock_dg:
                                mock_exps.find_one.return_value = {"tratamientos": []}
                                mock_dg.obtener_uid_por_id_mongo.side_effect = Exception("dgraph down")
                                result = svc.agregar_tratamiento("Juan", "Dr. García", "Paracetamol")
        assert "Dgraph Error" in result

    def test_handles_cassandra_error(self):
        with patch.object(svc, "get_paciente_id", return_value=ObjectId()):
            with patch.object(svc, "get_doctor_id", return_value=ObjectId()):
                with patch.object(svc, "expedientes") as mock_exps:
                    with patch.object(svc, "session") as mock_sess:
                        with patch.object(svc, "get_dgraph", return_value=None):
                            mock_exps.find_one.return_value = {"tratamientos": []}
                            mock_sess.prepare.side_effect = Exception("cass error")
                            result = svc.agregar_tratamiento("Juan", "Dr. García", "Paracetamol")
        assert "Error Cassandra" in result
