"""Time-series forecasting engine with walk-forward model selection.

The public entry point is :func:`build_forecast`, which turns raw sales rows into
a monthly revenue series, scores a set of candidate models by backtesting them on
the user's own history, and forecasts forward with the winner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge

# 80% prediction interval
Z_80 = 1.2816

Predictor = Callable[[np.ndarray, int], np.ndarray]


@dataclass
class Candidate:
    """A forecasting model that maps a history window to `horizon` future values."""

    name: str
    label: str
    min_points: int
    predict: Predictor


def _clean(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)


def _non_negative(values: np.ndarray) -> np.ndarray:
    return np.clip(values, 0.0, None)


# --------------------------------------------------------------------------- #
# Candidate models
# --------------------------------------------------------------------------- #


def _drift(y: np.ndarray, horizon: int) -> np.ndarray:
    """Random walk with drift: last observation plus the average period change."""
    y = _clean(y)
    step = float(np.mean(np.diff(y))) if len(y) > 1 else 0.0
    return _non_negative(y[-1] + step * np.arange(1, horizon + 1))


def _holt_damped(y: np.ndarray, horizon: int) -> np.ndarray:
    """Holt's linear trend with damping; smoothing parameters chosen by grid search."""
    y = _clean(y)
    best: tuple[float, np.ndarray] | None = None

    for alpha in (0.2, 0.4, 0.6, 0.8):
        for beta in (0.05, 0.15, 0.3):
            for phi in (0.8, 0.9, 0.98):
                level = float(y[0])
                trend = float(y[1] - y[0]) if len(y) > 1 else 0.0
                sse = 0.0
                for actual in y[1:]:
                    forecast = level + phi * trend
                    sse += (actual - forecast) ** 2
                    prev_level = level
                    level = alpha * actual + (1 - alpha) * forecast
                    trend = beta * (level - prev_level) + (1 - beta) * phi * trend
                if best is None or sse < best[0]:
                    damping = np.cumsum(phi ** np.arange(1, horizon + 1))
                    best = (sse, level + damping * trend)

    assert best is not None
    return _non_negative(best[1])


def _seasonal_design(index: np.ndarray, harmonics: int) -> np.ndarray:
    """Fourier terms for a 12-period (annual) cycle."""
    terms = []
    for k in range(1, harmonics + 1):
        terms.append(np.sin(2 * np.pi * k * index / 12.0))
        terms.append(np.cos(2 * np.pi * k * index / 12.0))
    return np.column_stack(terms)


def _ridge_trend(y: np.ndarray, horizon: int) -> np.ndarray:
    y = _clean(y)
    t = np.arange(len(y), dtype=float).reshape(-1, 1)
    model = Ridge(alpha=1.0).fit(t, y)
    future = np.arange(len(y), len(y) + horizon, dtype=float).reshape(-1, 1)
    return _non_negative(model.predict(future))


def _ridge_seasonal(y: np.ndarray, horizon: int) -> np.ndarray:
    """Linear trend plus annual seasonality, so the model can extrapolate both."""
    y = _clean(y)
    harmonics = 2 if len(y) >= 24 else 1
    t = np.arange(len(y), dtype=float)
    design = np.column_stack([t, _seasonal_design(t, harmonics)])
    model = Ridge(alpha=1.0).fit(design, y)

    future_t = np.arange(len(y), len(y) + horizon, dtype=float)
    future = np.column_stack([future_t, _seasonal_design(future_t, harmonics)])
    return _non_negative(model.predict(future))


def _lag_matrix(values: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    rows, targets = [], []
    for i in range(lags, len(values)):
        rows.append(values[i - lags : i][::-1])
        targets.append(values[i])
    return np.asarray(rows, dtype=float), np.asarray(targets, dtype=float)


def _gbm_hybrid(y: np.ndarray, horizon: int) -> np.ndarray:
    """Linear trend for extrapolation, gradient boosting for the residual pattern.

    Trees cannot extrapolate beyond their training range, so they are never given
    the raw time index. They only learn the recurring shape left over after the
    trend is removed.
    """
    y = _clean(y)
    lags = 3
    t = np.arange(len(y), dtype=float).reshape(-1, 1)
    trend_model = Ridge(alpha=1.0).fit(t, y)
    residual = y - trend_model.predict(t)

    features, targets = _lag_matrix(residual, lags)
    seasonal = _seasonal_design(np.arange(lags, len(residual), dtype=float), 1)
    design = np.column_stack([features, seasonal])
    residual_model = GradientBoostingRegressor(
        n_estimators=200, learning_rate=0.05, max_depth=2, random_state=42
    ).fit(design, targets)

    history = list(residual)
    predictions = []
    for step in range(horizon):
        position = len(y) + step
        window = np.asarray(history[-lags:][::-1], dtype=float)
        row = np.concatenate([window, _seasonal_design(np.array([float(position)]), 1)[0]])
        next_residual = float(residual_model.predict(row.reshape(1, -1))[0])
        history.append(next_residual)
        trend = float(trend_model.predict(np.array([[float(position)]]))[0])
        predictions.append(trend + next_residual)

    return _non_negative(np.asarray(predictions))


def _forest_differenced(y: np.ndarray, horizon: int) -> np.ndarray:
    """Random forest on period-over-period changes, then re-integrated.

    Differencing is what makes a forest usable here: it learns how much the series
    moves rather than an absolute level it could never predict outside its range.
    """
    y = _clean(y)
    lags = 3
    deltas = np.diff(y)
    features, targets = _lag_matrix(deltas, lags)
    model = RandomForestRegressor(
        n_estimators=300, min_samples_leaf=1, random_state=42, n_jobs=-1
    ).fit(features, targets)

    history = list(deltas)
    level = float(y[-1])
    predictions = []
    for _ in range(horizon):
        window = np.asarray(history[-lags:][::-1], dtype=float).reshape(1, -1)
        delta = float(model.predict(window)[0])
        history.append(delta)
        level += delta
        predictions.append(level)

    return _non_negative(np.asarray(predictions))


CANDIDATES: list[Candidate] = [
    Candidate("drift", "Random Walk with Drift", 3, _drift),
    Candidate("holt_damped", "Damped Holt Exponential Smoothing", 4, _holt_damped),
    Candidate("ridge_trend", "Ridge Linear Trend", 3, _ridge_trend),
    Candidate("ridge_seasonal", "Ridge Trend + Fourier Seasonality", 14, _ridge_seasonal),
    Candidate("gbm_hybrid", "Trend + Gradient Boosting Residuals", 10, _gbm_hybrid),
    Candidate("forest_differenced", "Random Forest on Differences", 11, _forest_differenced),
]


# --------------------------------------------------------------------------- #
# Backtesting
# --------------------------------------------------------------------------- #


def _score_errors(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    errors = predicted - actual
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    denominator = np.where(np.abs(actual) < 1e-9, np.nan, np.abs(actual))
    mape = float(np.nanmean(np.abs(errors) / denominator) * 100) if np.isfinite(denominator).any() else float("nan")
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": None if np.isnan(mape) else round(mape, 2),
    }


def _backtest(y: np.ndarray, candidate: Candidate) -> dict[str, Any] | None:
    """Expanding-window, one-step-ahead validation on the user's own history."""
    n = len(y)
    min_train = max(candidate.min_points, int(np.ceil(n * 0.6)))
    if n - min_train < 2:
        return None

    actual, predicted = [], []
    for cut in range(min_train, n):
        try:
            step = candidate.predict(y[:cut], 1)
        except Exception:
            return None
        if not np.all(np.isfinite(step)):
            return None
        predicted.append(float(step[0]))
        actual.append(float(y[cut]))

    actual_arr = np.asarray(actual)
    predicted_arr = np.asarray(predicted)
    metrics = _score_errors(actual_arr, predicted_arr)

    # Skill against a naive last-value baseline: 1.0 = perfect, <=0 = no better than naive.
    naive = np.asarray([float(y[cut - 1]) for cut in range(min_train, n)])
    naive_mae = float(np.mean(np.abs(naive - actual_arr)))
    metrics["skill_vs_naive"] = (
        round(1 - (metrics["mae"] / naive_mae), 3) if naive_mae > 1e-9 else None
    )

    if len(actual_arr) >= 2:
        actual_direction = np.sign(np.diff(actual_arr))
        predicted_direction = np.sign(predicted_arr[1:] - actual_arr[:-1])
        matched = actual_direction == predicted_direction
        metrics["direction_accuracy"] = round(float(np.mean(matched)) * 100, 1)
    else:
        metrics["direction_accuracy"] = None

    metrics["folds"] = len(actual_arr)
    metrics["residual_std"] = round(float(np.std(predicted_arr - actual_arr)), 2)
    return metrics


def _confidence(metrics: dict[str, Any] | None, history_length: int) -> str:
    if metrics is None:
        return "low"
    mape = metrics.get("mape")
    if history_length < 8 or mape is None:
        return "low"
    if mape <= 12 and history_length >= 12:
        return "high"
    if mape <= 25:
        return "medium"
    return "low"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def monthly_revenue_series(sales: pd.DataFrame) -> pd.Series:
    """Aggregate sales rows into a gap-free monthly revenue series."""
    if sales.empty or "date" not in sales.columns:
        return pd.Series(dtype=float)

    df = sales.copy()
    if "revenue" not in df.columns and {"quantity", "price"}.issubset(df.columns):
        df["revenue"] = df["quantity"] * df["price"]
    if "revenue" not in df.columns:
        return pd.Series(dtype=float)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return pd.Series(dtype=float)

    series = df.groupby(df["date"].dt.to_period("M"))["revenue"].sum().sort_index().astype(float)
    if len(series) > 1:
        # Months with zero sales are real signal, so fill the calendar rather than skip them.
        full_index = pd.period_range(series.index[0], series.index[-1], freq="M")
        series = series.reindex(full_index, fill_value=0.0)
    return series


def build_forecast(sales: pd.DataFrame, periods: int = 6) -> dict[str, Any]:
    """Forecast monthly revenue, selecting the model that scores best on backtests."""
    series = monthly_revenue_series(sales)
    history = [
        {"period": str(period), "revenue": round(float(value), 2)}
        for period, value in series.items()
    ]

    if len(series) < 3:
        return {
            "message": (
                "Need at least 3 months of dated sales history to model trends. "
                f"Found {len(series)}."
            ),
            "history": history,
            "predictions": [],
            "evaluation": [],
        }

    y = _clean(series.values)
    evaluation: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        if len(y) < candidate.min_points:
            continue
        metrics = _backtest(y, candidate)
        if metrics is None:
            continue
        evaluation.append({"model": candidate.label, "key": candidate.name, **metrics})

    scored = sorted(evaluation, key=lambda row: row["mae"])
    if scored:
        winner_key = scored[0]["key"]
        winner_metrics: dict[str, Any] | None = scored[0]
    else:
        # Too little history to validate; fall back to the most conservative model.
        winner_key = "holt_damped" if len(y) >= 4 else "ridge_trend"
        winner_metrics = None

    winner = next(c for c in CANDIDATES if c.name == winner_key)
    values = winner.predict(y, periods)

    sigma = float(winner_metrics["residual_std"]) if winner_metrics else float(np.std(np.diff(y)))
    last_period = series.index[-1]
    recent_average = float(np.mean(y[-3:]))

    predictions = []
    for step in range(1, periods + 1):
        point = float(values[step - 1])
        # Uncertainty compounds with horizon.
        margin = Z_80 * sigma * np.sqrt(step)
        predictions.append(
            {
                "period": str(last_period + step),
                "predicted_revenue": round(point, 2),
                "lower_bound": round(max(0.0, point - margin), 2),
                "upper_bound": round(point + margin, 2),
                "change_vs_recent_avg": (
                    round((point - recent_average) / recent_average * 100, 1)
                    if recent_average > 0
                    else None
                ),
            }
        )

    horizon_total = sum(p["predicted_revenue"] for p in predictions)
    return {
        "history": history,
        "predictions": predictions,
        "next_month_revenue": predictions[0]["predicted_revenue"],
        "horizon_total": round(horizon_total, 2),
        "selected_model": winner.label,
        "selection_basis": (
            f"Lowest backtest MAE across {len(evaluation)} candidate models"
            if scored
            else "Default model - history too short to backtest"
        ),
        "accuracy": winner_metrics,
        "evaluation": [
            {k: v for k, v in row.items() if k != "key"} for row in scored
        ],
        "confidence": _confidence(winner_metrics, len(y)),
        "models_used": [winner.label],
        "validation": "Expanding-window walk-forward, one step ahead",
    }
