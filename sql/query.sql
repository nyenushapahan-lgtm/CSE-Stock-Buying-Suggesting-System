/*Historical Prices Table Structure*/
CREATE TABLE historical_prices(
    id INT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(20) NOT NULL,
    open_price INT NOT NULL,
    high INT NOT NULL,
    low INT NOT NULL,
    close_price INT NOT NULL,
    volume INT NOT NULL,
    turnover INT NOT NULL,
    pct_change INT NOT NULL
);
trade_date,symbol,name,open_price,high,low,close_price,volume,turnover,pct_change

/*Retrive from top 10 gainers from the week*/

SELECT 
    DISTINCT latest.name,
    latest.symbol,
    latest.close_price AS close_latest,
    previous.close_price AS close_previous,
    ((latest.close_price - previous.close_price) / previous.close_price) * 100 AS weekly_pct_change
FROM 
    historical_prices AS latest
JOIN 
    historical_prices AS previous 
    ON latest.symbol = previous.symbol
WHERE 
    latest.trade_date = '2026-07-10' 
    AND previous.trade_date = '2026-07-03'
ORDER BY 
    weekly_pct_change DESC
LIMIT 10;

/*Getting top gainers*/
SELECT
    DISTINCT(name),
    symbol,
    open_price,
    close_price,
    pct_change

FROM
    historical_prices
WHERE
    trade_date = '2026-07-10' AND
    close_price > 10.00

ORDER BY 
    pct_change DESC

LIMIT 10;

/*CREATE material sector*/
CREATE TABLE material_sector(
    industryGroupCode VARCHAR(10) PRIMARY KEY,
    gicsCode VARCHAR(10) NOT NULL,
    symbol VARCHAR(6) NOt NULL,
    industryGroupName VARCHAR(50) NOT NULL
);

/*Sectorized table*/
CREATE TABLE sectorized_table(
    symbol VARCHAR(6) NOT NULL,
    sectorName VARCHAR(50) NOT NULL
);

SELECT SUM(volume) AS totalVolume
FROM historical_prices,sectorized_table,material_sector
WHERE sectorized_table.symbol = material_sector.symbol AND sectorized_table.symbol = historical_prices.symbol AND material_sector.industryGroupName = 'Energy';

/*Filterd 6 days back to closed prices from best performed companies*/
SELECT
    DISTINCT trade_date,
    close_price
FROM historical_prices
WHERE symbol='BOGA.N0000'
ORDER BY trade_date DESC 
LIMIT 6;

/*Getting industry group Names*/
SELECT
    DISTINCT industryGroupName
FROM material_sector;

/*Getting company names that belongs to sectors*/
SELECT symbol FROM sectorized_table WHERE sectorName='Banks'

/*Getting latest investments in selected sectors*/
SELECT 
    DISTINCT trade_date,
    SUM(volume) AS volume
FROM historical_prices 
WHERE 
    symbol = 'CBNK.N0000' 
    AND 
    trade_date = (
        SELECT 
            MAX(trade_date) 
        FROM historical_prices 
        WHERE symbol='CBNK.N0000'
        );

/*Deleting data that older than month*/
DELETE FROM historical_prices 
WHERE trade_date < (
    SELECT MAX(trade_date) - INTERVAL 30 DAY 
    FROM historical_prices
    );

/*get Sector wise close_prices*/
SELECT trade_date,DISTINCT(h.symbol), h.close_price
FROM historical_prices h
JOIN sectorized_table s ON h.symbol = s.symbol
WHERE h.trade_date=(SELECT MAX(trade_date) - INTERVAL 5 DAY FROM historical_prices)
AND s.sectorName = 'Banks'
ORDER BY h.close_price DESC;

/*Getting days list*/
SELECT DISTINCT(trade_date) FROM historical_prices ORDER BY trade_date DESC LIMIT 5;

/*Getting */
SELECT 
    DISTINCT(trade_date),
    open_price,
    high,
    low,
    close_price,
    volume 
FROM historical_prices 
WHERE 
    symbol='LGL.X0000';

/*Getting data back to range*/
SELECT 
    trade_date,
    symbol,
    name,
    close_price,
    volume
FROM 
    historical_prices
WHERE 
    trade_date >= (
        SELECT trade_date
        FROM (
            SELECT DISTINCT trade_date
            FROM historical_prices
            ORDER BY trade_date DESC
            LIMIT 29, 1   -- 30th most recent distinct trading date (0-indexed)
        ) AS recent_dates
    )
ORDER BY 
    symbol, trade_date;