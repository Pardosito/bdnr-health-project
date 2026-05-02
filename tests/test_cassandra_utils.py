from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest


class TestTimeuuidAHora:
    def test_returns_na_for_none(self):
        from Cassandra.utils import timeuuid_a_hora
        assert timeuuid_a_hora(None) == "N/A"

    def test_returns_formatted_time(self):
        from Cassandra.utils import timeuuid_a_hora
        mock_uuid = MagicMock()
        mock_dt = datetime(2024, 1, 15, 10, 30)
        with patch("Cassandra.utils.datetime_from_uuid1", return_value=mock_dt):
            result = timeuuid_a_hora(mock_uuid)
        assert result == "10:30"

    def test_returns_invalid_on_exception(self):
        from Cassandra.utils import timeuuid_a_hora
        mock_uuid = MagicMock()
        with patch("Cassandra.utils.datetime_from_uuid1", side_effect=Exception("bad")):
            result = timeuuid_a_hora(mock_uuid)
        assert result == "Formato inválido"


class TestGetVisitaId:
    def test_returns_none_when_no_row(self):
        from Cassandra.utils import get_visita_id
        mock_session = MagicMock()
        mock_session.prepare.return_value = MagicMock()
        mock_session.execute.return_value.one.return_value = None
        result = get_visita_id(mock_session, "2024-01-01", "doc1", "pac1")
        assert result is None

    def test_returns_hora_inicio_when_row_exists(self):
        from Cassandra.utils import get_visita_id
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.hora_inicio = "09:00"
        mock_session.execute.return_value.one.return_value = mock_row
        result = get_visita_id(mock_session, "2024-01-01", "doc1", "pac1")
        assert result == "09:00"

    def test_returns_none_on_exception(self):
        from Cassandra.utils import get_visita_id
        mock_session = MagicMock()
        mock_session.prepare.side_effect = Exception("error")
        result = get_visita_id(mock_session, "2024-01-01", "doc1", "pac1")
        assert result is None


class TestGetVisitaActiva:
    def test_returns_none_when_paciente_id_is_none(self):
        from Cassandra.utils import get_visita_activa
        mock_session = MagicMock()
        result = get_visita_activa(mock_session, None)
        assert result is None

    def test_returns_timestamp_when_fin_is_none(self):
        from Cassandra.utils import get_visita_activa
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.timestamp_fin = None
        mock_row.timestamp_inicio = "ts_inicio"
        mock_session.execute.return_value.one.return_value = mock_row
        result = get_visita_activa(mock_session, "pac1")
        assert result == "ts_inicio"

    def test_returns_none_when_visita_finalizada(self):
        from Cassandra.utils import get_visita_activa
        mock_session = MagicMock()
        mock_row = MagicMock()
        mock_row.timestamp_fin = "ts_fin"
        mock_session.execute.return_value.one.return_value = mock_row
        result = get_visita_activa(mock_session, "pac1")
        assert result is None

    def test_returns_none_when_no_row(self):
        from Cassandra.utils import get_visita_activa
        mock_session = MagicMock()
        mock_session.execute.return_value.one.return_value = None
        result = get_visita_activa(mock_session, "pac1")
        assert result is None


class TestEnums:
    def test_visitas_enum_has_expected_members(self):
        from Cassandra.utils import VisitasEnum
        assert "CONSULTA_INICIAL" in VisitasEnum.__members__
        assert "URGENCIA" in VisitasEnum.__members__

    def test_mediciones_enum_has_expected_members(self):
        from Cassandra.utils import MedicionesEnum
        assert "PRESION" in MedicionesEnum.__members__
        assert "PESO" in MedicionesEnum.__members__
        assert "TEMPERATURA" in MedicionesEnum.__members__
