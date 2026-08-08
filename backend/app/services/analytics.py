from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _safe_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _monthly_series(df: pd.DataFrame, value_col: str, date_col: str = "date") -> list[dict]:
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return []
    tmp = df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    if tmp.empty:
        return []
    grouped = tmp.groupby(tmp[date_col].dt.to_period("M"))[value_col].sum().sort_index()
    return [{"period": str(idx), "value": _safe_float(val)} for idx, val in grouped.items()]


def dashboard_kpis(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    sales = frames.get("sales", pd.DataFrame())
    expenses = frames.get("expenses", pd.DataFrame())
    inventory = frames.get("inventory", pd.DataFrame())
    reviews = frames.get("reviews", pd.DataFrame())

    revenue = _safe_float(sales["revenue"].sum()) if "revenue" in sales.columns else 0.0
    if revenue == 0 and {"quantity", "price"}.issubset(sales.columns):
        revenue = _safe_float((sales["quantity"] * sales["price"]).sum())

    total_expenses = _safe_float(expenses["amount"].sum()) if "amount" in expenses.columns else 0.0
    net_profit = revenue - total_expenses
    margin = (net_profit / revenue * 100) if revenue else 0.0
    orders = int(len(sales)) if not sales.empty else 0
    aov = revenue / orders if orders else 0.0
    customers = (
        int(sales["customer"].nunique())
        if "customer" in sales.columns
        else int(sales["customer_id"].nunique())
        if "customer_id" in sales.columns
        else 0
    )
    inventory_value = (
        _safe_float(inventory["stock_value"].sum())
        if "stock_value" in inventory.columns
        else 0.0
    )
    satisfaction = (
        _safe_float(reviews["rating"].mean()) if "rating" in reviews.columns and not reviews.empty else 0.0
    )

    # Growth: last month vs previous month
    growth = 0.0
    trend = _monthly_series(sales, "revenue")
    if len(trend) >= 2 and trend[-2]["value"]:
        growth = ((trend[-1]["value"] - trend[-2]["value"]) / trend[-2]["value"]) * 100

    return {
        "total_revenue": round(revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin": round(margin, 2),
        "total_orders": orders,
        "average_order_value": round(aov, 2),
        "total_customers": customers,
        "inventory_value": round(inventory_value, 2),
        "sales_growth": round(growth, 2),
        "customer_satisfaction": round(satisfaction, 2),
    }


def sales_analytics(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    sales = frames.get("sales", pd.DataFrame())
    if sales.empty:
        return {"message": "No sales data uploaded yet.", "monthly": [], "by_product": [], "by_region": []}

    if "revenue" not in sales.columns and {"quantity", "price"}.issubset(sales.columns):
        sales = sales.copy()
        sales["revenue"] = sales["quantity"] * sales["price"]

    by_product = []
    if "product" in sales.columns:
        grouped = (
            sales.groupby("product")
            .agg(revenue=("revenue", "sum"), units=("quantity", "sum") if "quantity" in sales.columns else ("revenue", "count"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        by_product = [
            {
                "product": row["product"],
                "revenue": round(_safe_float(row["revenue"]), 2),
                "units": int(row["units"]) if not pd.isna(row["units"]) else 0,
            }
            for _, row in grouped.head(10).iterrows()
        ]

    by_region = []
    if "region" in sales.columns:
        grouped = sales.groupby("region")["revenue"].sum().sort_values(ascending=False)
        by_region = [{"region": k, "revenue": round(_safe_float(v), 2)} for k, v in grouped.items()]

    return {
        "monthly": _monthly_series(sales, "revenue"),
        "by_product": by_product,
        "by_region": by_region,
        "top_product": by_product[0] if by_product else None,
        "low_products": list(reversed(by_product[-3:])) if len(by_product) >= 3 else [],
    }


def expense_analytics(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    expenses = frames.get("expenses", pd.DataFrame())
    if expenses.empty or "amount" not in expenses.columns:
        return {"message": "No expense data uploaded yet.", "monthly": [], "by_category": []}

    by_category = []
    if "category" in expenses.columns:
        grouped = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
        by_category = [
            {"category": k, "amount": round(_safe_float(v), 2)} for k, v in grouped.items()
        ]

    monthly = _monthly_series(expenses, "amount")
    growth = 0.0
    if len(monthly) >= 2 and monthly[-2]["value"]:
        growth = ((monthly[-1]["value"] - monthly[-2]["value"]) / monthly[-2]["value"]) * 100

    return {
        "total_expenses": round(_safe_float(expenses["amount"].sum()), 2),
        "by_category": by_category,
        "monthly": monthly,
        "expense_growth": round(growth, 2),
        "highest_category": by_category[0] if by_category else None,
    }


def profitability_analytics(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    kpis = dashboard_kpis(frames)
    sales = frames.get("sales", pd.DataFrame())
    expenses = frames.get("expenses", pd.DataFrame())
    rev_monthly = {x["period"]: x["value"] for x in _monthly_series(sales, "revenue")}
    exp_monthly = {x["period"]: x["value"] for x in _monthly_series(expenses, "amount")}
    periods = sorted(set(rev_monthly) | set(exp_monthly))
    monthly = []
    for p in periods:
        r = rev_monthly.get(p, 0.0)
        e = exp_monthly.get(p, 0.0)
        profit = r - e
        monthly.append(
            {
                "period": p,
                "revenue": round(r, 2),
                "expenses": round(e, 2),
                "profit": round(profit, 2),
                "margin": round((profit / r * 100) if r else 0.0, 2),
            }
        )
    return {
        "net_profit": kpis["net_profit"],
        "profit_margin": kpis["profit_margin"],
        "monthly": monthly,
    }


def inventory_analytics(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    inventory = frames.get("inventory", pd.DataFrame())
    if inventory.empty:
        return {"message": "No inventory data uploaded yet.", "items": [], "reorder_required": []}

    items = inventory.copy()
    if {"current_stock", "reorder_level"}.issubset(items.columns) and "status" not in items.columns:
        items["status"] = np.where(
            items["current_stock"] <= items["reorder_level"], "Reorder Required", "OK"
        )

    records = []
    for _, row in items.iterrows():
        records.append(
            {
                "product": row.get("product", "Unknown"),
                "current_stock": int(_safe_float(row.get("current_stock", 0))),
                "reorder_level": int(_safe_float(row.get("reorder_level", 0))),
                "supplier": row.get("supplier", ""),
                "stock_value": round(_safe_float(row.get("stock_value", 0)), 2),
                "status": row.get("status", "OK"),
            }
        )
    reorder = [r for r in records if r["status"] == "Reorder Required"]
    overstocked = [
        r
        for r in records
        if r["reorder_level"] > 0 and r["current_stock"] > r["reorder_level"] * 3
    ]
    return {
        "items": records,
        "reorder_required": reorder,
        "overstocked": overstocked,
        "total_stock_value": round(sum(r["stock_value"] for r in records), 2),
    }
