from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


def _ensure_revenue(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.copy()
    if "revenue" not in df.columns and {"quantity", "price"}.issubset(df.columns):
        df["revenue"] = df["quantity"] * df["price"]
    return df


def forecast_sales(frames: dict[str, pd.DataFrame], periods: int = 1) -> dict[str, Any]:
    sales = _ensure_revenue(frames.get("sales", pd.DataFrame()))
    if sales.empty or "date" not in sales.columns or "revenue" not in sales.columns:
        return {
            "message": "Upload historical sales data with date and revenue/quantity-price to forecast.",
            "predictions": [],
        }

    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales = sales.dropna(subset=["date"])
    monthly = (
        sales.groupby(sales["date"].dt.to_period("M"))["revenue"].sum().sort_index().astype(float)
    )
    if len(monthly) < 3:
        return {
            "message": "Need at least 3 months of sales history for a reliable forecast.",
            "history": [{"period": str(i), "revenue": float(v)} for i, v in monthly.items()],
            "predictions": [],
        }

    X = np.arange(len(monthly)).reshape(-1, 1)
    y = monthly.values
    lr = LinearRegression().fit(X, y)
    rf = RandomForestRegressor(n_estimators=80, random_state=42).fit(X, y)

    predictions = []
    last_period = monthly.index[-1]
    for i in range(1, periods + 1):
        idx = len(monthly) + i - 1
        lr_pred = float(lr.predict([[idx]])[0])
        rf_pred = float(rf.predict([[idx]])[0])
        blended = max(0.0, (lr_pred * 0.35) + (rf_pred * 0.65))
        next_period = last_period + i
        predictions.append(
            {
                "period": str(next_period),
                "predicted_revenue": round(blended, 2),
                "model_breakdown": {
                    "linear_regression": round(max(0.0, lr_pred), 2),
                    "random_forest": round(max(0.0, rf_pred), 2),
                },
            }
        )

    return {
        "history": [{"period": str(i), "revenue": round(float(v), 2)} for i, v in monthly.items()],
        "predictions": predictions,
        "next_month_revenue": predictions[0]["predicted_revenue"] if predictions else None,
        "models_used": ["Linear Regression", "Random Forest"],
    }


def detect_anomalies(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    sales = _ensure_revenue(frames.get("sales", pd.DataFrame()))
    if not sales.empty and "date" in sales.columns and "revenue" in sales.columns:
        daily = sales.copy()
        daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
        daily = daily.dropna(subset=["date"])
        series = daily.groupby(daily["date"].dt.date)["revenue"].sum()
        if len(series) >= 8:
            values = series.values.reshape(-1, 1)
            model = IsolationForest(contamination=0.08, random_state=42)
            labels = model.fit_predict(values)
            mean = float(series.mean())
            std = float(series.std() or 1)
            for date, value, label in zip(series.index, series.values, labels):
                z = (float(value) - mean) / std
                if label == -1 or abs(z) >= 2.5:
                    findings.append(
                        {
                            "type": "sales",
                            "date": str(date),
                            "value": round(float(value), 2),
                            "expected_range": [
                                round(max(0.0, mean - 1.5 * std), 2),
                                round(mean + 1.5 * std, 2),
                            ],
                            "z_score": round(float(z), 2),
                            "status": "Anomaly Detected",
                            "message": f"Unusual daily sales of ₹{float(value):,.0f}",
                        }
                    )

    expenses = frames.get("expenses", pd.DataFrame())
    if not expenses.empty and "amount" in expenses.columns:
        amounts = expenses["amount"].astype(float)
        if len(amounts) >= 8:
            q1, q3 = amounts.quantile(0.25), amounts.quantile(0.75)
            iqr = q3 - q1
            upper = q3 + 1.5 * iqr
            for _, row in expenses[amounts > upper].head(10).iterrows():
                findings.append(
                    {
                        "type": "expense",
                        "date": str(row.get("date", "")),
                        "value": round(float(row["amount"]), 2),
                        "category": row.get("category", "Unknown"),
                        "status": "Anomaly Detected",
                        "message": f"Unexpected expense spike in {row.get('category', 'Unknown')}",
                    }
                )

    inventory = frames.get("inventory", pd.DataFrame())
    if not inventory.empty and {"current_stock", "reorder_level"}.issubset(inventory.columns):
        critical = inventory[inventory["current_stock"] <= inventory["reorder_level"] * 0.3]
        for _, row in critical.head(10).iterrows():
            findings.append(
                {
                    "type": "inventory",
                    "product": row.get("product", "Unknown"),
                    "value": int(row.get("current_stock", 0)),
                    "status": "Anomaly Detected",
                    "message": f"Sudden low stock risk for {row.get('product', 'Unknown')}",
                }
            )

    return {
        "count": len(findings),
        "anomalies": findings[:25],
        "techniques": ["Z-Score", "IQR", "Isolation Forest"],
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
