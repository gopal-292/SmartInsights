from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATA_TYPE_HINTS = {
    "sales": ["quantity", "price", "product", "order", "revenue", "region", "customer"],
    "expenses": ["expense", "category", "amount", "description", "cost"],
    "inventory": ["stock", "reorder", "supplier", "inventory"],
    "customers": ["customer_id", "purchase_frequency", "total_spending", "recency", "last_purchase"],
    "reviews": ["review", "rating", "sentiment", "feedback", "comment"],
    "financial": ["revenue", "profit", "assets", "liabilities", "expenses"],
}

COLUMN_ALIASES = {
    "date": [
        "date",
        "order_date",
        "orderdate",
        "transaction_date",
        "invoice_date",
        "review_date",
    ],
    "product": [
        "product",
        "product_name",
        "productline",
        "product_line",
        "productcode",
        "product_code",
        "item",
        "sku_name",
    ],
    "quantity": [
        "quantity",
        "qty",
        "units",
        "units_sold",
        "quantityordered",
        "quantity_ordered",
    ],
    "price": ["price", "unit_price", "selling_price", "priceeach", "price_each"],
    "customer": [
        "customer",
        "customer_name",
        "customername",
        "client",
        "contactname",
        "contact_name",
    ],
    "customer_id": ["customer_id", "cust_id", "client_id"],
    "region": [
        "region",
        "city",
        "location",
        "state",
        "country",
        "territory",
    ],
    "order_id": [
        "order_id",
        "ordernumber",
        "order_number",
        "invoice_id",
        "transaction_id",
    ],
    "category": [
        "category",
        "expense_category",
        "product_category",
        "deal_size",
        "dealsize",
    ],
    "amount": ["amount", "expense_amount", "cost", "value"],
    "description": ["description", "notes", "remarks", "addressline1", "address_line1"],
    "current_stock": ["current_stock", "stock", "quantity_on_hand", "inventory"],
    "reorder_level": ["reorder_level", "reorder", "min_stock"],
    "supplier": ["supplier", "vendor"],
    "stock_value": ["stock_value", "inventory_value"],
    "purchase_frequency": ["purchase_frequency", "frequency", "orders_count"],
    "total_spending": ["total_spending", "total_spent", "lifetime_value", "ltv"],
    "last_purchase_date": ["last_purchase_date", "last_purchase", "last_order_date"],
    "rating": ["rating", "stars", "score"],
    "review_text": ["review_text", "review", "comment", "feedback"],
    "revenue": ["revenue", "sales_revenue", "income", "sales"],
    "expenses": ["expenses", "total_expenses", "costs"],
    "profit": ["profit", "net_profit"],
}


def _normalize_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: _normalize_col(c) for c in df.columns})

    # Ensure unique names after normalization (e.g. City + CITY)
    seen: dict[str, int] = {}
    unique_cols: list[str] = []
    for col in df.columns:
        if col not in seen:
            seen[col] = 0
            unique_cols.append(col)
        else:
            seen[col] += 1
            unique_cols.append(f"{col}_{seen[col]}")
    df.columns = unique_cols

    reverse_map: dict[str, str] = {}
    used_canonical: set[str] = set()
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in df.columns:
            used_canonical.add(canonical)
            continue
        for alias in aliases:
            if alias in df.columns and canonical not in used_canonical:
                reverse_map[alias] = canonical
                used_canonical.add(canonical)
                break
    return df.rename(columns=reverse_map)


def detect_data_type(df: pd.DataFrame, filename: str = "") -> str:
    cols = set(df.columns.astype(str))
    name = filename.lower()
    for dtype, hints in DATA_TYPE_HINTS.items():
        if dtype in name:
            return dtype
    scores: dict[str, int] = {}
    for dtype, hints in DATA_TYPE_HINTS.items():
        scores[dtype] = sum(1 for h in hints if any(h in c for c in cols))
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "sales"


def read_csv_robust(path: Path) -> pd.DataFrame:
    """Read CSV files from Excel/Windows that are often CP1252, not UTF-8."""
    from io import StringIO

    raw = Path(path).read_bytes()
    text: str | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("cp1252", errors="replace")

    # Normalize newlines and drop NUL bytes that break parsers
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("CSV file is empty.")

    first_line = text.split("\n", 1)[0]
    sep = ","
    for candidate in (",", ";", "\t", "|"):
        if first_line.count(candidate) > first_line.count(sep):
            sep = candidate

    try:
        return pd.read_csv(StringIO(text), sep=sep, engine="python")
    except Exception as exc:
        # Last resort: let pandas guess the separator
        try:
            return pd.read_csv(StringIO(text), sep=None, engine="python")
        except Exception as exc2:
            raise ValueError(
                "Could not parse CSV. Re-save in Excel as "
                "'CSV UTF-8 (Comma delimited)' and try again."
            ) from exc2


def read_upload(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return read_csv_robust(path)
    raise ValueError(f"Unsupported file type: {suffix}. Use CSV or Excel.")


def preprocess_dataframe(df: pd.DataFrame, data_type: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    notes: list[str] = []
    original_rows = len(df)
    df = standardize_columns(df)
    before_dupes = len(df)
    df = df.drop_duplicates()
    removed_dupes = before_dupes - len(df)
    if removed_dupes:
        notes.append(f"Removed {removed_dupes} duplicate rows")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "last_purchase_date" in df.columns:
        df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"], errors="coerce")

    numeric_candidates = [
        "quantity",
        "price",
        "amount",
        "current_stock",
        "reorder_level",
        "stock_value",
        "purchase_frequency",
        "total_spending",
        "rating",
        "revenue",
        "expenses",
        "profit",
        "assets",
        "liabilities",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    missing_before = int(df.isna().sum().sum())
    if data_type == "sales":
        if {"quantity", "price"}.issubset(df.columns) and "revenue" not in df.columns:
            df["revenue"] = df["quantity"].fillna(0) * df["price"].fillna(0)
            notes.append("Derived revenue = quantity × price")
        for col in ["quantity", "price", "revenue"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        if "product" in df.columns:
            df["product"] = df["product"].fillna("Unknown")
        if "region" in df.columns:
            df["region"] = df["region"].fillna("Unknown")
    elif data_type == "expenses":
        if "amount" in df.columns:
            df["amount"] = df["amount"].fillna(0)
        if "category" in df.columns:
            df["category"] = df["category"].fillna("Uncategorized")
    elif data_type == "inventory":
        for col in ["current_stock", "reorder_level", "stock_value"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        if {"current_stock", "reorder_level"}.issubset(df.columns):
            df["status"] = np.where(
                df["current_stock"] <= df["reorder_level"], "Reorder Required", "OK"
            )
            notes.append("Derived inventory status from reorder level")
    elif data_type == "reviews":
        if "rating" in df.columns:
            df["rating"] = df["rating"].fillna(df["rating"].median())
        if "review_text" in df.columns:
            df["review_text"] = df["review_text"].fillna("")
    else:
        df = df.fillna(0 if data_type == "financial" else "Unknown")

    missing_after = int(df.isna().sum().sum())
    if missing_before:
        notes.append(f"Handled {missing_before - missing_after} missing values")

    # Simple IQR outlier flag for amount/revenue
    outlier_col = "revenue" if "revenue" in df.columns else "amount" if "amount" in df.columns else None
    if outlier_col and df[outlier_col].notna().sum() > 8:
        q1 = df[outlier_col].quantile(0.25)
        q3 = df[outlier_col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[outlier_col] < lower) | (df[outlier_col] > upper)
        df["is_outlier"] = mask
        notes.append(f"Flagged {int(mask.sum())} outliers on {outlier_col}")

    notes.append(f"Processed {original_rows} → {len(df)} rows as {data_type}")
    meta = {
        "original_rows": original_rows,
        "processed_rows": len(df),
        "columns": list(df.columns),
        "notes": notes,
        "data_type": data_type,
    }
    return df, meta
