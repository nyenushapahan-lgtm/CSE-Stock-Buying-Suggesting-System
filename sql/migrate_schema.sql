-- Run in the configured database to repair the stock and sector mapping schema.
-- The application also refreshes sectorized_table from my_mapped_symboled.csv.

ALTER TABLE historical_prices
    MODIFY COLUMN name VARCHAR(255) NOT NULL;

CREATE TABLE IF NOT EXISTS sectorized_table (
    symbol VARCHAR(20) NOT NULL PRIMARY KEY,
    sectorName VARCHAR(100) NOT NULL
);

ALTER TABLE sectorized_table
    MODIFY COLUMN symbol VARCHAR(20) NOT NULL,
    MODIFY COLUMN sectorName VARCHAR(100) NOT NULL;
