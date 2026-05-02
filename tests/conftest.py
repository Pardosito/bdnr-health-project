"""
Patches all database drivers before any project module is imported,
so tests run without live MongoDB / Cassandra / Dgraph instances.
"""
import sys
from unittest.mock import MagicMock

# ── pymongo ──────────────────────────────────────────────────────────────────
pymongo_mod = MagicMock()
pymongo_errors_mod = MagicMock()
pymongo_errors_mod.ServerSelectionTimeoutError = type("ServerSelectionTimeoutError", (Exception,), {})
pymongo_errors_mod.ConnectionFailure = type("ConnectionFailure", (Exception,), {})
pymongo_mod.errors = pymongo_errors_mod
pymongo_mod.MongoClient = MagicMock()
sys.modules["pymongo"] = pymongo_mod
sys.modules["pymongo.errors"] = pymongo_errors_mod

# ── cassandra-driver ──────────────────────────────────────────────────────────
cass_mod = MagicMock()
cass_cluster_mod = MagicMock()
cass_cluster_mod.Cluster = MagicMock()
cass_cluster_mod.NoHostAvailable = type("NoHostAvailable", (Exception,), {})
cass_util_mod = MagicMock()
cass_util_mod.uuid_from_time = MagicMock()
cass_util_mod.datetime_from_uuid1 = MagicMock()
sys.modules["cassandra"] = cass_mod
sys.modules["cassandra.cluster"] = cass_cluster_mod
sys.modules["cassandra.util"] = cass_util_mod

# ── pydgraph ──────────────────────────────────────────────────────────────────
pydgraph_mod = MagicMock()
pydgraph_mod.DgraphClientStub = MagicMock()
pydgraph_mod.DgraphClient = MagicMock()
pydgraph_mod.Operation = MagicMock()
sys.modules["pydgraph"] = pydgraph_mod

# ── faker ─────────────────────────────────────────────────────────────────────
sys.modules["faker"] = MagicMock()
