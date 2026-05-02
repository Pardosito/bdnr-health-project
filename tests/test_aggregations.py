from unittest.mock import MagicMock, patch
import pytest
import Mongo.pipelines.aggregations as agg_mod
from Mongo.pipelines.aggregations import _calcular_edad


class TestEdadPromedioYMeds:
    def test_returns_aggregate_result(self):
        expected = [{"diagnostico": "Asma", "edad_promedio": 35.0}]
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter(expected)
            result = agg_mod.edad_promedio_y_meds("Asma")
        assert result == expected

    def test_calls_aggregate_with_match_stage(self):
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter([])
            agg_mod.edad_promedio_y_meds("Diabetes Tipo 2")
        pipeline = mock_exps.aggregate.call_args[0][0]
        assert any("$match" in stage for stage in pipeline)

    def test_returns_empty_when_no_results(self):
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter([])
            result = agg_mod.edad_promedio_y_meds("Nonexistent")
        assert result == []


class TestBucketsPorEdad:
    def test_returns_bucket_result(self):
        expected = [{"_id": 18, "total": 5}]
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter(expected)
            result = agg_mod.buckets_por_edad("Hipertensión")
        assert result == expected

    def test_calls_aggregate_with_bucket_stage(self):
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter([])
            agg_mod.buckets_por_edad("Asma")
        pipeline = mock_exps.aggregate.call_args[0][0]
        assert any("$bucket" in stage for stage in pipeline)

    def test_returns_empty_when_no_results(self):
        with patch.object(agg_mod, "expedientes") as mock_exps:
            mock_exps.aggregate.return_value = iter([])
            result = agg_mod.buckets_por_edad("Nonexistent")
        assert result == []


class TestCalcularEdad:
    def test_returns_age_for_valid_date(self):
        age = _calcular_edad("1990-01-01")
        assert isinstance(age, int)
        assert age > 0

    def test_returns_none_for_invalid_date(self):
        result = _calcular_edad("not-a-date")
        assert result is None

    def test_returns_none_for_empty_string(self):
        result = _calcular_edad("")
        assert result is None
