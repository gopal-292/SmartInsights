from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.analytics import (
    dashboard_kpis,
    expense_analytics,
    inventory_analytics,
    profitability_analytics,
    sales_analytics,
)
from app.services.ml_engine import analyze_sentiment, detect_anomalies, forecast_sales, segment_customers


def generate_insights(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    kpis = dashboard_kpis(frames)
    sales = sales_analytics(frames)
    expenses = expense_analytics(frames)
    profit = profitability_analytics(frames)
    inventory = inventory_analytics(frames)
    sentiment = analyze_sentiment(frames)
    anomalies = detect_anomalies(frames)
    forecast = forecast_sales(frames)

    insights: list[str] = []

    if kpis["total_revenue"] or kpis["total_expenses"]:
        insights.append(
            f"Revenue stands at ₹{kpis['total_revenue']:,.0f} against expenses of ₹{kpis['total_expenses']:,.0f}, "
            f"producing a net profit of ₹{kpis['net_profit']:,.0f} ({kpis['profit_margin']:.1f}% margin)."
        )

    if kpis["sales_growth"] != 0:
        direction = "increased" if kpis["sales_growth"] > 0 else "decreased"
        insights.append(
            f"Sales growth {direction} by {abs(kpis['sales_growth']):.1f}% compared to the previous month."
        )

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
        insights.append(
            f"Predicted revenue for next month is approximately ₹{forecast['next_month_revenue']:,.0f}."
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
    }


def generate_recommendations(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    kpis = dashboard_kpis(frames)
    sales = sales_analytics(frames)
    expenses = expense_analytics(frames)
    inventory = inventory_analytics(frames)
    sentiment = analyze_sentiment(frames)
    anomalies = detect_anomalies(frames)
    segments = segment_customers(frames)

    recs: list[dict[str, str]] = []

    for item in inventory.get("reorder_required") or []:
        recs.append(
            {
                "priority": "high",
                "area": "Inventory",
                "problem": (
                    f"{item['product']} is below reorder level "
                    f"({item['current_stock']}/{item['reorder_level']})."
                ),
                "recommendation": (
                    f"Reorder {item['product']} from {item.get('supplier') or 'your supplier'} "
                    "to avoid stockouts."
                ),
            }
        )

    if kpis["profit_margin"] < 15 and kpis["total_revenue"] > 0:
        recs.append(
            {
                "priority": "high",
                "area": "Profitability",
                "problem": f"Profit margin is only {kpis['profit_margin']:.1f}%.",
                "recommendation": "Review high expense categories and promote higher-margin products.",
            }
        )

    if expenses.get("expense_growth", 0) > 10:
        recs.append(
            {
                "priority": "medium",
                "area": "Expenses",
                "problem": f"Expenses grew by {expenses['expense_growth']:.1f}% recently.",
                "recommendation": "Investigate unnecessary spend and optimize marketing or overhead costs.",
            }
        )

    for low in sales.get("low_products") or []:
        recs.append(
            {
                "priority": "medium",
                "area": "Sales",
                "problem": f"{low['product']} is among the lowest-performing products.",
                "recommendation": (
                    f"Review pricing and availability of {low['product']} "
                    "and consider a targeted promotion."
                ),
            }
        )

    if sentiment.get("main_complaint") and sentiment["main_complaint"] != "None detected":
        recs.append(
            {
                "priority": "high",
                "area": "Customer Experience",
                "problem": f"Customers frequently mention {sentiment['main_complaint']}.",
                "recommendation": "Improve customer service processes addressing this complaint theme.",
            }
        )

    if anomalies.get("count"):
        recs.append(
            {
                "priority": "medium",
                "area": "Anomalies",
                "problem": f"{anomalies['count']} unusual business patterns were detected.",
                "recommendation": (
                    "Investigate sales anomalies and unexpected expense spikes "
                    "before they affect cash flow."
                ),
            }
        )

    for seg in segments.get("segments") or []:
        if "High-Value" in seg["segment"]:
            recs.append(
                {
                    "priority": "low",
                    "area": "Customer Retention",
                    "problem": f"You have {seg['count']} high-value customers.",
                    "recommendation": "Create loyalty offers for high-value customers to protect retention.",
                }
            )
            break

    if not recs:
        recs.append(
            {
                "priority": "low",
                "area": "Setup",
                "problem": "Limited business data available.",
                "recommendation": (
                    "Upload sales, expenses, inventory, and reviews "
                    "to unlock actionable recommendations."
                ),
            }
        )

    return {"recommendations": recs[:12], "count": len(recs[:12])}


def answer_business_question(frames: dict[str, pd.DataFrame], question: str) -> dict[str, Any]:
    q = question.lower().strip()
    kpis = dashboard_kpis(frames)
    sales = sales_analytics(frames)
    expenses = expense_analytics(frames)
    inventory = inventory_analytics(frames)
    sentiment = analyze_sentiment(frames)
    forecast = forecast_sales(frames)
    anomalies = detect_anomalies(frames)
    sources: list[str] = []

    if "profit" in q and ("decrease" in q or "drop" in q or "why" in q):
        sources = ["profitability", "expenses", "sales"]
        answer = (
            f"Profit is currently ₹{kpis['net_profit']:,.0f} with a margin of {kpis['profit_margin']:.1f}%. "
            f"Revenue is ₹{kpis['total_revenue']:,.0f} while expenses are ₹{kpis['total_expenses']:,.0f}."
        )
        if expenses.get("highest_category"):
            cat = expenses["highest_category"]
            answer += f" The largest expense driver is {cat['category']} (₹{cat['amount']:,.0f})."
        if kpis["sales_growth"] < 0:
            answer += f" Sales also declined by {abs(kpis['sales_growth']):.1f}% month-over-month."
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
    elif "expected revenue" in q or "forecast" in q or "next month" in q:
        sources = ["forecast"]
        if forecast.get("next_month_revenue") is not None:
            answer = f"Expected revenue next month is about ₹{forecast['next_month_revenue']:,.0f}."
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
            "Try asking about profit, top products, reorders, expenses, forecast, or customer complaints."
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
