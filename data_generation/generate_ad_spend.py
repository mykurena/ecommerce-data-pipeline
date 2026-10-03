"""Generate synthetic daily ad spend (Meta Ads / Google Ads) aligned with the Olist date range.

Output: data/generated/ad_spend.json (list of records, one per campaign per day)

Usage:
    python data_generation/generate_ad_spend.py
    python data_generation/generate_ad_spend.py --inject-issues   # adds duplicates/nulls to test data-quality alerts
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START_DATE = "2017-01-01" 
END_DATE = "2018-08-31"
OUTPUT_PATH = Path("data/generated/ad_spend.json")

# platform, campaign, base daily spend (BRL), typical CTR, typical CPC (BRL)
CAMPAIGNS = [
    ("meta_ads", "brand_awareness", 180.0, 0.011, 0.55),
    ("meta_ads", "retargeting", 90.0, 0.030, 0.40),
    ("meta_ads", "promo_seasonal", 140.0, 0.018, 0.48),
    ("google_ads", "search_generic", 220.0, 0.045, 0.85),
    ("google_ads", "search_brand", 70.0, 0.120, 0.25),
    ("google_ads", "shopping", 160.0, 0.025, 0.60),
]


def build_ad_spend(rng: np.random.Generator) -> pd.DataFrame:
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    rows = []

    for platform, campaign, base_spend, ctr, cpc in CAMPAIGNS:
        # weekly seasonality: slightly higher spend on weekdays
        weekday_factor = np.where(dates.dayofweek < 5, 1.1, 0.8)
        # growth trend over the period (business scaling up)
        trend = np.linspace(0.8, 1.4, len(dates))
        # November (Black Friday) boost
        seasonal = np.where(dates.month == 11, 1.6, 1.0)
        noise = rng.normal(1.0, 0.12, len(dates)).clip(0.5, None)

        spend = base_spend * weekday_factor * trend * seasonal * noise
        cpc_daily = (cpc * rng.normal(1.0, 0.08, len(dates))).clip(0.05, None)
        clicks = (spend / cpc_daily).round().astype(int)
        impressions = (clicks / (ctr * rng.normal(1.0, 0.10, len(dates)).clip(0.3, None))).round().astype(int)

        rows.append(
            pd.DataFrame(
                {
                    "date": dates.strftime("%Y-%m-%d"),
                    "platform": platform,
                    "campaign_name": campaign,
                    "spend_brl": spend.round(2),
                    "impressions": impressions,
                    "clicks": clicks,
                }
            )
        )

    df = pd.concat(rows, ignore_index=True)
    df.insert(0, "ad_record_id", [f"ad_{i:06d}" for i in range(len(df))])
    return df


def inject_issues(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Add controlled data-quality problems so dbt tests and n8n alerts have something to catch."""
    df = df.copy()
    # 1. null spend values
    null_idx = rng.choice(df.index, size=15, replace=False)
    df.loc[null_idx, "spend_brl"] = None
    # 2. negative spend values
    neg_idx = rng.choice(df.index, size=5, replace=False)
    df.loc[neg_idx, "spend_brl"] = -df.loc[neg_idx, "spend_brl"].abs()
    # 3. duplicated records
    dupes = df.sample(10, random_state=SEED)
    return pd.concat([df, dupes], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inject-issues", action="store_true", help="add duplicates, nulls and negatives")
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)
    df = build_ad_spend(rng)
    if args.inject_issues:
        df = inject_issues(df, rng)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = json.loads(df.to_json(orient="records"))
    OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")

    print(f"Wrote {len(df):,} rows to {OUTPUT_PATH}")
    print(df.groupby("platform")["spend_brl"].sum().round(2))


if __name__ == "__main__":
    main()
