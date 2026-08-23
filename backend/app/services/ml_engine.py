from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.services.forecasting import build_forecast
from app.services.patterns import detect_patterns


def _ensure_revenue(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.copy()
    if "revenue" not in df.columns and {"quantity", "price"}.issubset(df.columns):
        df["revenue"] = df["quantity"] * df["price"]
    return df


def forecast_sales(frames: dict[str, pd.DataFrame], periods: int = 6) -> dict[str, Any]:
    """Backtested monthly revenue forecast enriched with the detected history patterns."""
    sales = frames.get("sales", pd.DataFrame())
    if sales.empty or "date" not in sales.columns:
        return {
            "message": "Upload historical sales data with date and revenue/quantity-price to forecast.",
            "predictions": [],
            "history": [],
            "evaluation": [],
        }

    result = build_forecast(sales, periods=periods)
    patterns = detect_patterns(frames)
    result["patterns"] = patterns
    result["key_findings"] = patterns.get("headlines", [])
    return result


MAD_TO_SIGMA = 1.4826


def _robust_scale(values: np.ndarray) -> float:
    """Median absolute deviation rescaled to a standard-deviation equivalent.

    Robust to the very outliers being searched for, unlike mean and standard deviation.
    """
    mad = float(np.median(np.abs(values - np.median(values))))
    if mad > 1e-9:
        return mad * MAD_TO_SIGMA
    fallback = float(np.std(values))
    return fallback if fallback > 1e-9 else 1.0


def _sales_anomalies(sales: pd.DataFrame) -> list[dict[str, Any]]:
    """Flag daily revenue that breaks the local level after weekday effects are removed."""
    daily = sales.copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"])
    series = daily.groupby(daily["date"].dt.normalize())["revenue"].sum().sort_index()
    if len(series) < 21:
        return []

    # A busy Saturday is not an anomaly, so normalise the weekly shape out first.
    weekday = series.index.dayofweek
    overall_median = float(series.median()) or 1.0
    weekday_factor = (
        series.groupby(weekday).median() / overall_median
    ).replace(0, 1.0)
    factors = np.array([float(weekday_factor.get(d, 1.0)) or 1.0 for d in weekday])
    adjusted = pd.Series(series.values / factors, index=series.index)

    # Local level, so a festive month is judged against its own neighbourhood.
    expected = adjusted.rolling(29, center=True, min_periods=7).median()
    residual = (adjusted - expected).dropna()
    if residual.empty:
        return []

    scale = _robust_scale(residual.values)
    robust_z = residual / scale

    model = IsolationForest(contamination=0.02, random_state=42)
    forest_labels = pd.Series(
        model.fit_predict(residual.values.reshape(-1, 1)), index=residual.index
    )

    findings: list[dict[str, Any]] = []
    for date, z in robust_z.items():
        agreed = forest_labels.loc[date] == -1 and abs(z) >= 2.5
        if abs(z) < 3.5 and not agreed:
            continue
        actual = float(series.loc[date])
        baseline = float(expected.loc[date]) * float(weekday_factor.get(date.dayofweek, 1.0))
        findings.append(
            {
                "type": "sales",
                "date": date.strftime("%Y-%m-%d"),
                "value": round(actual, 2),
                "expected": round(baseline, 2),
                "expected_range": [
                    round(max(0.0, baseline - 2 * scale), 2),
                    round(baseline + 2 * scale, 2),
                ],
                "z_score": round(float(z), 2),
                "severity": "high" if abs(z) >= 5 else "medium",
                "status": "Anomaly Detected",
                "message": (
                    f"Daily sales of ₹{actual:,.0f} versus an expected ₹{baseline:,.0f} "
                    f"({'above' if actual > baseline else 'below'} normal for a "
                    f"{date.strftime('%A')})"
                ),
            }
        )
    return findings


def _expense_anomalies(expenses: pd.DataFrame) -> list[dict[str, Any]]:
    """Score each expense against its own category; a rent row is not a marketing row."""
    df = expenses.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    if len(df) < 8:
        return []

    if "category" not in df.columns:
        df["category"] = "Uncategorized"

    findings: list[dict[str, Any]] = []
    for category, group in df.groupby("category"):
        values = group["amount"].astype(float).values
        if len(group) < 6:
            continue
        centre = float(np.median(values))
        scale = _robust_scale(values)
        for idx, amount in zip(group.index, values):
            z = (float(amount) - centre) / scale
            if z < 3.5:
                continue
            row = group.loc[idx]
            findings.append(
                {
                    "type": "expense",
                    "date": str(row.get("date", ""))[:10],
                    "value": round(float(amount), 2),
                    "expected": round(centre, 2),
                    "category": str(category),
                    "z_score": round(float(z), 2),
                    "severity": "high" if z >= 5 else "medium",
                    "status": "Anomaly Detected",
                    "message": (
                        f"{category} spend of ₹{float(amount):,.0f} against a typical "
                        f"₹{centre:,.0f} for this category"
                    ),
                }
            )
    return findings


def detect_anomalies(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    sales = _ensure_revenue(frames.get("sales", pd.DataFrame()))
    if not sales.empty and "date" in sales.columns and "revenue" in sales.columns:
        findings.extend(_sales_anomalies(sales))

    expenses = frames.get("expenses", pd.DataFrame())
    if not expenses.empty and "amount" in expenses.columns:
        findings.extend(_expense_anomalies(expenses))

    inventory = frames.get("inventory", pd.DataFrame())
    if not inventory.empty and {"current_stock", "reorder_level"}.issubset(inventory.columns):
        critical = inventory[inventory["current_stock"] <= inventory["reorder_level"] * 0.3]
        for _, row in critical.head(10).iterrows():
            findings.append(
                {
                    "type": "inventory",
                    "product": row.get("product", "Unknown"),
                    "value": int(row.get("current_stock", 0)),
                    "severity": "high",
                    "status": "Anomaly Detected",
                    "message": f"Sudden low stock risk for {row.get('product', 'Unknown')}",
                }
            )

    findings.sort(key=lambda item: -abs(float(item.get("z_score", 0) or 0)))
    return {
        "count": len(findings),
        "anomalies": findings[:25],
        "techniques": ["Median Absolute Deviation", "Rolling Median Baseline", "Isolation Forest"],
        "method": (
            "Weekday effects and the local level are removed before scoring, so seasonal "
            "peaks are not reported as anomalies."
        ),
    }


def analyze_sentiment(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    reviews = frames.get("reviews", pd.DataFrame())
    if reviews.empty:
        return {"message": "No customer reviews uploaded yet.", "distribution": {}}

    texts = []
    if "review_text" in reviews.columns:
        texts = reviews["review_text"].fillna("").astype(str).tolist()
    ratings = reviews["rating"].astype(float) if "rating" in reviews.columns else None

    labels = []
    for i, text in enumerate(texts or [""] * len(reviews)):
        score = 0
        lower = text.lower()
        positive_words = ["good", "great", "excellent", "love", "fast", "amazing", "happy", "perfect"]
        negative_words = ["bad", "poor", "late", "delay", "worst", "broken", "slow", "rude", "refund"]
        score += sum(1 for w in positive_words if w in lower)
        score -= sum(1 for w in negative_words if w in lower)
        if ratings is not None and i < len(ratings) and not pd.isna(ratings.iloc[i]):
            r = float(ratings.iloc[i])
            score += 1 if r >= 4 else -1 if r <= 2 else 0
        if score > 0:
            labels.append("Positive")
        elif score < 0:
            labels.append("Negative")
        else:
            labels.append("Neutral")

    counts = Counter(labels)
    total = max(sum(counts.values()), 1)
    distribution = {
        "Positive": round(counts.get("Positive", 0) / total * 100, 1),
        "Neutral": round(counts.get("Neutral", 0) / total * 100, 1),
        "Negative": round(counts.get("Negative", 0) / total * 100, 1),
    }

    complaint_keywords = {
        "Delivery Delay": ["delay", "late", "shipping", "delivery"],
        "Product Quality": ["quality", "broken", "defect", "damaged"],
        "Customer Service": ["support", "rude", "service", "response"],
        "Pricing": ["expensive", "price", "costly", "overpriced"],
    }
    complaint_scores = {k: 0 for k in complaint_keywords}
    for text in texts:
        lower = text.lower()
        for theme, words in complaint_keywords.items():
            if any(w in lower for w in words):
                complaint_scores[theme] += 1
    main_complaint = max(complaint_scores, key=complaint_scores.get)
    if complaint_scores[main_complaint] == 0:
        main_complaint = "None detected"

    return {
        "distribution": distribution,
        "counts": dict(counts),
        "main_complaint": main_complaint,
        "sample_size": total,
        "average_rating": round(float(ratings.mean()), 2) if ratings is not None else None,
    }


def segment_customers(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    customers = frames.get("customers", pd.DataFrame())
    sales = _ensure_revenue(frames.get("sales", pd.DataFrame()))

    if customers.empty and not sales.empty:
        # Derive RFM-ish features from sales
        tmp = sales.copy()
        if "customer" not in tmp.columns and "customer_id" in tmp.columns:
            tmp["customer"] = tmp["customer_id"]
        if "customer" in tmp.columns and "revenue" in tmp.columns:
            if "date" in tmp.columns:
                tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
                latest = tmp["date"].max()
                grouped = tmp.groupby("customer").agg(
                    purchase_frequency=("revenue", "count"),
                    total_spending=("revenue", "sum"),
                    last_purchase_date=("date", "max"),
                )
                grouped["recency_days"] = (latest - grouped["last_purchase_date"]).dt.days.fillna(999)
            else:
                grouped = tmp.groupby("customer").agg(
                    purchase_frequency=("revenue", "count"),
                    total_spending=("revenue", "sum"),
                )
                grouped["recency_days"] = 30
            customers = grouped.reset_index().rename(columns={"customer": "customer_id"})

    if customers.empty:
        return {"message": "No customer data available for segmentation.", "segments": []}

    feature_cols = [c for c in ["purchase_frequency", "total_spending", "recency_days"] if c in customers.columns]
    if "average_order_value" not in customers.columns and {"total_spending", "purchase_frequency"}.issubset(
        customers.columns
    ):
        customers = customers.copy()
        customers["average_order_value"] = customers["total_spending"] / customers["purchase_frequency"].replace(
            0, np.nan
        )
        customers["average_order_value"] = customers["average_order_value"].fillna(0)
        feature_cols.append("average_order_value")

    if len(feature_cols) < 2 or len(customers) < 4:
        return {"message": "Need more customer records/features for clustering.", "segments": []}

    matrix = customers[feature_cols].fillna(0).astype(float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    n_clusters = min(4, len(customers))
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(scaled)
    customers = customers.copy()
    customers["cluster"] = labels

    # Label clusters heuristically
    cluster_stats = customers.groupby("cluster")[feature_cols].mean()
    segment_names = {}
    for cluster_id, row in cluster_stats.iterrows():
        spending = row.get("total_spending", 0)
        freq = row.get("purchase_frequency", 0)
        recency = row.get("recency_days", 0)
        if spending >= cluster_stats["total_spending"].median() and freq >= cluster_stats[
            "purchase_frequency"
        ].median():
            name = "High-Value Customers"
        elif recency >= cluster_stats.get("recency_days", pd.Series([0])).median() and freq <= cluster_stats[
            "purchase_frequency"
        ].median():
            name = "Inactive Customers"
        elif freq >= cluster_stats["purchase_frequency"].median():
            name = "Regular Customers"
        else:
            name = "Occasional Customers"
        segment_names[int(cluster_id)] = name

    segments = []
    for cluster_id, name in segment_names.items():
        subset = customers[customers["cluster"] == cluster_id]
        segments.append(
            {
                "segment": name,
                "count": int(len(subset)),
                "avg_spending": round(float(subset.get("total_spending", pd.Series([0])).mean()), 2),
                "avg_frequency": round(float(subset.get("purchase_frequency", pd.Series([0])).mean()), 2),
            }
        )

    # Deduplicate names if collisions
    seen = Counter()
    for seg in segments:
        seen[seg["segment"]] += 1
        if seen[seg["segment"]] > 1:
            seg["segment"] = f"{seg['segment']} ({seen[seg['segment']]})"

    return {
        "algorithm": "K-Means Clustering",
        "features": feature_cols,
        "segments": segments,
        "total_customers": int(len(customers)),
    }
