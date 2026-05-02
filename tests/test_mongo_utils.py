from unittest.mock import MagicMock, patch
import pytest
import Mongo.utils as utils_mod


class TestGetDoctorId:
    def test_returns_id_when_found(self):
        mock_doc = {"_id": "doc_id_123", "nombre": "Dr. Test"}
        with patch.object(utils_mod, "doctores") as mock_coll:
            mock_coll.find_one.return_value = mock_doc
            result = utils_mod.get_doctor_id("Dr. Test")
        assert result == "doc_id_123"

    def test_returns_none_when_not_found(self):
        with patch.object(utils_mod, "doctores") as mock_coll:
            mock_coll.find_one.return_value = None
            result = utils_mod.get_doctor_id("Nonexistent")
        assert result is None


class TestGetDoctorById:
    def test_returns_error_for_invalid_id(self):
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            mock_oid.is_valid.return_value = False
            result = utils_mod.get_doctor_by_id("invalid")
        assert result == "ID de doctor inválido"

    def test_returns_not_found_when_none(self):
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            with patch.object(utils_mod, "doctores") as mock_coll:
                mock_oid.is_valid.return_value = True
                mock_coll.find_one.return_value = None
                result = utils_mod.get_doctor_by_id("507f1f77bcf86cd799439011")
        assert result == "Doctor no encontrado"

    def test_returns_doc_when_found(self):
        mock_doc = {"_id": "id1", "nombre": "Dr. Test"}
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            with patch.object(utils_mod, "doctores") as mock_coll:
                mock_oid.is_valid.return_value = True
                mock_coll.find_one.return_value = mock_doc
                result = utils_mod.get_doctor_by_id("507f1f77bcf86cd799439011")
        assert result == mock_doc


class TestGetPacienteId:
    def test_returns_id_when_found(self):
        mock_pac = {"_id": "pac_id_123", "nombre": "Juan"}
        with patch.object(utils_mod, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = mock_pac
            result = utils_mod.get_paciente_id("Juan")
        assert result == "pac_id_123"

    def test_returns_none_when_not_found(self):
        with patch.object(utils_mod, "pacientes") as mock_coll:
            mock_coll.find_one.return_value = None
            result = utils_mod.get_paciente_id("Nonexistent")
        assert result is None


class TestGetPacienteById:
    def test_returns_error_for_invalid_id(self):
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            mock_oid.is_valid.return_value = False
            result = utils_mod.get_paciente_by_id("invalid")
        assert result == "ID de paciente inválido"

    def test_returns_not_found_when_none(self):
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            with patch.object(utils_mod, "pacientes") as mock_coll:
                mock_oid.is_valid.return_value = True
                mock_coll.find_one.return_value = None
                result = utils_mod.get_paciente_by_id("507f1f77bcf86cd799439011")
        assert result == "Paciente no encontrado"

    def test_returns_paciente_when_found(self):
        mock_pac = {"_id": "id1", "nombre": "Juan"}
        with patch.object(utils_mod, "ObjectId") as mock_oid:
            with patch.object(utils_mod, "pacientes") as mock_coll:
                mock_oid.is_valid.return_value = True
                mock_coll.find_one.return_value = mock_pac
                result = utils_mod.get_paciente_by_id("507f1f77bcf86cd799439011")
        assert result == mock_pac
