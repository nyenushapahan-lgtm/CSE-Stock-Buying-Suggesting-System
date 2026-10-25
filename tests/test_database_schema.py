import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.databases.schema import migrate_database_schema


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.batch_rows = []
        self.closed = False
        self._fetch_result = None

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if "information_schema.statistics" in query:
            self._fetch_result = {"primary_key_count": 0}

    def executemany(self, query, rows):
        self.executed.append((query, None))
        self.batch_rows = list(rows)

    def fetchone(self):
        return self._fetch_result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False, **kwargs):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class DatabaseSchemaTests(unittest.TestCase):
    def test_migration_widens_names_and_loads_sector_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping_path = Path(temp_dir) / "mapping.csv"
            pd.DataFrame(
                [
                    {"symbol": "AAA.N0000", "sector_name": "Banks"},
                    {"symbol": "BBB.N0000", "sector_name": "Utilities"},
                ]
            ).to_csv(mapping_path, index=False)
            connection = FakeConnection()

            success, message = migrate_database_schema(connection, str(mapping_path))

            self.assertTrue(success, message)
            self.assertIn("2 sector mappings", message)
            executed_sql = "\n".join(query for query, _ in connection.fake_cursor.executed)
            self.assertIn("MODIFY COLUMN name VARCHAR(255)", executed_sql)
            self.assertIn("CREATE TABLE IF NOT EXISTS sectorized_table", executed_sql)
            self.assertIn("ADD PRIMARY KEY (symbol)", executed_sql)
            self.assertEqual(
                connection.fake_cursor.batch_rows,
                [("AAA.N0000", "Banks"), ("BBB.N0000", "Utilities")],
            )
            self.assertTrue(connection.committed)
            self.assertFalse(connection.rolled_back)

    def test_migration_rejects_ambiguous_duplicate_symbols(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping_path = Path(temp_dir) / "mapping.csv"
            pd.DataFrame(
                [
                    {"symbol": "AAA", "sector_name": "Banks"},
                    {"symbol": "AAA", "sector_name": "Utilities"},
                ]
            ).to_csv(mapping_path, index=False)
            connection = FakeConnection()

            success, message = migrate_database_schema(connection, str(mapping_path))

            self.assertFalse(success)
            self.assertIn("duplicate symbols", message)
            self.assertFalse(connection.fake_cursor.executed)


if __name__ == "__main__":
    unittest.main()
