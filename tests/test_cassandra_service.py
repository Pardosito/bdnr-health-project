from unittest.mock import MagicMock, patch, call
from datetime import date
from bson import ObjectId
import pytest
import Cassandra.cassandra as cass_svc

_VALID_OID = ObjectId()


def _mock_session():
    s = MagicMock()
    s.prepare.return_value = MagicMock()
    return s


class TestRegistroInicioVisita:
    def test_calls_session_execute(self, capsys):
        mock_sess = _mock_session()
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    cass_svc.registro_inicio_visita("Juan", "Dr. García")
        mock_sess.execute.assert_called_once()
        captured = capsys.readouterr()
        assert "exitosamente" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    cass_svc.registro_inicio_visita("Juan", "Dr. García")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestRegistroFinVisita:
    def test_calls_session_execute(self, capsys):
        mock_sess = _mock_session()
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                    cass_svc.registro_fin_visita("Juan")
        mock_sess.execute.assert_called_once()
        captured = capsys.readouterr()
        assert "finalizada" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_visita_activa", return_value=None):
                    cass_svc.registro_fin_visita("Juan")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestObtenerVisitasDelDia:
    def test_prints_no_visits_when_empty(self, capsys):
        mock_sess = _mock_session()
        mock_sess.execute.return_value = []
        with patch.object(cass_svc, "session", mock_sess):
            cass_svc.obtener_visitas_del_dia("2024-01-15")
        captured = capsys.readouterr()
        assert "No hay visitas" in captured.out

    def test_prints_visit_rows(self, capsys):
        mock_sess = _mock_session()
        mock_row = MagicMock()
        mock_row.hora_inicio = MagicMock()
        mock_row.hora_fin = MagicMock()
        mock_row.doctor_id = "doc123"
        mock_row.paciente_id = "pac123"
        mock_row.tipo_visita = "CITA_GENERAL"
        mock_sess.execute.return_value = [mock_row]
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_by_id", return_value={"nombre": "Dr. A"}):
                with patch.object(cass_svc, "get_paciente_by_id", return_value={"nombre": "Juan"}):
                    with patch.object(cass_svc, "timeuuid_a_hora", return_value="10:00"):
                        cass_svc.obtener_visitas_del_dia("2024-01-15")
        captured = capsys.readouterr()
        assert "Dr. A" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            cass_svc.obtener_visitas_del_dia("2024-01-15")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestRegistrarSignoVital:
    def test_returns_none_when_patient_not_found(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value=None):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                result = cass_svc.registrar_signo_vital("Nonexistent", "Dr. A", "PRESION", "120/80")
        assert result is None
        captured = capsys.readouterr()
        assert "no encontrado" in captured.out

    def test_returns_none_when_doctor_not_found(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
            with patch.object(cass_svc, "get_doctor_id", return_value=None):
                result = cass_svc.registrar_signo_vital("Juan", "Nonexistent", "PRESION", "120/80")
        assert result is None
        captured = capsys.readouterr()
        assert "no encontrado" in captured.out

    def test_returns_none_for_invalid_tipo(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                result = cass_svc.registrar_signo_vital("Juan", "Dr. A", "INVALID_TIPO", "val")
        assert result is None
        captured = capsys.readouterr()
        assert "inválido" in captured.out

    def test_returns_none_when_no_active_visit(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_visita_activa", return_value=None):
                    with patch.object(cass_svc, "get_paciente_by_id", return_value={"nombre": "Juan"}):
                        result = cass_svc.registrar_signo_vital("Juan", "Dr. A", "PRESION", "120/80")
        assert result is None

    def test_registers_successfully(self, capsys):
        mock_sess = _mock_session()
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                        cass_svc.registrar_signo_vital("Juan", "Dr. A", "PRESION", "120/80")
        mock_sess.execute.assert_called_once()
        captured = capsys.readouterr()
        assert "PRESION" in captured.out

    def test_handles_session_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                        cass_svc.registrar_signo_vital("Juan", "Dr. A", "PRESION", "120/80")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestRegistrarRecetaPorVisita:
    def test_returns_when_patient_not_found(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value=None):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                cass_svc.registrar_receta_por_visita("Juan", "Dr. A", "Paracetamol")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_returns_when_no_active_visit(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_visita_activa", return_value=None):
                    cass_svc.registrar_receta_por_visita("Juan", "Dr. A", "Paracetamol")
        captured = capsys.readouterr()
        assert "no tiene visitas activas" in captured.out

    def test_returns_when_empty_receta(self, capsys):
        with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                    cass_svc.registrar_receta_por_visita("Juan", "Dr. A", "")
        captured = capsys.readouterr()
        assert "contenido" in captured.out

    def test_registers_successfully(self, capsys):
        mock_sess = _mock_session()
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value=_VALID_OID):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                        with patch.object(cass_svc, "expedientes"):
                            cass_svc.registrar_receta_por_visita("Juan", "Dr. A", "Paracetamol")
        captured = capsys.readouterr()
        assert "guardada" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                    with patch.object(cass_svc, "get_visita_activa", return_value="ts123"):
                        cass_svc.registrar_receta_por_visita("Juan", "Dr. A", "Paracetamol")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestRegistrarDiagnostico:
    def test_returns_error_when_doctor_not_found(self):
        with patch.object(cass_svc, "get_doctor_id", return_value=None):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                result = cass_svc.registrar_diagnostico_por_visita("Nonexistent", "Juan", "Asma")
        assert "Error" in result

    def test_returns_error_when_no_diagnostico(self):
        with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                result = cass_svc.registrar_diagnostico_por_visita("Dr. A", "Juan", "")
        assert "diagnóstico" in result

    def test_registers_successfully(self):
        mock_sess = _mock_session()
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_paciente_id", return_value=_VALID_OID):
                    with patch.object(cass_svc, "get_visita_activa", return_value=None):
                        with patch.object(cass_svc, "expedientes"):
                            result = cass_svc.registrar_diagnostico_por_visita("Dr. A", "Juan", "Asma")
        assert "Asma" in result

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_paciente_id", return_value=_VALID_OID):
                    with patch.object(cass_svc, "get_visita_activa", return_value=None):
                        result = cass_svc.registrar_diagnostico_por_visita("Dr. A", "Juan", "Asma")
        assert "Error" in result


class TestConsultarRecetasPorDoctor:
    def test_prints_message_when_no_rows(self, capsys):
        mock_sess = _mock_session()
        mock_sess.execute.return_value = None
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                cass_svc.consultar_recetas_por_doctor("Dr. A")
        captured = capsys.readouterr()
        assert "no tiene" in captured.out

    def test_prints_rows(self, capsys):
        mock_sess = _mock_session()
        mock_row = MagicMock()
        mock_row.doctor_id = "doc123"
        mock_row.paciente_id = "pac123"
        mock_row.receta = "Paracetamol"
        mock_sess.execute.return_value = [mock_row]
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_doctor_by_id", return_value={"nombre": "Dr. A"}):
                    with patch.object(cass_svc, "get_paciente_by_id", return_value={"nombre": "Juan"}):
                        cass_svc.consultar_recetas_por_doctor("Dr. A")
        captured = capsys.readouterr()
        assert "Paracetamol" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                cass_svc.consultar_recetas_por_doctor("Dr. A")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestObtenerDiagnosticoTratamientoPaciente:
    def test_returns_when_doctor_not_found(self, capsys):
        with patch.object(cass_svc, "get_doctor_id", return_value=None):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                cass_svc.obtener_diagnostico_tratamiento_paciente("Nonexistent", "Juan", "2024-01-01")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_returns_when_patient_not_found(self, capsys):
        with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
            with patch.object(cass_svc, "get_paciente_id", return_value=None):
                cass_svc.obtener_diagnostico_tratamiento_paciente("Dr. A", "Nonexistent", "2024-01-01")
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_returns_on_invalid_date(self, capsys):
        with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
            with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                cass_svc.obtener_diagnostico_tratamiento_paciente("Dr. A", "Juan", "not-a-date")
        captured = capsys.readouterr()
        assert "inválido" in captured.out

    def test_prints_no_diagnosticos(self, capsys):
        mock_sess = _mock_session()
        mock_sess.execute.return_value = []
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                    cass_svc.obtener_diagnostico_tratamiento_paciente("Dr. A", "Juan", "2024-01-01")
        captured = capsys.readouterr()
        assert "No se encontraron" in captured.out

    def test_prints_rows(self, capsys):
        mock_sess = _mock_session()
        mock_row = MagicMock()
        mock_row.doctor_id = "doc123"
        mock_row.paciente_id = "pac123"
        mock_row.diagnostico = "Asma"
        mock_row.fecha = "2024-01-01"
        mock_sess.execute.return_value = [mock_row]
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                    with patch.object(cass_svc, "get_doctor_by_id", return_value={"nombre": "Dr. A"}):
                        with patch.object(cass_svc, "get_paciente_by_id", return_value={"nombre": "Juan"}):
                            cass_svc.obtener_diagnostico_tratamiento_paciente("Dr. A", "Juan", "2024-01-01")
        captured = capsys.readouterr()
        assert "Asma" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_paciente_id", return_value="pac123"):
                    cass_svc.obtener_diagnostico_tratamiento_paciente("Dr. A", "Juan", "2024-01-01")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestVerificarDisponibilidadDoctor:
    def test_prints_availability(self, capsys):
        mock_sess = _mock_session()
        mock_row = MagicMock()
        mock_row.doctor_id = "doc123"
        mock_row.paciente_id = "pac123"
        mock_row.tipo_visita = "CITA_GENERAL"
        mock_row.fecha = "2024-01-15"
        mock_sess.execute.return_value = [mock_row]
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                with patch.object(cass_svc, "get_doctor_by_id", return_value={"nombre": "Dr. A"}):
                    with patch.object(cass_svc, "get_paciente_by_id", return_value={"nombre": "Juan"}):
                        cass_svc.verificar_disponibilidad_doctor("Dr. A", "2024-01-15")
        captured = capsys.readouterr()
        assert "Dr. A" in captured.out

    def test_handles_exception(self, capsys):
        mock_sess = _mock_session()
        mock_sess.prepare.side_effect = Exception("fail")
        with patch.object(cass_svc, "session", mock_sess):
            with patch.object(cass_svc, "get_doctor_id", return_value="doc123"):
                cass_svc.verificar_disponibilidad_doctor("Dr. A", "2024-01-15")
        captured = capsys.readouterr()
        assert "Error" in captured.out
