"""Convert a CSE trade-summary CSV into the application's market-data schema.

Run this script from the folder containing trade-summary.csv:
    python /path/to/convert_trade_summary.py

Update TRADE_DATE below to the date represented by the source file.
"""

import csv


# Set this to the trading date for the source summary, in YYYY-MM-DD format.
TRADE_DATE = "2025-01-01"

INPUT_FILE = "trade-summary.csv"
OUTPUT_FILE = "trade-summary-transformed.csv"
OUTPUT_HEADERS = [
    "trade_date",
    "symbol",
    "name",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "turnover",
    "pct_change",
]

HEADER_KEYWORDS = {
    "symbol": "symbol",
    "name": "company name",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "last trade",
    "volume": "share volume",
    "turnover": "trade volume",
    "pct_change": "change",
}


def normalize_header(header):
    for character in ("*", "(", ")", "%", "."):
        header = header.replace(character, "")
    return " ".join(header.lower().split())


def find_source_columns(source_headers):
    normalized_headers = [normalize_header(header) for header in source_headers]
    source_columns = {}

    for target, keyword in HEADER_KEYWORDS.items():
        exact_matches = [
            index
            for index, header in enumerate(normalized_headers)
            if header == keyword
        ]
        matches = exact_matches or [
            index
            for index, header in enumerate(normalized_headers)
            if header.startswith(keyword + " ")
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one source column matching {keyword!r} for {target!r}; "
                f"found {len(matches)}"
            )
        source_columns[target] = matches[0]

    return source_columns


def format_decimal(value):
    return f"{float(value.replace(',', '').strip()):.2f}"


def format_integer(value):
    number = float(value.replace(",", "").strip())
    if not number.is_integer():
        raise ValueError(f"Expected a whole number, got {value!r}")
    return str(int(number))


def main():
    rows_read = 0
    rows_written = 0
    rows_skipped = 0

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as source_file:
        reader = csv.reader(source_file)
        try:
            source_headers = next(reader)
        except StopIteration as error:
            raise ValueError(f"{INPUT_FILE} is empty") from error

        source_columns = find_source_columns(source_headers)
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as output_file:
            writer = csv.writer(output_file, quoting=csv.QUOTE_ALL)
            output_file.write(",".join(OUTPUT_HEADERS) + "\n")

            for source_row in reader:
                if not source_row:
                    rows_skipped += 1
                    continue
                rows_read += 1
                if len(source_row) != len(source_headers):
                    raise ValueError(
                        f"Input row {reader.line_num} has {len(source_row)} fields; "
                        f"expected {len(source_headers)}"
                    )

                symbol = source_row[source_columns["symbol"]].strip()
                name = " ".join(source_row[source_columns["name"]].split())
                output_row = [
                    TRADE_DATE,
                    symbol,
                    name,
                    format_decimal(source_row[source_columns["open"]]),
                    format_decimal(source_row[source_columns["high"]]),
                    format_decimal(source_row[source_columns["low"]]),
                    format_decimal(source_row[source_columns["close"]]),
                    format_integer(source_row[source_columns["volume"]]),
                    format_integer(source_row[source_columns["turnover"]]),
                    format_decimal(source_row[source_columns["pct_change"]]),
                ]
                writer.writerow(output_row)
                rows_written += 1

    with open(OUTPUT_FILE, "r", encoding="utf-8", newline="") as output_file:
        output_reader = csv.reader(output_file)
        output_headers = next(output_reader)
        assert output_headers == OUTPUT_HEADERS
        output_rows = list(output_reader)
        assert len(output_rows) == rows_read
        assert all(len(row) == 10 for row in output_rows)

    print(
        f"Rows read: {rows_read}; rows written: {rows_written}; "
        f"rows skipped: {rows_skipped}"
    )


if __name__ == "__main__":
    main()
