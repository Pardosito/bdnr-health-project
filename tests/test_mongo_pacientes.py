from unittest.mock import MagicMock, patch
import pytest
import Mongo.services.pacientes_service as svc


def _make_pac():
    return {
        "_id": "pac_id_123",
        "nombre": "Juan Pérez",
        "fecha_nac": "1990-05-15",
        "sexo": "M",
        "telefono": "555-1234",
        "correo": "juan@test.com",
        "cont_eme": "María Pérez",
        "direccion": "Calle 1",
        "seguro": "GNP",
        "poliza": "POL123"
    }


class TestRegistrarPaciente:
    def test_returns_mongo_id(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "pac123"
        with patch.object(svc, "pacientes") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=None):
                mock_coll.insert_one.return_value = mock_result
                result = svc.registrar_paciente(_make_pac())
        assert result == "pac123"

    def test_syncs_to_dgraph(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "pac123"
        mock_client = MagicMock()
        with patch.object(svc, "pacientes") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=mock_client):
                with patch.object(svc, "dg_utils") as mock_dg:
                    mock_coll.insert_one.return_value = mock_result
                    result = svc.registrar_paciente(_make_pac())
        assert result == "pac123"
        mock_dg.crear_paciente.assert_called_once()

    def test_handles_invalid_fecha_nac(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "pac123"
        pac = _make_pac()
        pac["fecha_nac"] = "not-a-date"
        with patch.object(svc, "pacientes") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=MagicMock()):
                with patch.object(svc, "dg_utils"):
                    mock_coll.insert_one.return_value = mock_result
                    result = svc.registrar_paciente(pac)
        assert result == "pac123"

    def test_handles_dgraph_exception(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "pac123"
        with patch.object(svc, "pacientes") as mock_coll:
            with patch.object(svc, "get_dgraph", return_value=MagicMock()):
                with patch.object(svc, "dg_utils") as mock_dg:
                    mock_dg.crear_paciente.side_effect = Exception("fail")
                    mock_coll.insert_one.return_value = mock_result
                    result = svc.registrar_paciente(_make_pac())
        assert result == "pac123"


class TestBuscarPacientePorNombre:
    def test_returns_error_when_not_found(self):
        with patch.object(svc, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = None
            result = svc.buscar_paciente_por_nombre("Nonexistent")
        assert result == {"error": svc._PACIENTE_NO_ENCONTRADO}

    def test_prints_patient_when_found(self, capsys):
        mock_pac = _make_pac()
        with patch.object(svc, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = mock_pac
            svc.buscar_paciente_por_nombre("Juan")
        captured = capsys.readouterr()
        assert "Juan" in captured.out


class TestObtenerPacienteYExpediente:
    def test_returns_not_found_message(self):
        with patch.object(svc, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = None
            result = svc.obtener_paciente_y_expediente("Nonexistent")
        assert result == svc._PACIENTE_NO_ENCONTRADO

    def test_prints_with_expediente(self, capsys):
        mock_pac = _make_pac()
        mock_exp = {"alergias": [], "padecimientos": ["Asma"], "tratamientos": []}
        with patch.object(svc, "pacientes") as mock_pacs:
            with patch.object(svc, "expedientes") as mock_exps:
                mock_pacs.find_one.return_value = mock_pac
                mock_exps.find_one.return_value = mock_exp
                svc.obtener_paciente_y_expediente("Juan")
        captured = capsys.readouterr()
        assert "Juan" in captured.out

    def test_prints_without_expediente(self, capsys):
        mock_pac = _make_pac()
        with patch.object(svc, "pacientes") as mock_pacs:
            with patch.object(svc, "expedientes") as mock_exps:
                mock_pacs.find_one.return_value = mock_pac
                mock_exps.find_one.return_value = None
                svc.obtener_paciente_y_expediente("Juan")
        captured = capsys.readouterr()
        assert "Juan" in captured.out

    def test_finds_by_object_id(self, capsys):
        mock_pac = _make_pac()
        with patch.object(svc, "pacientes") as mock_pacs:
            with patch.object(svc, "ObjectId"):
                with patch.object(svc, "expedientes") as mock_exps:
                    mock_pacs.find_one.return_value = mock_pac
                    mock_exps.find_one.return_value = None
                    svc.obtener_paciente_y_expediente("507f1f77bcf86cd799439011")
        captured = capsys.readouterr()
        assert "Juan" in captured.out


class TestFiltrarPacientes:
    def test_prints_results(self, capsys):
        mock_pac = _make_pac()
        mock_exp = {"alergias": [], "padecimientos": [], "tratamientos": []}
        with patch.object(svc, "pacientes") as mock_pacs:
            with patch.object(svc, "expedientes") as mock_exps:
                with patch.object(svc, "ObjectId"):
                    mock_pacs.find.return_value = [mock_pac]
                    mock_exps.find_one.return_value = mock_exp
                    svc.filtrar_pacientes({"sexo": "M"})
        captured = capsys.readouterr()
        assert "Juan" in captured.out

    def test_handles_missing_expediente(self, capsys):
        mock_pac = _make_pac()
        with patch.object(svc, "pacientes") as mock_pacs:
            with patch.object(svc, "expedientes") as mock_exps:
                with patch.object(svc, "ObjectId"):
                    mock_pacs.find.return_value = [mock_pac]
                    mock_exps.find_one.return_value = None
                    svc.filtrar_pacientes({})
        captured = capsys.readouterr()
        assert "Juan" in captured.out


class TestBuscarPacientePorId:
    def test_returns_error_for_invalid_id(self):
        result = svc.buscar_paciente_por_id("not-an-id")
        assert "error" in result

    def test_returns_error_when_not_found(self):
        with patch.object(svc, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = None
            result = svc.buscar_paciente_por_id("507f1f77bcf86cd799439011")
        assert "error" in result

    def test_prints_paciente_when_found(self, capsys):
        with patch.object(svc, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = _make_pac()
            svc.buscar_paciente_por_id("507f1f77bcf86cd799439011")
        captured = capsys.readouterr()
        assert "Juan" in captured.out


class TestObtenerInfoMedica:
    def test_returns_not_found_when_no_patient(self):
        with patch.object(svc, "get_paciente_id", return_value=None):
            result = svc.obtener_info_medica("Nonexistent")
        assert result == "Paciente no encontrado"

    def test_returns_no_expediente_message(self):
        with patch.object(svc, "get_paciente_id", return_value="pac123"):
            with patch.object(svc, "expedientes") as mock_exps:
                mock_exps.find_one.return_value = None
                result = svc.obtener_info_medica("Juan")
        assert result == "Paciente no tiene expediente creado"

    def test_returns_clinical_data(self):
        mock_exp = {"alergias": ["Polen"], "padecimientos": ["Asma"], "tratamientos": ["Salbutamol"]}
        with patch.object(svc, "get_paciente_id", return_value="pac123"):
            with patch.object(svc, "expedientes") as mock_exps:
                with patch.object(svc, "buscar_paciente_por_id"):
                    mock_exps.find_one.return_value = mock_exp
                    result = svc.obtener_info_medica("Juan")
        assert result["alergias"] == ["Polen"]
        assert result["padecimientos"] == ["Asma"]
