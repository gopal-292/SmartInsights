"""Smoke-check the forecasting, pattern and advisor engines on synthetic data.

Run from the backend directory:  .venv\\Scripts\\python.exe scripts\\check_ml.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Windows consoles default to cp1252, which cannot render the rupee sign.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services.advisor import generate_action_plan  # noqa: E402
from app.services.forecasting import build_forecast  # noqa: E402
from app.services.patterns import detect_patterns  # noqa: E402
from app.services.preprocessing import (  # noqa: E402
    detect_data_type,
    preprocess_dataframe,
    read_csv_robust,
)

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"

PRODUCTS = ["Basmati Rice", "Sunflower Oil", "Tea Powder", "Wheat Flour"]


def synthetic_frames(months: int = 30, seed: int = 7) -> dict[str, pd.DataFrame]:
    """Trend + annual seasonality + weekly effect + noise, so patterns are known up front."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-01")
    days = pd.date_range(start, periods=months * 30, freq="D")

    rows = []
    for i, day in enumerate(days):
        trend = 1.0 + 0.0025 * i
        seasonal = 1.0 + 0.30 * np.sin(2 * np.pi * (day.month - 3) / 12)
        weekly = 1.25 if day.dayofweek >= 5 else 1.0
        for product_index, product in enumerate(PRODUCTS):
            # Give one product a deliberate late-period decline.
            drift = 0.55 if (product == "Tea Powder" and i > len(days) - 90) else 1.0
            base = (40 + product_index * 15) * trend * seasonal * weekly * drift
            quantity = max(1, int(rng.normal(base / 20, 2)))
            rows.append(
                {
                    "date": day,
                    "product": product,
                    "quantity": quantity,
                    "price": 60 + product_index * 25,
                    "customer": f"C{rng.integers(1, 40)}",
                    "region": rng.choice(["North", "South", "East"]),
                }
            )

    sales = pd.DataFrame(rows)
    sales["revenue"] = sales["quantity"] * sales["price"]

    expenses = pd.DataFrame(
        {
            "date": days[::7],
            "category": rng.choice(["Rent", "Salaries", "Marketing", "Logistics"], size=len(days[::7])),
            # Costs deliberately grow faster than revenue.
            "amount": rng.normal(9000, 1200, size=len(days[::7])) * (1 + 0.004 * np.arange(len(days[::7]))),
        }
    )

    inventory = pd.DataFrame(
        {
            "product": PRODUCTS,
            "current_stock": [40, 900, 1500, 260],
            "reorder_level": [100, 120, 150, 100],
            "supplier": ["Agro Traders", "Oil Mills", "Tea Estate", "Flour Co"],
            "stock_value": [4000, 90000, 165000, 33800],
        }
    )

    reviews = pd.DataFrame(
        {
            "rating": [5, 4, 2, 1, 5, 3, 2, 4, 1, 5, 2, 4],
            "review_text": [
                "great quality", "fast delivery", "delivery was late again",
                "very late shipping and rude support", "love it", "okay",
                "delayed delivery", "good price", "worst delay ever",
                "excellent", "shipping delay", "happy",
            ],
        }
    )

    return {"sales": sales, "expenses": expenses, "inventory": inventory, "reviews": reviews}


def sample_frames() -> dict[str, pd.DataFrame]:
    """Load backend/sample_data through the same pipeline an upload goes through."""
    frames: dict[str, pd.DataFrame] = {}
    for path in sorted(SAMPLE_DIR.glob("*.csv")):
        raw = read_csv_robust(path)
        data_type = detect_data_type(raw, path.name)
        processed, _ = preprocess_dataframe(raw, data_type)
        frames[data_type] = processed
    return frames


def main() -> None:
    use_sample = "--sample" in sys.argv
    frames = sample_frames() if use_sample else synthetic_frames()
    print(f"source: {'sample_data CSVs' if use_sample else 'synthetic series'}\n")

    forecast = build_forecast(frames["sales"], periods=6)
    print("=== FORECAST ===")
    print("selected:", forecast["selected_model"], "| confidence:", forecast["confidence"])
    print("accuracy:", json.dumps(forecast["accuracy"], indent=2))
    print("\nmodel leaderboard (lower MAE is better):")
    for row in forecast["evaluation"]:
        print(
            f"  {row['model']:<42} MAE {row['mae']:>12,.0f}  MAPE {row['mape']}%  "
            f"skill {row['skill_vs_naive']}  dir {row['direction_accuracy']}%"
        )
    print("\npredictions:")
    for row in forecast["predictions"]:
        print(
            f"  {row['period']}  {row['predicted_revenue']:>12,.0f}  "
            f"[{row['lower_bound']:,.0f} .. {row['upper_bound']:,.0f}]  "
            f"{row['change_vs_recent_avg']:+.1f}% vs recent"
        )

    patterns = detect_patterns(frames)
    print("\n=== PATTERNS ===")
    for line in patterns["headlines"]:
        print(" -", line)

    plan = generate_action_plan(frames)
    print("\n=== MARKET CONTEXT ===")
    print(plan["market_context"]["summary"])
    print("\n=== ACTIONS ===")
    for item in plan["recommendations"]:
        print(f"\n[{item['priority'].upper()}] {item['area']} ({item['timeframe']})")
        print("  situation:", item["situation"])
        print("  action   :", item["action"])
        print("  impact   :", item["expected_impact"])

    # Fail loudly if anything is not JSON-serialisable for the API layer.
    json.dumps({"forecast": forecast, "patterns": patterns, "plan": plan})
    print("\nAll payloads are JSON-serialisable.")


if __name__ == "__main__":
    main()
