"""Tests for Mongo/mongo.py connection logic."""
import importlib
from unittest.mock import MagicMock, patch
import pytest
import Mongo.mongo as mongo_mod


class TestMongoConnect:
    def test_connect_raises_on_ping_failure(self):
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = Exception("ping failed")
        with patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            with pytest.raises(Exception, match="ping failed"):
                mongo_mod._connect()

    def test_connect_logs_warning_on_index_failure(self):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_doctores = MagicMock()
        mock_doctores.create_index.side_effect = Exception("index fail")
        mock_db.__getitem__.side_effect = lambda name: mock_doctores
        with patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            client, db, doctores, pacientes, expedientes = mongo_mod._connect()
        assert client is mock_client

    def test_module_level_except_sets_none_on_failure(self):
        import pymongo
        original_mc = pymongo.MongoClient
        pymongo.MongoClient = MagicMock(side_effect=Exception("no mongo"))
        try:
            importlib.reload(mongo_mod)
            assert mongo_mod.doctores is None
            assert mongo_mod.pacientes is None
            assert mongo_mod.expedientes is None
        finally:
            pymongo.MongoClient = original_mc
            importlib.reload(mongo_mod)
