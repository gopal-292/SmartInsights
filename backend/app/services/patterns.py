"""Pattern discovery over historical business data.

Turns raw sales/expense rows into the structural signals a forecast cannot express
on its own: trend strength, seasonality, momentum shifts, product rotation,
concentration risk and margin pressure.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from app.services.forecasting import monthly_revenue_series

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _with_revenue(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "revenue" not in out.columns and {"quantity", "price"}.issubset(out.columns):
        out["revenue"] = out["quantity"] * out["price"]
    return out


def _dated_sales(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sales = _with_revenue(frames.get("sales", pd.DataFrame()))
    if sales.empty or "date" not in sales.columns or "revenue" not in sales.columns:
        return pd.DataFrame()
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    return sales.dropna(subset=["date"])


def _pct(new: float, old: float) -> float | None:
    if old is None or abs(old) < 1e-9:
        return None
    return round((new - old) / abs(old) * 100, 1)


def _trend(series: pd.Series) -> dict[str, Any]:
    """Fit a linear trend and express the slope as a percentage of average revenue."""
    y = np.asarray(series.values, dtype=float)
    t = np.arange(len(y), dtype=float).reshape(-1, 1)
    model = Ridge(alpha=1.0).fit(t, y)
    slope = float(model.coef_[0])
    average = float(np.mean(y)) or 1.0
    slope_pct = slope / average * 100

    predicted = model.predict(t)
    total_variance = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = (
        round(1 - float(np.sum((y - predicted) ** 2)) / total_variance, 3)
        if total_variance > 1e-9
        else None
    )

    if slope_pct > 0.75:
        direction = "growing"
    elif slope_pct < -0.75:
        direction = "declining"
    else:
        direction = "stable"

    summary = (
        f"Revenue is broadly stable, drifting {slope_pct:+.1f}% per month "
        f"({'+' if slope >= 0 else '-'}₹{abs(slope):,.0f}/month)."
        if direction == "stable"
        else (
            f"Revenue is {direction} at about {abs(slope_pct):.1f}% per month "
            f"({'+' if slope >= 0 else '-'}₹{abs(slope):,.0f}/month)."
        )
    )

    return {
        "direction": direction,
        "monthly_change_pct": round(slope_pct, 1),
        "monthly_change_value": round(slope, 2),
        "fit_r2": r_squared,
        "summary": summary,
    }


def _momentum(series: pd.Series, adjusted: pd.Series) -> dict[str, Any]:
    """Growth rates come from the adjusted series; reported levels stay in real rupees."""
    raw = np.asarray(series.values, dtype=float)
    y = np.asarray(adjusted.values, dtype=float)
    window = 3 if len(y) >= 6 else max(1, len(y) // 2)
    recent = float(np.mean(raw[-window:]))
    prior = float(np.mean(raw[-2 * window : -window])) if len(raw) >= 2 * window else None
    change = (
        _pct(float(np.mean(y[-window:])), float(np.mean(y[-2 * window : -window])))
        if len(y) >= 2 * window
        else None
    )

    # Comparing adjacent windows confuses seasonality with growth, so prefer the same
    # months one year earlier whenever there is enough history.
    yoy_change = None
    if len(raw) >= 12 + window:
        yoy_change = _pct(float(np.mean(raw[-window:])), float(np.mean(raw[-(12 + window) : -12])))
    basis_change = yoy_change if yoy_change is not None else change

    streak, streak_direction = 0, "flat"
    if len(y) >= 2:
        deltas = np.diff(y)
        sign = np.sign(deltas[-1])
        if sign != 0:
            streak_direction = "up" if sign > 0 else "down"
            for delta in deltas[::-1]:
                if np.sign(delta) == sign:
                    streak += 1
                else:
                    break

    return {
        "window_months": window,
        "recent_avg": round(recent, 2),
        "previous_avg": round(prior, 2) if prior is not None else None,
        "change_pct": change,
        "yoy_change_pct": yoy_change,
        "basis": "year-over-year" if yoy_change is not None else "consecutive windows",
        "streak_months": streak,
        "streak_direction": streak_direction,
        "state": (
            "accelerating" if basis_change is not None and basis_change > 5
            else "slowing" if basis_change is not None and basis_change < -5
            else "steady"
        ),
    }


def _volatility(series: pd.Series) -> dict[str, Any]:
    y = np.asarray(series.values, dtype=float)
    mean = float(np.mean(y)) or 1.0
    cv = float(np.std(y)) / mean * 100
    return {
        "coefficient_of_variation": round(cv, 1),
        "level": "high" if cv > 40 else "moderate" if cv > 18 else "low",
        "best_month": {
            "period": str(series.idxmax()),
            "revenue": round(float(series.max()), 2),
        },
        "worst_month": {
            "period": str(series.idxmin()),
            "revenue": round(float(series.min()), 2),
        },
    }


def _seasonal_index(series: pd.Series) -> pd.Series | None:
    """Calendar-month index where 1.0 is an average month.

    With two or more years, use classical ratio-to-moving-average decomposition so the
    trend is removed before the seasonal shape is measured. Below that, fall back to a
    ratio against the overall mean, which is cruder but still informative.
    """
    if len(series) < 12:
        return None

    months = pd.Series([p.month for p in series.index], index=series.index)
    values = pd.Series(series.values, index=series.index, dtype=float)

    if len(series) >= 36:
        # A 2x12 centred moving average follows a curved trend, but it discards a year of
        # data, so it only pays off once there are three or more years.
        trend = values.rolling(12, center=True).mean().rolling(2).mean().shift(-1)
    else:
        # Straight-line detrending keeps every observation, which matters at 12-35 months
        # where a moving average would leave roughly one sample per calendar month.
        t = np.arange(len(values), dtype=float).reshape(-1, 1)
        fitted = Ridge(alpha=1.0).fit(t, values.values).predict(t)
        trend = pd.Series(fitted, index=values.index)

    ratio = (values / trend.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).dropna()
    if len(ratio) < 12:
        return None

    index = ratio.groupby(months.loc[ratio.index]).mean()
    index = index / (float(index.mean()) or 1.0)
    return index.reindex(range(1, 13)).interpolate().bfill().ffill().round(3)


def _deseasonalize(series: pd.Series, index: pd.Series | None) -> pd.Series:
    if index is None:
        return series
    factors = np.array([float(index.get(p.month, 1.0)) or 1.0 for p in series.index])
    return pd.Series(series.values / factors, index=series.index)


def _seasonality(series: pd.Series, index: pd.Series | None) -> dict[str, Any]:
    if index is None:
        return {
            "detected": False,
            "message": f"Needs 12+ months to separate seasonality from trend (have {len(series)}).",
        }

    strength = float(index.std()) * 100

    peak_month, low_month = int(index.idxmax()), int(index.idxmin())
    return {
        "detected": strength >= 10,
        "strength_pct": round(strength, 1),
        "method": (
            "ratio to 2x12 moving average" if len(series) >= 36 else "ratio to linear trend"
        ),
        "peak_month": MONTH_NAMES[peak_month - 1],
        "peak_index": float(index.max()),
        "low_month": MONTH_NAMES[low_month - 1],
        "low_index": float(index.min()),
        "monthly_index": {MONTH_NAMES[m - 1]: float(v) for m, v in index.items()},
        "summary": (
            f"{MONTH_NAMES[peak_month - 1]} runs {(index.max() - 1) * 100:+.0f}% versus an average "
            f"month and {MONTH_NAMES[low_month - 1]} runs {(index.min() - 1) * 100:+.0f}%."
        ),
    }


def _weekday_pattern(sales: pd.DataFrame) -> dict[str, Any]:
    daily = sales.groupby(sales["date"].dt.dayofweek)["revenue"].mean()
    if len(daily) < 5:
        return {"detected": False}
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    overall = float(daily.mean()) or 1.0
    best, worst = int(daily.idxmax()), int(daily.idxmin())
    spread = (float(daily.max()) - float(daily.min())) / overall * 100
    return {
        "detected": spread >= 20,
        "best_day": names[best],
        "worst_day": names[worst],
        "spread_pct": round(spread, 1),
        "average_by_day": {names[int(d)]: round(float(v), 2) for d, v in daily.items()},
    }


def _product_momentum(sales: pd.DataFrame) -> dict[str, Any]:
    if "product" not in sales.columns:
        return {"available": False}

    latest = sales["date"].max()
    span_days = max((latest - sales["date"].min()).days, 1)
    window = 30 if span_days >= 90 else max(7, span_days // 3)

    recent_cut = latest - pd.Timedelta(days=window)
    prior_cut = latest - pd.Timedelta(days=2 * window)

    recent = sales[sales["date"] > recent_cut].groupby("product")["revenue"].sum()
    prior = sales[(sales["date"] > prior_cut) & (sales["date"] <= recent_cut)].groupby("product")["revenue"].sum()
    if recent.empty or prior.empty:
        return {"available": False}

    combined = pd.concat([recent.rename("recent"), prior.rename("prior")], axis=1).fillna(0.0)
    combined["delta"] = combined["recent"] - combined["prior"]
    combined["change_pct"] = combined.apply(
        lambda r: _pct(r["recent"], r["prior"]) if r["prior"] > 0 else None, axis=1
    )

    def rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
        return [
            {
                "product": str(name),
                "recent_revenue": round(float(row["recent"]), 2),
                "previous_revenue": round(float(row["prior"]), 2),
                "delta": round(float(row["delta"]), 2),
                "change_pct": row["change_pct"],
            }
            for name, row in frame.iterrows()
        ]

    rising = combined[combined["delta"] > 0].sort_values("delta", ascending=False).head(5)
    declining = combined[combined["delta"] < 0].sort_values("delta").head(5)

    return {
        "available": True,
        "window_days": window,
        "rising": rows(rising),
        "declining": rows(declining),
    }


def _concentration(sales: pd.DataFrame) -> dict[str, Any]:
    total = float(sales["revenue"].sum()) or 1.0
    result: dict[str, Any] = {}

    for column, key in (("product", "product"), ("customer", "customer"), ("region", "region")):
        source = column if column in sales.columns else f"{column}_id"
        if source not in sales.columns:
            continue
        grouped = sales.groupby(source)["revenue"].sum().sort_values(ascending=False)
        top_share = float(grouped.iloc[0]) / total * 100
        top3_share = float(grouped.head(3).sum()) / total * 100
        result[key] = {
            "top_name": str(grouped.index[0]),
            "top_share_pct": round(top_share, 1),
            "top3_share_pct": round(top3_share, 1),
            "distinct_count": int(len(grouped)),
            "risk": "high" if top_share > 40 else "moderate" if top_share > 25 else "low",
        }

    return result


def _margin_pressure(frames: dict[str, pd.DataFrame], revenue: pd.Series) -> dict[str, Any]:
    expenses = frames.get("expenses", pd.DataFrame())
    if expenses.empty or "amount" not in expenses.columns or "date" not in expenses.columns:
        return {"available": False}

    exp = expenses.copy()
    exp["date"] = pd.to_datetime(exp["date"], errors="coerce")
    exp = exp.dropna(subset=["date"])
    if exp.empty:
        return {"available": False}

    monthly_exp = exp.groupby(exp["date"].dt.to_period("M"))["amount"].sum().sort_index().astype(float)
    shared = revenue.index.intersection(monthly_exp.index)
    if len(shared) < 2:
        return {"available": False}

    rev, cost = revenue.loc[shared], monthly_exp.loc[shared]
    window = min(3, len(shared) // 2) or 1

    if len(shared) >= 12 + window:
        # Same months a year earlier, so a seasonal trough is not mistaken for cost blowout.
        basis = "year-over-year"
        rev_growth = _pct(float(rev[-window:].mean()), float(rev[-(12 + window) : -12].mean()))
        cost_growth = _pct(float(cost[-window:].mean()), float(cost[-(12 + window) : -12].mean()))
    else:
        basis = "consecutive windows"
        baseline_rev = float(rev[:-window].mean()) if len(rev) > window else float(rev.mean())
        baseline_cost = float(cost[:-window].mean()) if len(cost) > window else float(cost.mean())
        rev_growth = _pct(float(rev[-window:].mean()), baseline_rev)
        cost_growth = _pct(float(cost[-window:].mean()), baseline_cost)

    margins = ((rev - cost) / rev.replace(0, np.nan) * 100).dropna()
    margin_trend = None
    if len(margins) >= 3:
        margin_trend = round(float(margins.iloc[-1] - margins.iloc[0]), 1)

    squeeze = (
        rev_growth is not None
        and cost_growth is not None
        and cost_growth > rev_growth + 5
    )

    top_categories = []
    if "category" in exp.columns:
        recent_period = monthly_exp.index[-1]
        recent = exp[exp["date"].dt.to_period("M") == recent_period]
        grouped = recent.groupby("category")["amount"].sum().sort_values(ascending=False).head(5)
        total_recent = float(grouped.sum()) or 1.0
        top_categories = [
            {
                "category": str(name),
                "amount": round(float(value), 2),
                "share_pct": round(float(value) / total_recent * 100, 1),
            }
            for name, value in grouped.items()
        ]

    return {
        "available": True,
        "basis": basis,
        "comparison_months": window,
        "revenue_growth_pct": rev_growth,
        "expense_growth_pct": cost_growth,
        "current_margin_pct": round(float(margins.iloc[-1]), 1) if len(margins) else None,
        "margin_change_pts": margin_trend,
        "squeeze": bool(squeeze),
        "top_expense_categories": top_categories,
    }


def _repeat_behaviour(sales: pd.DataFrame) -> dict[str, Any]:
    column = "customer" if "customer" in sales.columns else "customer_id"
    if column not in sales.columns:
        return {"available": False}

    orders = sales.groupby(column).agg(orders=("revenue", "count"), spend=("revenue", "sum"), last=("date", "max"))
    repeat_rate = float((orders["orders"] > 1).mean()) * 100
    latest = sales["date"].max()
    dormant_cut = 60
    dormant = orders[(latest - orders["last"]).dt.days > dormant_cut]
    high_value_threshold = float(orders["spend"].quantile(0.75))
    dormant_valuable = dormant[dormant["spend"] >= high_value_threshold]

    return {
        "available": True,
        "customers": int(len(orders)),
        "repeat_rate_pct": round(repeat_rate, 1),
        "avg_order_value": round(float(sales["revenue"].mean()), 2),
        "dormant_days": dormant_cut,
        "dormant_customers": int(len(dormant)),
        "at_risk_valuable_customers": int(len(dormant_valuable)),
        "revenue_at_risk": round(float(dormant_valuable["spend"].sum()), 2),
    }


def detect_patterns(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Full pattern report for the current dataset."""
    sales = _dated_sales(frames)
    if sales.empty:
        return {
            "available": False,
            "message": "Upload dated sales data (with revenue, or quantity and price) to detect patterns.",
        }

    series = monthly_revenue_series(sales)
    if len(series) < 2:
        return {
            "available": False,
            "message": "At least 2 months of sales history are required to detect patterns.",
        }

    # Trend and momentum are measured on the seasonally adjusted series; otherwise a
    # festive peak or a quiet month gets misreported as growth or decline.
    index = _seasonal_index(series)
    adjusted = _deseasonalize(series, index)

    report: dict[str, Any] = {
        "available": True,
        "months_of_history": int(len(series)),
        "seasonally_adjusted": index is not None,
        "date_range": {
            "from": str(sales["date"].min().date()),
            "to": str(sales["date"].max().date()),
        },
        "trend": _trend(adjusted),
        "momentum": _momentum(series, adjusted),
        "volatility": _volatility(series),
        "seasonality": _seasonality(series, index),
        "weekday_pattern": _weekday_pattern(sales),
        "product_momentum": _product_momentum(sales),
        "concentration": _concentration(sales),
        "margin": _margin_pressure(frames, series),
        "customers": _repeat_behaviour(sales),
    }

    report["headlines"] = _headlines(report)
    return report


def _headlines(report: dict[str, Any]) -> list[str]:
    """Plain-language summary of the strongest signals."""
    lines = [report["trend"]["summary"]]

    momentum = report["momentum"]
    if momentum.get("yoy_change_pct") is not None:
        lines.append(
            f"Demand is {momentum['state']}: the last {momentum['window_months']} months ran "
            f"{momentum['yoy_change_pct']:+.1f}% against the same months last year."
        )
    elif momentum["change_pct"] is not None:
        lines.append(
            f"Demand is {momentum['state']}: the last {momentum['window_months']} months averaged "
            f"{momentum['change_pct']:+.1f}% versus the {momentum['window_months']} before "
            "(not yet seasonally comparable)."
        )
    if momentum["streak_months"] >= 3:
        lines.append(
            f"{momentum['streak_months']} consecutive months trending {momentum['streak_direction']}."
        )

    season = report["seasonality"]
    if season.get("detected"):
        lines.append(season["summary"])

    products = report["product_momentum"]
    if products.get("available"):
        if products["rising"]:
            top = products["rising"][0]
            lines.append(
                f"{top['product']} is the fastest-growing line, up ₹{top['delta']:,.0f} "
                f"in the last {products['window_days']} days."
            )
        if products["declining"]:
            worst = products["declining"][0]
            lines.append(
                f"{worst['product']} is losing ground, down ₹{abs(worst['delta']):,.0f} "
                f"over the same window."
            )

    concentration = report["concentration"].get("product")
    if concentration and concentration["risk"] != "low":
        lines.append(
            f"{concentration['top_name']} alone drives {concentration['top_share_pct']}% of revenue "
            f"- a {concentration['risk']} concentration risk."
        )

    margin = report["margin"]
    if margin.get("available") and margin.get("squeeze"):
        lines.append(
            f"Costs are outpacing sales {margin['basis']}: expenses "
            f"{margin['expense_growth_pct']:+.1f}% versus revenue "
            f"{margin['revenue_growth_pct']:+.1f}%."
        )

    volatility = report["volatility"]
    if volatility["level"] == "high":
        lines.append(
            f"Monthly revenue swings are wide ({volatility['coefficient_of_variation']}% variation), "
            "so treat single-month moves cautiously."
        )

    return lines
