"""Load raw data into BigQuery (dataset: raw).

Sources:
    - Olist CSV files in data/olist/        -> raw.olist_<name>
    - Synthetic ad spend in data/generated/ -> raw.ad_spend

Design notes:
    - Olist columns are loaded as STRING to keep the raw layer faithful to the source.
      Type casting happens later in the dbt staging models.
    - Every table gets a _loaded_at column, used later for freshness checks.
    - Each run replaces the table (WRITE_TRUNCATE), so the script is safe to re-run.

Usage:
    python ingestion/load_to_bigquery.py
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
RAW_DATASET = os.getenv("BQ_RAW_DATASET", "raw")

OLIST_DIR = Path("data/olist")
AD_SPEND_PATH = Path("data/generated/ad_spend.json")


def table_name_from_file(path: Path) -> str:
    """olist_orders_dataset.csv -> olist_orders"""
    return path.stem.replace("_dataset", "")


def load_dataframe(client: bigquery.Client, df: pd.DataFrame, table: str) -> None:
    df = df.copy()
    df["_loaded_at"] = datetime.now(timezone.utc)

    table_id = f"{PROJECT_ID}.{RAW_DATASET}.{table}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # wait for the job to finish

    print(f"  OK  {table_id}: {len(df):,} rows")


def load_olist(client: bigquery.Client) -> None:
    files = sorted(OLIST_DIR.glob("*.csv"))
    if not files:
        print(f"  No CSV files found in {OLIST_DIR}. Download Olist from Kaggle first.")
        return
    for path in files:
        df = pd.read_csv(path, dtype=str)
        load_dataframe(client, df, table_name_from_file(path))


def load_ad_spend(client: bigquery.Client) -> None:
    if not AD_SPEND_PATH.exists():
        print(f"  {AD_SPEND_PATH} not found. Run data_generation/generate_ad_spend.py first.")
        return
    records = json.loads(AD_SPEND_PATH.read_text(encoding="utf-8"))
    load_dataframe(client, pd.DataFrame(records), "ad_spend")


def main() -> None:
    if not PROJECT_ID:
        raise SystemExit("GCP_PROJECT_ID is not set. Copy .env.example to .env and fill it in.")

    client = bigquery.Client(project=PROJECT_ID)

    print("Loading Olist...")
    load_olist(client)
    print("Loading ad spend...")
    load_ad_spend(client)
    print("Done.")


if __name__ == "__main__":
    main()
