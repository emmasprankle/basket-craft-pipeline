import sys
from db import get_mysql_engine, get_pg_engine, validate_connections
from extract import extract_tables
from load import load_raw_tables
from transform import run_transform


def main():
    print("=== Basket Craft ELT Pipeline ===")

    print("\n[1/4] Validating database connections...")
    try:
        mysql_engine = get_mysql_engine()
        pg_engine = get_pg_engine()
        validate_connections(mysql_engine, pg_engine)
        print("  Connections OK")
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    print("\n[2/4] Extracting from MySQL...")
    try:
        tables = extract_tables(mysql_engine)
        for name, df in tables.items():
            print(f"  Extracted {name}: {len(df)} rows")
    except Exception as e:
        print(f"  ERROR during extract: {e}")
        sys.exit(1)

    print("\n[3/4] Loading into raw schema (PostgreSQL)...")
    try:
        load_raw_tables(tables, pg_engine)
    except Exception as e:
        print(f"  ERROR during load: {e}")
        sys.exit(1)

    print("\n[4/4] Transforming into analytics schema...")
    try:
        run_transform(pg_engine)
    except Exception as e:
        print(f"  ERROR during transform: {e}")
        sys.exit(1)

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()
