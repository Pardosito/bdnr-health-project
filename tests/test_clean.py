from unittest.mock import MagicMock, patch
import clean


class TestLimpiarTodo:
    def test_cleans_mongo_when_connected(self, capsys):
        mock_db = MagicMock()
        with patch.object(clean, "get_mongo", return_value=mock_db):
            with patch.object(clean, "get_dgraph", return_value=None):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_session = MagicMock()
                    mock_cluster.return_value.connect.return_value = mock_session
                    clean.limpiar_todo()
        mock_db.client.drop_database.assert_called_once()
        captured = capsys.readouterr()
        assert "eliminada" in captured.out

    def test_prints_message_when_mongo_none(self, capsys):
        with patch.object(clean, "get_mongo", return_value=None):
            with patch.object(clean, "get_dgraph", return_value=None):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_cluster.return_value.connect.return_value = MagicMock()
                    clean.limpiar_todo()
        captured = capsys.readouterr()
        assert "No hay conexión" in captured.out

    def test_handles_mongo_exception(self, capsys):
        with patch.object(clean, "get_mongo", side_effect=Exception("mongo fail")):
            with patch.object(clean, "get_dgraph", return_value=None):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_cluster.return_value.connect.return_value = MagicMock()
                    clean.limpiar_todo()
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_cleans_cassandra(self, capsys):
        with patch.object(clean, "get_mongo", return_value=None):
            with patch.object(clean, "get_dgraph", return_value=None):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_sess = MagicMock()
                    mock_cluster.return_value.connect.return_value = mock_sess
                    clean.limpiar_todo()
        mock_sess.execute.assert_called_once()

    def test_handles_cassandra_exception(self, capsys):
        with patch.object(clean, "get_mongo", return_value=None):
            with patch.object(clean, "get_dgraph", return_value=None):
                with patch.object(clean, "Cluster", side_effect=Exception("cass fail")):
                    clean.limpiar_todo()
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_cleans_dgraph_when_connected(self, capsys):
        mock_client = MagicMock()
        with patch.object(clean, "get_mongo", return_value=None):
            with patch.object(clean, "get_dgraph", return_value=mock_client):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_cluster.return_value.connect.return_value = MagicMock()
                    with patch.object(clean, "pydgraph") as mock_pd:
                        clean.limpiar_todo()
        mock_client.alter.assert_called_once()

    def test_handles_dgraph_exception(self, capsys):
        with patch.object(clean, "get_mongo", return_value=None):
            with patch.object(clean, "get_dgraph", side_effect=Exception("dg fail")):
                with patch.object(clean, "Cluster") as mock_cluster:
                    mock_cluster.return_value.connect.return_value = MagicMock()
                    clean.limpiar_todo()
        captured = capsys.readouterr()
        assert "Error" in captured.out
