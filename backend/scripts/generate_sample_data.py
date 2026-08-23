"""Regenerate the demo CSVs in backend/sample_data.

Produces 24 months of retail history with a known structure so the analytics can
be judged against ground truth: a mild upward trend, an Indian festive-season
peak in October/November, a weekend uplift, one product in decline, one
accelerating, cost growth outpacing revenue growth, dormant high-value customers
and a delivery-delay complaint theme.

Run from the backend directory:
    .venv\\Scripts\\python.exe scripts\\generate_sample_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parents[1] / "sample_data"

START = pd.Timestamp("2024-08-01")
END = pd.Timestamp("2026-07-31")

# name -> (units/day baseline, unit price)
PRODUCTS = {
    "Basmati Rice 5kg": (6.0, 520),
    "Sunflower Oil 1L": (14.0, 185),
    "Tea Powder 500g": (10.0, 240),
    "Wheat Flour 10kg": (5.0, 430),
    "Toor Dal 1kg": (12.0, 160),
    "Detergent Powder 2kg": (7.0, 310),
    "Milk Powder 500g": (6.0, 275),
    "Spice Mix Pack": (15.0, 95),
}

# Festive season lifts October and November; February is the annual low.
MONTH_FACTOR = {
    1: 0.88, 2: 0.80, 3: 0.90, 4: 0.98, 5: 1.05, 6: 0.95,
    7: 0.92, 8: 1.02, 9: 1.10, 10: 1.35, 11: 1.28, 12: 1.15,
}
WEEKDAY_FACTOR = {0: 0.95, 1: 0.92, 2: 0.96, 3: 1.00, 4: 1.08, 5: 1.25, 6: 1.15}

REGIONS = ["North", "South", "East", "West"]
SELL_PROBABILITY = 0.6

rng = np.random.default_rng(20240801)


def _customers() -> list[str]:
    return [f"CUST{i:03d}" for i in range(1, 61)]


def build_sales(customers: list[str]) -> pd.DataFrame:
    days = pd.date_range(START, END, freq="D")
    total_days = len(days)
    # Customers 50-59 go quiet in the final quarter to create a win-back list.
    dormant = set(customers[50:])
    dormant_cutoff = END - pd.Timedelta(days=100)

    rows = []
    order_number = 10000
    for day_index, day in enumerate(days):
        trend = 1.012 ** (day_index / 30.0)
        seasonal = MONTH_FACTOR[day.month]
        weekly = WEEKDAY_FACTOR[day.dayofweek]
        days_left = total_days - day_index

        for product, (base_units, price) in PRODUCTS.items():
            if rng.random() > SELL_PROBABILITY:
                continue

            lifecycle = 1.0
            if product == "Detergent Powder 2kg" and days_left < 75:
                # Losing share to a competitor over the last ~2.5 months.
                lifecycle = 0.45 + 0.55 * (days_left / 75.0)
            elif product == "Milk Powder 500g" and days_left < 90:
                lifecycle = 1.0 + 0.6 * (1 - days_left / 90.0)

            expected = base_units / SELL_PROBABILITY * trend * seasonal * weekly * lifecycle
            units = int(max(1, rng.normal(expected, expected * 0.22)))

            pool = [c for c in customers if not (c in dormant and day > dormant_cutoff)]
            order_number += 1
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Product": product,
                    "Quantity": units,
                    "Price": price,
                    "Customer": str(rng.choice(pool)),
                    "Region": str(rng.choice(REGIONS)),
                    "Order ID": f"ORD{order_number}",
                }
            )

    return pd.DataFrame(rows)


def build_expenses(sales: pd.DataFrame) -> pd.DataFrame:
    revenue_by_month = (
        sales.assign(
            revenue=sales["Quantity"] * sales["Price"],
            period=pd.to_datetime(sales["Date"]).dt.to_period("M"),
        )
        .groupby("period")["revenue"]
        .sum()
        .sort_index()
    )

    rows = []
    for month_index, (period, revenue) in enumerate(revenue_by_month.items()):
        month_start = period.to_timestamp()
        revenue = float(revenue)
        # Supplier prices creep up over the final 8 months without a matching price rise,
        # which is what puts the margin under pressure.
        months_from_end = len(revenue_by_month) - month_index - 1
        cogs_ratio = 0.66 + (0.06 * (1 - months_from_end / 8.0) if months_from_end < 8 else 0.0)
        overhead_drift = 1.0 + 0.015 * month_index

        monthly = [
            ("Purchases", revenue * cogs_ratio, "Stock purchased from suppliers"),
            ("Rent", 45000, "Monthly shop rent"),
            ("Salaries", 55000 * (1.008**month_index), "Staff salaries"),
            ("Utilities", 12000 * overhead_drift, "Electricity and water"),
            ("Packaging", revenue * 0.008, "Packaging material"),
        ]
        for category, amount, description in monthly:
            rows.append(
                {
                    "Date": month_start.strftime("%Y-%m-%d"),
                    "Expense Category": category,
                    "Amount": round(float(amount), 2),
                    "Description": description,
                }
            )

        for week in range(4):
            day = month_start + pd.Timedelta(days=week * 7 + 3)
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Expense Category": "Marketing",
                    "Amount": round(float(rng.normal(3000, 400) * overhead_drift), 2),
                    "Description": "Local ads and promotions",
                }
            )
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Expense Category": "Logistics",
                    "Amount": round(float(revenue * 0.02 / 4 * overhead_drift), 2),
                    "Description": "Delivery and transport",
                }
            )

    return pd.DataFrame(rows)


def build_inventory(sales: pd.DataFrame) -> pd.DataFrame:
    recent = sales[pd.to_datetime(sales["Date"]) > END - pd.Timedelta(days=60)]
    per_day = recent.groupby("Product")["Quantity"].sum() / 60.0

    # Deliberate mix: two lines short of cover, one heavily overstocked, rest healthy.
    cover_days = {
        "Basmati Rice 5kg": 8,
        "Wheat Flour 10kg": 16,
        "Tea Powder 500g": 175,
        "Sunflower Oil 1L": 50,
        "Toor Dal 1kg": 45,
        "Detergent Powder 2kg": 70,
        "Milk Powder 500g": 30,
        "Spice Mix Pack": 55,
    }
    suppliers = {
        "Basmati Rice 5kg": "Agro Traders Pvt Ltd",
        "Sunflower Oil 1L": "Golden Oil Mills",
        "Tea Powder 500g": "Nilgiri Tea Estate",
        "Wheat Flour 10kg": "Shree Flour Mills",
        "Toor Dal 1kg": "Deccan Pulses",
        "Detergent Powder 2kg": "CleanCo Distributors",
        "Milk Powder 500g": "Dairy Fresh Supply",
        "Spice Mix Pack": "Masala House",
    }

    rows = []
    for product, (_, price) in PRODUCTS.items():
        daily = float(per_day.get(product, 1.0))
        stock = int(round(daily * cover_days[product]))
        rows.append(
            {
                "Product": product,
                "Current Stock": stock,
                "Reorder Level": int(round(daily * 21)),
                "Supplier": suppliers[product],
                "Stock Value": round(stock * price * 0.72, 2),
            }
        )
    return pd.DataFrame(rows)


def build_customers(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.assign(
        revenue=sales["Quantity"] * sales["Price"], date=pd.to_datetime(sales["Date"])
    )
    grouped = df.groupby("Customer").agg(
        purchase_frequency=("revenue", "count"),
        total_spending=("revenue", "sum"),
        last_purchase=("date", "max"),
    )
    return pd.DataFrame(
        {
            "Customer ID": grouped.index,
            "Purchase Frequency": grouped["purchase_frequency"].values,
            "Total Spending": grouped["total_spending"].round(2).values,
            "Last Purchase Date": grouped["last_purchase"].dt.strftime("%Y-%m-%d").values,
        }
    )


def build_reviews(customers: list[str]) -> pd.DataFrame:
    positive = [
        "Great quality rice, will buy again",
        "Fast delivery and fresh stock",
        "Excellent prices compared to the market",
        "Very happy with the packaging",
        "Friendly staff and good service",
        "Perfect, exactly what I ordered",
    ]
    neutral = [
        "Product is okay for the price",
        "Average experience, nothing special",
        "Decent but the range could be wider",
    ]
    negative = [
        "Delivery was late again this month",
        "Very slow shipping, waited five days",
        "Support was rude when I asked about the delay",
        "Order arrived late and one item was damaged",
        "Delivery delay every single time, please fix it",
        "Late delivery and no update from the team",
    ]

    rows = []
    days = pd.date_range(START, END, freq="D")
    for _ in range(80):
        draw = rng.random()
        if draw < 0.55:
            rating, text = int(rng.integers(4, 6)), str(rng.choice(positive))
        elif draw < 0.72:
            rating, text = 3, str(rng.choice(neutral))
        else:
            rating, text = int(rng.integers(1, 3)), str(rng.choice(negative))
        rows.append(
            {
                "Customer": str(rng.choice(customers)),
                "Rating": rating,
                "Review Text": text,
                "Date": pd.Timestamp(rng.choice(days)).strftime("%Y-%m-%d"),
            }
        )
    return pd.DataFrame(rows).sort_values("Date")


def main() -> None:
    customers = _customers()
    sales = build_sales(customers)
    expenses = build_expenses(sales)
    inventory = build_inventory(sales)
    customer_table = build_customers(sales)
    reviews = build_reviews(customers)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in (
        ("sales", sales),
        ("expenses", expenses),
        ("inventory", inventory),
        ("customers", customer_table),
        ("reviews", reviews),
    ):
        path = OUT_DIR / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        print(f"{path.name:<16} {len(frame):>6} rows")

    revenue = float((sales["Quantity"] * sales["Price"]).sum())
    cost = float(expenses["Amount"].sum())
    print(
        f"\nRevenue {revenue:,.0f} | Expenses {cost:,.0f} | "
        f"Margin {(revenue - cost) / revenue * 100:.1f}% | "
        f"Months {pd.to_datetime(sales['Date']).dt.to_period('M').nunique()}"
    )


if __name__ == "__main__":
    main()
