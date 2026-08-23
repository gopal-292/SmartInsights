"""Situation-aware recommendation engine.

Combines the pattern report, the forecast, inventory levels, cost structure,
customer behaviour and review sentiment into prioritised actions. Every action
carries the evidence it was derived from and a quantified expected impact so the
owner can judge whether it is worth doing.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.analytics import dashboard_kpis, inventory_analytics
from app.services.forecasting import build_forecast
from app.services.ml_engine import analyze_sentiment, detect_anomalies
from app.services.patterns import MONTH_NAMES, detect_patterns

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _money(value: float) -> str:
    return f"₹{value:,.0f}"


def _action(
    priority: str,
    area: str,
    situation: str,
    action: str,
    impact: str,
    confidence: str,
    evidence: list[str],
    timeframe: str,
) -> dict[str, Any]:
    return {
        "priority": priority,
        "area": area,
        "situation": situation,
        # `problem` and `recommendation` keep older clients and the PDF template working.
        "problem": situation,
        "recommendation": action,
        "action": action,
        "expected_impact": impact,
        "confidence": confidence,
        "evidence": evidence,
        "timeframe": timeframe,
    }


def _daily_demand(sales: pd.DataFrame, growth_factor: float) -> dict[str, float]:
    """Units sold per day per product over the recent window, scaled by forecast growth."""
    if sales.empty or "product" not in sales.columns or "date" not in sales.columns:
        return {}

    df = sales.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return {}

    latest = df["date"].max()
    span = max((latest - df["date"].min()).days, 1)
    window = min(60, span)
    recent = df[df["date"] > latest - pd.Timedelta(days=window)]
    if recent.empty:
        return {}

    if "quantity" in recent.columns:
        units = recent.groupby("product")["quantity"].sum()
    else:
        units = recent.groupby("product").size()

    return {
        str(product): float(total) / window * growth_factor
        for product, total in units.items()
        if float(total) > 0
    }


def _market_context(patterns: dict[str, Any], forecast: dict[str, Any], kpis: dict[str, Any]) -> dict[str, Any]:
    trend = patterns.get("trend", {})
    momentum = patterns.get("momentum", {})
    margin = patterns.get("margin", {})
    predictions = forecast.get("predictions") or []

    demand_direction = trend.get("direction", "unknown")
    next_month = predictions[0]["predicted_revenue"] if predictions else None
    recent_avg = momentum.get("recent_avg")
    gap_pct = predictions[0]["change_vs_recent_avg"] if predictions else None

    if demand_direction == "growing" and momentum.get("state") == "accelerating":
        outlook = "expansion"
    elif demand_direction == "declining" or momentum.get("state") == "slowing":
        outlook = "contraction"
    else:
        outlook = "steady"

    cost_pressure = "rising" if margin.get("squeeze") else "contained" if margin.get("available") else "unknown"

    return {
        "outlook": outlook,
        "demand_direction": demand_direction,
        "momentum_state": momentum.get("state"),
        "next_month_forecast": next_month,
        "recent_monthly_average": recent_avg,
        "forecast_vs_recent_pct": gap_pct,
        "forecast_confidence": forecast.get("confidence"),
        "cost_pressure": cost_pressure,
        "profit_margin_pct": kpis.get("profit_margin"),
        "volatility": patterns.get("volatility", {}).get("level"),
        "summary": _context_summary(outlook, demand_direction, gap_pct, cost_pressure, kpis),
    }


def _context_summary(
    outlook: str, direction: str, gap_pct: float | None, cost_pressure: str, kpis: dict[str, Any]
) -> str:
    parts = [f"Market position looks like {outlook}: demand is {direction}"]
    if gap_pct is not None:
        parts.append(f"next month is projected {gap_pct:+.1f}% against the recent run rate")
    if cost_pressure == "rising":
        parts.append("cost growth is outrunning revenue growth")
    margin = kpis.get("profit_margin")
    if margin is not None:
        parts.append(f"current margin is {margin:.1f}%")
    return ", ".join(parts) + "."


def _demand_actions(patterns: dict[str, Any], forecast: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    predictions = forecast.get("predictions") or []
    if not predictions:
        return actions

    first = predictions[0]
    gap_pct = first.get("change_vs_recent_avg")
    recent_avg = patterns.get("momentum", {}).get("recent_avg") or 0.0
    confidence = forecast.get("confidence", "low")
    accuracy = forecast.get("accuracy") or {}
    evidence = [
        f"Selected model: {forecast.get('selected_model')} ({forecast.get('selection_basis')})",
    ]
    if accuracy.get("mape") is not None:
        evidence.append(f"Backtest error {accuracy['mape']}% MAPE over {accuracy.get('folds')} folds")
    if accuracy.get("direction_accuracy") is not None:
        evidence.append(f"Direction called correctly {accuracy['direction_accuracy']}% of the time")

    if gap_pct is not None and gap_pct <= -8:
        shortfall = max(recent_avg - first["predicted_revenue"], 0.0)
        actions.append(
            _action(
                "critical" if gap_pct <= -20 else "high",
                "Demand",
                f"Revenue for {first['period']} is projected at {_money(first['predicted_revenue'])}, "
                f"{abs(gap_pct):.1f}% below the recent monthly average.",
                "Pull demand forward now: launch a time-boxed offer on your fastest-moving products, "
                "reactivate dormant customers by email or phone, and hold back discretionary spend "
                "until the pipeline recovers.",
                f"Closing the gap protects roughly {_money(shortfall)} of monthly revenue.",
                confidence,
                evidence,
                "this month",
            )
        )
    elif gap_pct is not None and gap_pct >= 8:
        upside = max(first["predicted_revenue"] - recent_avg, 0.0)
        actions.append(
            _action(
                "high",
                "Demand",
                f"Demand is turning up: {first['period']} is projected at "
                f"{_money(first['predicted_revenue'])}, {gap_pct:+.1f}% above the recent average.",
                "Protect the upside before it arrives: raise stock cover on your growing lines, "
                "confirm supplier lead times, and add staffing or delivery capacity for the peak.",
                f"Capturing the projected lift is worth about {_money(upside)} next month.",
                confidence,
                evidence,
                "this month",
            )
        )

    horizon_total = forecast.get("horizon_total")
    if horizon_total and len(predictions) >= 3 and confidence in {"high", "medium"}:
        actions.append(
            _action(
                "low",
                "Planning",
                f"The next {len(predictions)} months are projected to total {_money(horizon_total)} "
                f"(range {_money(predictions[-1]['lower_bound'])}-{_money(predictions[-1]['upper_bound'])} "
                f"by {predictions[-1]['period']}).",
                "Set your purchasing and hiring budget against the lower bound of the forecast, "
                "not the midpoint, so a weak month does not become a cash problem.",
                "Prevents over-committing cash on an optimistic projection.",
                confidence,
                [f"80% prediction interval widens with horizon; residual spread from walk-forward backtest"],
                "this quarter",
            )
        )

    return actions


def _seasonal_actions(patterns: dict[str, Any], forecast: dict[str, Any]) -> list[dict[str, Any]]:
    season = patterns.get("seasonality", {})
    predictions = forecast.get("predictions") or []
    if not season.get("detected") or not predictions:
        return []

    index = season.get("monthly_index", {})
    upcoming: list[tuple[str, float]] = []
    for prediction in predictions[:3]:
        try:
            month_number = pd.Period(prediction["period"], freq="M").month
        except Exception:
            continue
        name = MONTH_NAMES[month_number - 1]
        if name in index:
            upcoming.append((name, float(index[name])))

    if not upcoming:
        return []

    peak = max(upcoming, key=lambda item: item[1])
    trough = min(upcoming, key=lambda item: item[1])
    actions: list[dict[str, Any]] = []
    evidence = [season["summary"], f"Seasonal strength {season['strength_pct']}% of average revenue"]

    if peak[1] >= 1.10:
        actions.append(
            _action(
                "high",
                "Seasonality",
                f"Of the months ahead, {peak[0]} carries the strongest seasonal pull - "
                f"historically {(peak[1] - 1) * 100:+.0f}% versus an average month "
                f"(your annual peak is {season['peak_month']}).",
                f"Start the {peak[0]} build-up 4-6 weeks early: place supplier orders now, "
                "schedule the campaign, and roster extra capacity for the peak weeks.",
                f"Avoiding stockouts through the peak protects the extra "
                f"{(peak[1] - 1) * 100:.0f}% of seasonal volume.",
                "high",
                evidence,
                "next 4-6 weeks",
            )
        )
    if trough[1] <= 0.90:
        actions.append(
            _action(
                "medium",
                "Seasonality",
                f"{trough[0]} is historically soft at {(trough[1] - 1) * 100:.0f}% versus an "
                f"average month.",
                f"Plan {trough[0]} as a low-cost month: shift maintenance and training into it, "
                "delay non-essential purchases, and run a low-margin volume offer to keep cash moving.",
                "Smooths the seasonal cash dip instead of absorbing it.",
                "high",
                evidence,
                "before " + trough[0],
            )
        )
    return actions


def _product_actions(patterns: dict[str, Any]) -> list[dict[str, Any]]:
    products = patterns.get("product_momentum", {})
    if not products.get("available"):
        return []

    actions: list[dict[str, Any]] = []
    window = products["window_days"]

    for item in products.get("declining", [])[:2]:
        change = item["change_pct"]
        actions.append(
            _action(
                "high" if change is not None and change <= -30 else "medium",
                "Product Mix",
                f"{item['product']} fell from {_money(item['previous_revenue'])} to "
                f"{_money(item['recent_revenue'])} in the last {window} days"
                + (f" ({change:+.1f}%)." if change is not None else "."),
                f"Diagnose {item['product']} before it drags the mix down: check whether it is "
                "price, availability or a competitor. If demand is genuinely gone, bundle it with a "
                "fast mover to clear stock rather than discounting it alone.",
                f"Recovering half the drop adds about {_money(abs(item['delta']) / 2)} per "
                f"{window}-day cycle.",
                "medium",
                [f"Revenue delta {_money(item['delta'])} over a {window}-day comparison window"],
                "this month",
            )
        )

    for item in products.get("rising", [])[:2]:
        actions.append(
            _action(
                "medium",
                "Product Mix",
                f"{item['product']} grew to {_money(item['recent_revenue'])} in the last "
                f"{window} days, up {_money(item['delta'])}.",
                f"Put weight behind {item['product']}: give it prime placement, test a small price "
                "increase since demand is proven, and secure supply ahead of the trend.",
                f"Sustaining the current run rate is worth about {_money(item['delta'])} per "
                f"{window}-day cycle.",
                "medium",
                [f"Fastest-growing line by absolute revenue over {window} days"],
                "this month",
            )
        )

    return actions


def _inventory_actions(
    frames: dict[str, pd.DataFrame], patterns: dict[str, Any], forecast: dict[str, Any]
) -> list[dict[str, Any]]:
    inventory = inventory_analytics(frames)
    items = inventory.get("items") or []
    if not items:
        return []

    predictions = forecast.get("predictions") or []
    recent_avg = patterns.get("momentum", {}).get("recent_avg") or 0.0
    growth_factor = 1.0
    if predictions and recent_avg > 0:
        growth_factor = min(max(predictions[0]["predicted_revenue"] / recent_avg, 0.5), 2.0)

    demand = _daily_demand(frames.get("sales", pd.DataFrame()), growth_factor)
    actions: list[dict[str, Any]] = []
    stockout_risk: list[dict[str, Any]] = []
    overstock: list[dict[str, Any]] = []

    for item in items:
        per_day = demand.get(str(item["product"]))
        if not per_day:
            continue
        cover_days = item["current_stock"] / per_day
        if cover_days < 21:
            shortfall_units = max(per_day * 45 - item["current_stock"], 0)
            stockout_risk.append({**item, "cover_days": cover_days, "reorder_units": shortfall_units})
        elif cover_days > 120:
            overstock.append({**item, "cover_days": cover_days})

    stockout_risk.sort(key=lambda row: row["cover_days"])
    for item in stockout_risk[:3]:
        actions.append(
            _action(
                "critical" if item["cover_days"] < 10 else "high",
                "Inventory",
                f"{item['product']} has {item['current_stock']} units left - about "
                f"{item['cover_days']:.0f} days of cover at forecast demand.",
                f"Raise a purchase order for roughly {item['reorder_units']:.0f} units of "
                f"{item['product']}"
                + (f" with {item['supplier']}" if item.get("supplier") else "")
                + " to reach 45 days of cover.",
                f"Prevents an estimated stockout in {item['cover_days']:.0f} days on a line "
                "that is actively selling.",
                "high" if forecast.get("confidence") != "low" else "medium",
                [
                    f"Recent demand {demand[str(item['product'])]:.1f} units/day, "
                    f"scaled by forecast growth factor {growth_factor:.2f}",
                ],
                "this week",
            )
        )

    overstock.sort(key=lambda row: -row["stock_value"])
    for item in overstock[:2]:
        actions.append(
            _action(
                "medium",
                "Inventory",
                f"{item['product']} holds {item['current_stock']} units - about "
                f"{item['cover_days']:.0f} days of cover, far beyond what demand needs.",
                f"Free the capital tied up in {item['product']}: run a clearance or bundle it with "
                "a fast mover, and pause reordering until cover drops below 60 days.",
                f"Releases up to {_money(item['stock_value'] * 0.5)} of working capital.",
                "medium",
                [f"Cover of {item['cover_days']:.0f} days against current demand"],
                "this quarter",
            )
        )

    # Items with no recent sales at all are a separate, quieter problem.
    dead = [
        item
        for item in items
        if item["current_stock"] > 0 and str(item["product"]) not in demand
    ]
    if dead:
        value = sum(item["stock_value"] for item in dead)
        names = ", ".join(str(item["product"]) for item in dead[:3])
        actions.append(
            _action(
                "medium" if value > 0 else "low",
                "Inventory",
                f"{len(dead)} stocked product(s) recorded no sales in the recent window ({names}).",
                "Decide explicitly whether to relaunch or liquidate these lines - dead stock is "
                "cash sitting on a shelf and it distorts your reorder logic.",
                f"Up to {_money(value)} of stock value is currently unproductive.",
                "medium",
                ["No sales rows for these products in the recent demand window"],
                "this quarter",
            )
        )

    return actions


def _cost_actions(patterns: dict[str, Any], kpis: dict[str, Any]) -> list[dict[str, Any]]:
    margin = patterns.get("margin", {})
    actions: list[dict[str, Any]] = []

    if margin.get("available") and margin.get("squeeze"):
        top = (margin.get("top_expense_categories") or [None])[0]
        target = top["category"] if top else "your largest cost line"
        saving = top["amount"] * 0.1 if top else 0.0
        actions.append(
            _action(
                "critical",
                "Margins",
                f"Measured {margin['basis']}, expenses are growing "
                f"{margin['expense_growth_pct']:+.1f}% while revenue grows "
                f"{margin['revenue_growth_pct']:+.1f}% - margin is being squeezed"
                + (
                    f" and has moved {margin['margin_change_pts']:+.1f} points."
                    if margin.get("margin_change_pts") is not None
                    else "."
                ),
                f"Attack {target} first since it is your biggest recent cost: renegotiate the rate, "
                "cut the lowest-return line items, and put a monthly cap on it before volume grows "
                "the problem further.",
                f"A 10% reduction on {target} recovers about {_money(saving)} per month."
                if saving
                else "Restores the gap between revenue and cost growth.",
                "high",
                [
                    f"Revenue growth {margin['revenue_growth_pct']}% vs expense growth "
                    f"{margin['expense_growth_pct']}% over {margin['comparison_months']} months "
                    f"({margin['basis']})",
                ],
                "this month",
            )
        )

    revenue = kpis.get("total_revenue") or 0.0
    if revenue > 0 and kpis.get("profit_margin", 0) < 15:
        actions.append(
            _action(
                "high",
                "Profitability",
                f"Net margin is {kpis['profit_margin']:.1f}%, which leaves very little room "
                "to absorb a bad month.",
                "Reprice deliberately rather than broadly: lift prices 3-5% on products where demand "
                "is growing, hold prices on price-sensitive lines, and drop the products that cannot "
                "carry their share of overhead.",
                f"A 3% price lift on current revenue is roughly {_money(revenue * 0.03)} of gross profit.",
                "medium",
                [f"Revenue {_money(revenue)}, expenses {_money(kpis.get('total_expenses', 0))}"],
                "this quarter",
            )
        )

    return actions


def _customer_actions(patterns: dict[str, Any], sentiment: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    customers = patterns.get("customers", {})

    if customers.get("available"):
        at_risk = customers.get("at_risk_valuable_customers", 0)
        if at_risk:
            actions.append(
                _action(
                    "high",
                    "Retention",
                    f"{at_risk} of your highest-spending customers "
                    f"{'has' if at_risk == 1 else 'have'} not bought in over "
                    f"{customers['dormant_days']} days.",
                    "Run a personal win-back on this exact list - a call or named email with a "
                    "reason to return beats a broadcast discount, and it tells you why they left.",
                    f"{_money(customers['revenue_at_risk'])} of historical revenue sits with these "
                    "accounts.",
                    "medium",
                    [
                        f"{customers['dormant_customers']} dormant customers total, "
                        f"{at_risk} in the top spending quartile",
                    ],
                    "this month",
                )
            )

        if customers.get("repeat_rate_pct", 100) < 25:
            actions.append(
                _action(
                    "medium",
                    "Retention",
                    f"Only {customers['repeat_rate_pct']}% of customers have bought more than once, "
                    "so growth depends entirely on new acquisition.",
                    "Build one repeat mechanism: a follow-up offer timed to your average repurchase "
                    "gap, or a small loyalty credit. Acquisition costs far more than reactivation.",
                    f"Moving repeat rate up 10 points on {customers['customers']} customers adds "
                    f"roughly {_money(customers['customers'] * 0.1 * customers['avg_order_value'])} "
                    "per cycle.",
                    "medium",
                    [f"Repeat rate {customers['repeat_rate_pct']}% across {customers['customers']} customers"],
                    "this quarter",
                )
            )

    distribution = sentiment.get("distribution") or {}
    negative = distribution.get("Negative", 0)
    complaint = sentiment.get("main_complaint")
    if negative >= 20 and complaint and complaint != "None detected":
        actions.append(
            _action(
                "high" if negative >= 35 else "medium",
                "Customer Experience",
                f"{negative}% of reviews are negative and the dominant theme is {complaint}.",
                f"Fix {complaint.lower()} as a process, not a case: find the step that fails, assign "
                "an owner, and re-check the review mix in 30 days to confirm it moved.",
                "Negative experience is the cheapest churn to prevent - it is already diagnosed.",
                "medium",
                [
                    f"Sentiment split {distribution}",
                    f"Sample size {sentiment.get('sample_size')} reviews",
                ],
                "this month",
            )
        )

    return actions


def _risk_actions(patterns: dict[str, Any], anomalies: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    concentration = patterns.get("concentration", {})
    for key, label in (("product", "product"), ("customer", "customer")):
        block = concentration.get(key)
        if block and block["risk"] == "high":
            actions.append(
                _action(
                    "high",
                    "Risk",
                    f"{block['top_name']} accounts for {block['top_share_pct']}% of revenue across "
                    f"only {block['distinct_count']} {label}s.",
                    f"Reduce single-{label} dependence: set a target of bringing the top {label} below "
                    "30% of revenue by growing the next tier, and make sure you are not one lost "
                    f"{label} away from a cash crisis.",
                    f"Removes a single point of failure covering {block['top_share_pct']}% of revenue.",
                    "high",
                    [f"Top 3 {label}s hold {block['top3_share_pct']}% of revenue"],
                    "this quarter",
                )
            )

    volatility = patterns.get("volatility", {})
    if volatility.get("level") == "high":
        actions.append(
            _action(
                "medium",
                "Cash Flow",
                f"Monthly revenue varies by {volatility['coefficient_of_variation']}% around the mean "
                f"(best {volatility['best_month']['period']}, worst {volatility['worst_month']['period']}).",
                "Hold a cash buffer sized to your worst month rather than your average one, and avoid "
                "fixed commitments that only work at peak volume.",
                f"Covers the gap between your best and worst month "
                f"({_money(volatility['best_month']['revenue'] - volatility['worst_month']['revenue'])}).",
                "high",
                ["Coefficient of variation on monthly revenue"],
                "this quarter",
            )
        )

    count = anomalies.get("count", 0)
    if count:
        actions.append(
            _action(
                "medium",
                "Anomalies",
                f"{count} data point(s) sit outside their normal range after weekday and "
                "seasonal effects are accounted for.",
                "Review the flagged days and expense spikes before month-end close - unexplained "
                "outliers are usually either a data entry error or a real event worth understanding.",
                "Protects both the books and the accuracy of every model built on this data.",
                "high",
                [f"Techniques: {', '.join(anomalies.get('techniques', []))}"],
                "this week",
            )
        )

    weekday = patterns.get("weekday_pattern", {})
    if weekday.get("detected"):
        actions.append(
            _action(
                "low",
                "Operations",
                f"{weekday['best_day']} outsells {weekday['worst_day']} by "
                f"{weekday['spread_pct']:.0f}% of an average day.",
                f"Match cost to demand: staff up for {weekday['best_day']} and either trim hours or "
                f"run a targeted offer on {weekday['worst_day']}.",
                "Improves labour efficiency without touching revenue.",
                "medium",
                ["Average revenue by day of week"],
                "this month",
            )
        )

    return actions


def generate_action_plan(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Full recommendation report: market context plus prioritised, evidenced actions."""
    sales = frames.get("sales", pd.DataFrame())
    patterns = detect_patterns(frames)
    kpis = dashboard_kpis(frames)

    if not patterns.get("available"):
        return {
            "market_context": {"outlook": "unknown", "summary": patterns.get("message", "")},
            "patterns": patterns,
            "recommendations": [
                _action(
                    "high",
                    "Setup",
                    patterns.get("message", "Not enough data to analyse."),
                    "Upload dated sales history plus expenses, inventory and reviews. Three or more "
                    "months of sales unlocks forecasting; twelve months unlocks seasonality.",
                    "Every other recommendation depends on this data.",
                    "high",
                    [],
                    "now",
                )
            ],
            "counts": {"critical": 0, "high": 1, "medium": 0, "low": 0},
        }

    forecast = build_forecast(sales, periods=6)
    sentiment = analyze_sentiment(frames)
    anomalies = detect_anomalies(frames)

    recommendations = [
        *_demand_actions(patterns, forecast),
        *_seasonal_actions(patterns, forecast),
        *_inventory_actions(frames, patterns, forecast),
        *_cost_actions(patterns, kpis),
        *_product_actions(patterns),
        *_customer_actions(patterns, sentiment),
        *_risk_actions(patterns, anomalies),
    ]
    recommendations.sort(key=lambda row: PRIORITY_ORDER.get(row["priority"], 9))

    if not recommendations:
        recommendations.append(
            _action(
                "low",
                "Steady State",
                "No structural problems surfaced: demand, costs, stock cover and sentiment are all "
                "within normal ranges.",
                "Keep the current plan and re-run this analysis after the next month of data lands. "
                "Use the spare capacity to test one growth experiment on your strongest product.",
                "Maintains the current trajectory.",
                "medium",
                patterns.get("headlines", [])[:2],
                "next month",
            )
        )

    counts = {level: 0 for level in PRIORITY_ORDER}
    for item in recommendations:
        counts[item["priority"]] = counts.get(item["priority"], 0) + 1

    return {
        "market_context": _market_context(patterns, forecast, kpis),
        "patterns": patterns,
        "key_findings": patterns.get("headlines", []),
        "forecast_summary": {
            "next_month_revenue": forecast.get("next_month_revenue"),
            "horizon_total": forecast.get("horizon_total"),
            "selected_model": forecast.get("selected_model"),
            "confidence": forecast.get("confidence"),
            "accuracy": forecast.get("accuracy"),
        },
        "recommendations": recommendations,
        "counts": counts,
    }
