from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.advisor import generate_action_plan
from app.services.analytics import (
    dashboard_kpis,
    expense_analytics,
    inventory_analytics,
    profitability_analytics,
    sales_analytics,
)
from app.services.ml_engine import analyze_sentiment, detect_anomalies, forecast_sales, segment_customers
from app.services.patterns import detect_patterns


def generate_insights(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    kpis = dashboard_kpis(frames)
    sales = sales_analytics(frames)
    expenses = expense_analytics(frames)
    profit = profitability_analytics(frames)
    inventory = inventory_analytics(frames)
    sentiment = analyze_sentiment(frames)
    anomalies = detect_anomalies(frames)
    forecast = forecast_sales(frames)
    patterns = forecast.get("patterns") or detect_patterns(frames)

    insights: list[str] = []

    if kpis["total_revenue"] or kpis["total_expenses"]:
        insights.append(
            f"Revenue stands at ₹{kpis['total_revenue']:,.0f} against expenses of ₹{kpis['total_expenses']:,.0f}, "
            f"producing a net profit of ₹{kpis['net_profit']:,.0f} ({kpis['profit_margin']:.1f}% margin)."
        )

    # Pattern headlines carry the structural story: trend, momentum, seasonality, mix shifts.
    insights.extend(patterns.get("headlines", []))

    if expenses.get("highest_category"):
        cat = expenses["highest_category"]
        insights.append(
            f"The largest expense category is {cat['category']} at ₹{cat['amount']:,.0f}."
        )

    if sales.get("top_product"):
        top = sales["top_product"]
        insights.append(
            f"Top product is {top['product']} with ₹{top['revenue']:,.0f} revenue and {top['units']} units sold."
        )

    reorder = inventory.get("reorder_required") or []
    if reorder:
        names = ", ".join(item["product"] for item in reorder[:3])
        insights.append(f"{len(reorder)} products need reordering, including {names}.")

    if sentiment.get("distribution"):
        dist = sentiment["distribution"]
        insights.append(
            f"Customer sentiment is {dist.get('Positive', 0)}% positive, "
            f"{dist.get('Neutral', 0)}% neutral, and {dist.get('Negative', 0)}% negative."
        )
        if sentiment.get("main_complaint") and sentiment["main_complaint"] != "None detected":
            insights.append(f"Main customer complaint theme: {sentiment['main_complaint']}.")

    if anomalies.get("count"):
        insights.append(
            f"{anomalies['count']} unusual patterns were detected across sales, expenses, or inventory."
        )

    if forecast.get("next_month_revenue") is not None:
        first = (forecast.get("predictions") or [{}])[0]
        insights.append(
            f"Next month is projected at ₹{forecast['next_month_revenue']:,.0f} "
            f"(80% range ₹{first.get('lower_bound', 0):,.0f}-₹{first.get('upper_bound', 0):,.0f}) "
            f"using {forecast.get('selected_model')} at {forecast.get('confidence')} confidence."
        )

    if not insights:
        insights.append(
            "Upload sales, expenses, inventory, and review data to generate AI business insights."
        )

    return {
        "summary": " ".join(insights),
        "insights": insights,
        "kpis": kpis,
        "profit": profit,
        "patterns": patterns,
    }


def generate_recommendations(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Prioritised actions derived from detected patterns and the current market situation."""
    plan = generate_action_plan(frames)
    recommendations = plan["recommendations"][:14]
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "market_context": plan.get("market_context", {}),
        "key_findings": plan.get("key_findings", []),
        "forecast_summary": plan.get("forecast_summary", {}),
        "counts": plan.get("counts", {}),
    }


def answer_business_question(frames: dict[str, pd.DataFrame], question: str) -> dict[str, Any]:
    q = question.lower().strip()
    kpis = dashboard_kpis(frames)
    sales = sales_analytics(frames)
    expenses = expense_analytics(frames)
    inventory = inventory_analytics(frames)
    sentiment = analyze_sentiment(frames)
    forecast = forecast_sales(frames)
    anomalies = detect_anomalies(frames)
    patterns = forecast.get("patterns") or {}
    sources: list[str] = []

    if "profit" in q and ("decrease" in q or "drop" in q or "why" in q):
        sources = ["profitability", "expenses", "sales"]
        answer = (
            f"Profit is currently ₹{kpis['net_profit']:,.0f} with a margin of {kpis['profit_margin']:.1f}%. "
            f"Revenue is ₹{kpis['total_revenue']:,.0f} while expenses are ₹{kpis['total_expenses']:,.0f}."
        )
        margin = patterns.get("margin") or {}
        if margin.get("squeeze"):
            answer += (
                f" Costs are the driver: expenses grew {margin['expense_growth_pct']:+.1f}% while "
                f"revenue grew {margin['revenue_growth_pct']:+.1f}%."
            )
        if expenses.get("highest_category"):
            cat = expenses["highest_category"]
            answer += f" The largest expense driver is {cat['category']} (₹{cat['amount']:,.0f})."
        if kpis["sales_growth"] < 0:
            answer += f" Sales also declined by {abs(kpis['sales_growth']):.1f}% month-over-month."
    elif any(k in q for k in ("trend", "pattern", "growing", "declining", "momentum")):
        sources = ["patterns"]
        headlines = patterns.get("headlines") or []
        answer = (
            " ".join(headlines)
            if headlines
            else patterns.get("message", "Not enough dated sales history to detect trends yet.")
        )
    elif "season" in q:
        sources = ["patterns"]
        season = patterns.get("seasonality") or {}
        answer = (
            season["summary"]
            if season.get("detected")
            else season.get("message", "No clear seasonal pattern was detected in your data.")
        )
    elif any(k in q for k in ("recommend", "what should i do", "action", "advice", "improve")):
        sources = ["recommendations"]
        plan = generate_action_plan(frames)
        top = plan["recommendations"][:3]
        answer = plan["market_context"].get("summary", "") + " Top actions: " + " ".join(
            f"({i + 1}) {item['action']}" for i, item in enumerate(top)
        )
    elif any(k in q for k in ("accurate", "accuracy", "reliable", "how good")):
        sources = ["forecast"]
        accuracy = forecast.get("accuracy")
        if accuracy:
            answer = (
                f"The forecast uses {forecast['selected_model']}, chosen by walk-forward backtesting "
                f"against {len(forecast.get('evaluation', []))} candidate models. On held-out months it "
                f"averaged {accuracy['mape']}% error (MAE ₹{accuracy['mae']:,.0f}) across "
                f"{accuracy['folds']} folds, and called the direction of change correctly "
                f"{accuracy.get('direction_accuracy')}% of the time. Overall confidence: "
                f"{forecast.get('confidence')}."
            )
        else:
            answer = (
                "There is not yet enough history to validate the forecast, so treat it as indicative. "
                "Accuracy metrics appear once you have around 6+ months of sales data."
            )
    elif "highest revenue" in q or "top product" in q or "best product" in q:
        sources = ["sales"]
        top = sales.get("top_product")
        answer = (
            f"Your top product is {top['product']} with ₹{top['revenue']:,.0f} revenue."
            if top
            else "No product sales data is available yet."
        )
    elif "reorder" in q or "stock" in q or "inventory" in q:
        sources = ["inventory"]
        items = inventory.get("reorder_required") or []
        if items:
            names = ", ".join(f"{i['product']} ({i['current_stock']})" for i in items[:5])
            answer = f"Products that need reordering: {names}."
        else:
            answer = "No products currently require reordering based on uploaded inventory data."
    elif "expense" in q or "biggest cost" in q:
        sources = ["expenses"]
        cat = expenses.get("highest_category")
        answer = (
            f"Your biggest expense category is {cat['category']} at ₹{cat['amount']:,.0f}."
            if cat
            else "No expense data uploaded yet."
        )
    elif "highest sales" in q or "best month" in q:
        sources = ["sales"]
        monthly = sales.get("monthly") or []
        if monthly:
            best = max(monthly, key=lambda x: x["value"])
            answer = f"{best['period']} had the highest sales at ₹{best['value']:,.0f}."
        else:
            answer = "Monthly sales history is not available yet."
    elif "expected revenue" in q or "forecast" in q or "next month" in q or "predict" in q:
        sources = ["forecast"]
        predictions = forecast.get("predictions") or []
        if predictions:
            first = predictions[0]
            answer = (
                f"{first['period']} is projected at ₹{first['predicted_revenue']:,.0f}, with an 80% "
                f"range of ₹{first['lower_bound']:,.0f} to ₹{first['upper_bound']:,.0f}. "
                f"That is {first['change_vs_recent_avg']:+.1f}% against the recent monthly average. "
                f"Model: {forecast['selected_model']} ({forecast.get('confidence')} confidence)."
            )
            if len(predictions) >= 3:
                answer += f" The next {len(predictions)} months total ₹{forecast['horizon_total']:,.0f}."
        else:
            answer = forecast.get("message", "Not enough history to forecast yet.")
    elif "complain" in q or "sentiment" in q or ("customer" in q and "issue" in q):
        sources = ["sentiment"]
        dist = sentiment.get("distribution") or {}
        answer = (
            f"Customer sentiment: {dist.get('Positive', 0)}% positive, "
            f"{dist.get('Neutral', 0)}% neutral, {dist.get('Negative', 0)}% negative. "
            f"Main complaint: {sentiment.get('main_complaint', 'N/A')}."
        )
    elif "anomaly" in q or "unusual" in q:
        sources = ["anomalies"]
        answer = (
            f"Detected {anomalies.get('count', 0)} anomalies. "
            "Review the Anomaly Detection page for details."
        )
    elif "revenue" in q:
        sources = ["dashboard"]
        answer = f"Total revenue is ₹{kpis['total_revenue']:,.0f} across {kpis['total_orders']} orders."
    else:
        sources = ["dashboard", "insights"]
        summary = generate_insights(frames)["summary"]
        answer = (
            f"Based on your current business data: {summary} "
            "Try asking about profit, trends, seasonality, top products, reorders, expenses, "
            "forecast accuracy, or what you should do next."
        )

    return {"answer": answer, "sources": sources, "kpis_snapshot": kpis}


def build_report_payload(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    return {
        "executive_summary": generate_insights(frames),
        "kpis": dashboard_kpis(frames),
        "sales": sales_analytics(frames),
        "expenses": expense_analytics(frames),
        "profitability": profitability_analytics(frames),
        "inventory": inventory_analytics(frames),
        "sentiment": analyze_sentiment(frames),
        "forecast": forecast_sales(frames),
        "anomalies": detect_anomalies(frames),
        "segments": segment_customers(frames),
        "recommendations": generate_recommendations(frames),
    }
