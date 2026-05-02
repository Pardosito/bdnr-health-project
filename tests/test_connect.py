from unittest.mock import MagicMock, patch
import pytest
import connect


class TestGetMongo:
    def test_returns_db_on_success(self):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        with patch.object(connect, "MongoClient", return_value=mock_client):
            result = connect.get_mongo()
        assert result == mock_db

    def test_returns_none_on_timeout(self):
        from pymongo.errors import ServerSelectionTimeoutError
        mock_client = MagicMock()
        mock_client.server_info.side_effect = ServerSelectionTimeoutError()
        with patch.object(connect, "MongoClient", return_value=mock_client):
            result = connect.get_mongo()
        assert result is None

    def test_returns_none_on_connection_failure(self):
        from pymongo.errors import ConnectionFailure
        mock_client = MagicMock()
        mock_client.server_info.side_effect = ConnectionFailure()
        with patch.object(connect, "MongoClient", return_value=mock_client):
            result = connect.get_mongo()
        assert result is None


class TestGetCassandra:
    def test_returns_session_on_success(self):
        mock_session = MagicMock()
        mock_cluster = MagicMock()
        mock_cluster.connect.return_value = mock_session
        with patch.object(connect, "Cluster", return_value=mock_cluster):
            with patch.object(connect, "model"):
                result = connect.get_cassandra()
        assert result == mock_session

    def test_returns_none_on_no_host_available(self):
        from cassandra.cluster import NoHostAvailable
        with patch.object(connect, "Cluster") as mc:
            mc.return_value.connect.side_effect = NoHostAvailable("no hosts", {})
            result = connect.get_cassandra()
        assert result is None

    def test_returns_none_on_exception(self):
        with patch.object(connect, "Cluster") as mc:
            mc.return_value.connect.side_effect = Exception("no host")
            result = connect.get_cassandra()
        assert result is None


class TestGetDgraph:
    def test_returns_client_on_success(self):
        mock_stub = MagicMock()
        mock_client = MagicMock()
        with patch.object(connect.pydgraph, "DgraphClientStub", return_value=mock_stub):
            with patch.object(connect.pydgraph, "DgraphClient", return_value=mock_client):
                result = connect.get_dgraph()
        assert result == mock_client

    def test_returns_none_on_exception(self):
        with patch.object(connect.pydgraph, "DgraphClientStub", side_effect=Exception("fail")):
            result = connect.get_dgraph()
        assert result is None


class TestGetAllConnections:
    def test_returns_dict_with_all_keys(self):
        with patch.object(connect, "get_mongo", return_value="mongo"):
            with patch.object(connect, "get_cassandra", return_value="cassandra"):
                with patch.object(connect, "get_dgraph", return_value="dgraph"):
                    result = connect.get_all_connections()
        assert set(result.keys()) == {"mongo", "cassandra", "dgraph"}
