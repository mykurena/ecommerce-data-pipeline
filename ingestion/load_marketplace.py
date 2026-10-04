"""Load the synthetic marketplace feed into BigQuery (raw.marketplace_orders).

Reuses the loader from load_to_bigquery.py (adds _loaded_at, replaces the table on each run).

Usage:
    python ingestion/load_marketplace.py
"""
import json
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from load_to_bigquery import PROJECT_ID, load_dataframe

MARKETPLACE_PATH = Path("data/generated/marketplace_orders.json")


def main() -> None:
    if not PROJECT_ID:
        raise SystemExit("GCP_PROJECT_ID is not set. Copy .env.example to .env and fill it in.")
    if not MARKETPLACE_PATH.exists():
        raise SystemExit(f"{MARKETPLACE_PATH} not found. Run data_generation/generate_marketplace_orders.py first.")

    payload = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(payload["orders"])

    client = bigquery.Client(project=PROJECT_ID)
    print("Loading marketplace orders...")
    load_dataframe(client, df, "marketplace_orders")
    print("Done.")


if __name__ == "__main__":
    main()
