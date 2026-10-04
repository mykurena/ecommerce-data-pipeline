"""Generate a synthetic marketplace order feed (second sales channel), API-style JSON.

Output: data/generated/marketplace_orders.json
    {"meta": {...}, "orders": [ {...}, ... ]}

Dates are aligned with the Olist range so both channels can be compared.

Usage:
    python data_generation/generate_marketplace_orders.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
START_DATE = "2017-01-01"
END_DATE = "2018-08-31"
OUTPUT_PATH = Path("data/generated/marketplace_orders.json")

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "PE"]
STATE_WEIGHTS = [0.38, 0.15, 0.12, 0.07, 0.07, 0.05, 0.05, 0.04, 0.04, 0.03]
STATUSES = ["delivered", "shipped", "cancelled", "returned"]
STATUS_WEIGHTS = [0.84, 0.05, 0.06, 0.05]


def build_orders(rng: np.random.Generator) -> pd.DataFrame:
    dates = pd.date_range(START_DATE, END_DATE, freq="D")

    # expected orders per day: growth trend, weekday effect, November boost
    trend = np.linspace(0.6, 1.5, len(dates))
    weekday = np.where(dates.dayofweek < 5, 1.1, 0.8)
    seasonal = np.where(dates.month == 11, 1.7, 1.0)
    daily_orders = rng.poisson(8 * trend * weekday * seasonal)

    rows = []
    for date, n in zip(dates, daily_orders):
        for _ in range(int(n)):
            seconds = int(rng.integers(0, 86400))
            ordered_at = date + pd.Timedelta(seconds=seconds)
            units = int(rng.choice([1, 2, 3, 4], p=[0.62, 0.25, 0.09, 0.04]))
            unit_price = float(rng.lognormal(mean=4.4, sigma=0.5))
            gross = round(unit_price * units, 2)
            fee = round(gross * float(rng.uniform(0.12, 0.18)), 2)
            rows.append(
                {
                    "ordered_at": ordered_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": str(rng.choice(STATUSES, p=STATUS_WEIGHTS)),
                    "units": units,
                    "gross_amount_brl": gross,
                    "marketplace_fee_brl": fee,
                    "shipping_state": str(rng.choice(STATES, p=STATE_WEIGHTS)),
                }
            )

    df = pd.DataFrame(rows)
    df.insert(0, "marketplace_order_id", [f"mp_{i:07d}" for i in range(len(df))])
    return df


def main() -> None:
    rng = np.random.default_rng(SEED)
    df = build_orders(rng)

    payload = {
        "meta": {
            "source": "marketplace_api_simulated",
            "page": 1,
            "total_orders": len(df),
            "currency": "BRL",
        },
        "orders": json.loads(df.to_json(orient="records")),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload), encoding="utf-8")

    print(f"Wrote {len(df):,} orders to {OUTPUT_PATH}")
    print(df["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
