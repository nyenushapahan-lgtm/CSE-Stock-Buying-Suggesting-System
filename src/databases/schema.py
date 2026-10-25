from typing import Tuple

import pandas as pd


HISTORICAL_PRICES_SCHEMA = """
    CREATE TABLE IF NOT EXISTS historical_prices (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        trade_date DATE NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        name VARCHAR(255) NOT NULL,
        open_price INT NOT NULL,
        high INT NOT NULL,
        low INT NOT NULL,
        close_price INT NOT NULL,
        volume INT NOT NULL,
        turnover INT NOT NULL,
        pct_change INT NOT NULL
    )
"""


def migrate_database_schema(connection, sector_mapping_path: str) -> Tuple[bool, str]:
    """Widen stock names and replace sectorized_table with the bundled mapping."""
    try:
        mapping = pd.read_csv(sector_mapping_path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as error:
        return False, f"Unable to load sector mapping for database migration: {error}"

    required_columns = {"symbol", "sector_name"}
    if not required_columns.issubset(mapping.columns):
        return False, "Sector mapping is missing symbol or sector_name columns"

    mapping = mapping.loc[:, ["symbol", "sector_name"]].copy()
    mapping["symbol"] = mapping["symbol"].astype("string").str.strip()
    mapping["sector_name"] = mapping["sector_name"].astype("string").str.strip()
    mapping = mapping.dropna(subset=["symbol", "sector_name"])
    mapping = mapping.loc[(mapping["symbol"] != "") & (mapping["sector_name"] != "")]
    if mapping.empty:
        return False, "Sector mapping contains no valid rows"
    if mapping["symbol"].duplicated().any():
        return False, "Sector mapping contains duplicate symbols"
    if mapping["symbol"].str.len().max() > 20 or mapping["sector_name"].str.len().max() > 100:
        return False, "Sector mapping values exceed the database column limits"

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(HISTORICAL_PRICES_SCHEMA)
        cursor.execute(
            "ALTER TABLE historical_prices MODIFY COLUMN name VARCHAR(255) NOT NULL"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sectorized_table (
                symbol VARCHAR(20) NOT NULL PRIMARY KEY,
                sectorName VARCHAR(100) NOT NULL
            )
            """
        )
        cursor.execute(
            "ALTER TABLE sectorized_table MODIFY COLUMN symbol VARCHAR(20) NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE sectorized_table MODIFY COLUMN sectorName VARCHAR(100) NOT NULL"
        )
        cursor.execute(
            """
            SELECT COUNT(*) AS primary_key_count
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'sectorized_table'
              AND index_name = 'PRIMARY'
            """
        )
        index_result = cursor.fetchone()
        if not index_result or not index_result["primary_key_count"]:
            cursor.execute("DELETE FROM sectorized_table")
            cursor.executemany(
                "INSERT INTO sectorized_table (symbol, sectorName) VALUES (%s, %s)",
                list(mapping.itertuples(index=False, name=None)),
            )
            cursor.execute("ALTER TABLE sectorized_table ADD PRIMARY KEY (symbol)")
        else:
            cursor.execute("DELETE FROM sectorized_table")
            cursor.executemany(
                "INSERT INTO sectorized_table (symbol, sectorName) VALUES (%s, %s)",
                list(mapping.itertuples(index=False, name=None)),
            )
        connection.commit()
        return True, f"Database schema ready; loaded {len(mapping)} sector mappings"
    except Exception as error:
        connection.rollback()
        return False, f"Database schema migration failed: {error}"
    finally:
        if cursor:
            cursor.close()
