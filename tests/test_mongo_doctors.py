from unittest.mock import MagicMock, patch
import pytest
import Mongo.services.doctors_service as svc


def _make_doc():
    return {
        "nombre": "Dr. García",
        "especialidad": "Cardiología",
        "subespecialidad": "Arritmias",
        "cedula": "12345678",
        "telefono": "555-0001",
        "correo": "garcia@test.com",
        "consultorio": "101"
    }


class TestRegistrarDoctor:
    def test_returns_mongo_id_no_dgraph(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "abc123"
        with patch.object(svc, "doctores") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=None):
                mock_coll.insert_one.return_value = mock_result
                result = svc.registrar_doctor(_make_doc())
        assert result == "abc123"

    def test_syncs_to_dgraph_when_available(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "abc123"
        mock_client = MagicMock()
        with patch.object(svc, "doctores") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=mock_client):
                with patch.object(svc, "dg_utils") as mock_dg:
                    mock_dg.crear_doctor.return_value = "uid1"
                    mock_dg.crear_especialidad.return_value = "esp_uid"
                    mock_coll.insert_one.return_value = mock_result
                    result = svc.registrar_doctor(_make_doc())
        assert result == "abc123"
        mock_dg.crear_doctor.assert_called_once()

    def test_handles_dgraph_exception(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "abc123"
        with patch.object(svc, "doctores") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=MagicMock()):
                with patch.object(svc, "dg_utils") as mock_dg:
                    mock_dg.crear_doctor.side_effect = Exception("dgraph down")
                    mock_coll.insert_one.return_value = mock_result
                    result = svc.registrar_doctor(_make_doc())
        assert result == "abc123"


class TestBuscarDoctorPorNombre:
    def test_returns_error_when_not_found(self):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find_one.return_value = None
            result = svc.buscar_doctor_por_nombre("Nonexistent")
        assert result == {"error": "Doctor no encontrado."}

    def test_prints_doctor_when_found(self, capsys):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find_one.return_value = _make_doc()
            svc.buscar_doctor_por_nombre("García")
        captured = capsys.readouterr()
        assert "García" in captured.out


class TestBuscarDoctorPorId:
    def test_returns_error_for_invalid_id(self):
        result = svc.buscar_doctor_por_id("not-an-id")
        assert "error" in result

    def test_returns_error_when_not_found(self):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find_one.return_value = None
            result = svc.buscar_doctor_por_id("507f1f77bcf86cd799439011")
        assert "error" in result

    def test_prints_doctor_when_found(self, capsys):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find_one.return_value = _make_doc()
            svc.buscar_doctor_por_id("507f1f77bcf86cd799439011")
        captured = capsys.readouterr()
        assert "García" in captured.out


class TestBuscarPorEspecialidad:
    def test_prints_message_when_none_found(self, capsys):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find.return_value = []
            svc.buscar_por_especialidad("Radiología")
        captured = capsys.readouterr()
        assert "No hay doctores" in captured.out

    def test_prints_doctors_when_found(self, capsys):
        with patch.object(svc, "doctores") as mock_coll:
            mock_coll.find.return_value = [_make_doc(), _make_doc()]
            svc.buscar_por_especialidad("Cardiología")
        captured = capsys.readouterr()
        assert "Encontrados" in captured.out
