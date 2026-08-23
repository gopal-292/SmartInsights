"""Render executive reports to PDF via Jinja2 + WeasyPrint.

WeasyPrint needs native libraries (Pango, Cairo, GObject). On Windows install:
  winget install -e --id tschoonj.GTKForWindows
Then restart the terminal/backend so PATH picks up the GTK bin folder.
Docs: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


class ReportGenerationError(RuntimeError):
    """Raised when HTML rendering or PDF conversion fails."""


def _format_inr(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"₹{amount:,.0f}"


def _format_pct(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{amount:.1f}%"


def _ensure_gtk_on_path() -> None:
    """Best-effort: add common Windows GTK bin paths so WeasyPrint can load DLLs."""
    if os.name != "nt":
        return
    candidates = [
        Path(r"C:\Program Files\GTK3-Runtime Win64\bin"),
        Path(r"C:\Program Files\GTK3-Runtime\bin"),
        Path(r"C:\GTK3-Runtime Win64\bin"),
        Path(os.environ.get("GTK_BIN", "")),
    ]
    path = os.environ.get("PATH", "")
    for folder in candidates:
        if folder and folder.exists() and str(folder) not in path:
            os.environ["PATH"] = str(folder) + os.pathsep + path
            path = os.environ["PATH"]


def _jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["inr"] = _format_inr
    env.filters["pct"] = _format_pct
    return env


def render_report_html(payload: dict[str, Any]) -> str:
    """Render the executive report payload to HTML with Jinja2."""
    context = {
        **payload,
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        "business": payload.get("business"),
        "kpis": payload.get("kpis") or {},
        "executive_summary": payload.get("executive_summary") or {},
        "sales": payload.get("sales") or {},
        "expenses": payload.get("expenses") or {},
        "profitability": payload.get("profitability") or {},
        "inventory": payload.get("inventory") or {},
        "sentiment": payload.get("sentiment") or {},
        "segments": payload.get("segments") or {},
        "forecast": payload.get("forecast") or {},
        "anomalies": payload.get("anomalies") or {},
        "recommendations": payload.get("recommendations") or {},
    }
    try:
        return _jinja_env().get_template("report.html").render(**context)
    except Exception as exc:  # noqa: BLE001
        raise ReportGenerationError(f"Failed to render report HTML: {exc}") from exc


def generate_report_pdf(payload: dict[str, Any]) -> bytes:
    """Convert a report payload into PDF bytes via WeasyPrint."""
    html = render_report_html(payload)
    _ensure_gtk_on_path()

    try:
        from weasyprint import HTML
    except Exception as exc:  # ImportError or DLL load failures on Windows
        raise ReportGenerationError(
            "WeasyPrint is unavailable. Install Python deps (`pip install weasyprint`) "
            "and native GTK libraries. On Windows run: "
            "`winget install -e --id tschoonj.GTKForWindows`, then restart the backend. "
            f"Details: {exc}"
        ) from exc

    try:
        pdf = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
    except Exception as exc:  # noqa: BLE001
        raise ReportGenerationError(
            "PDF generation failed. On Windows, missing GTK/Pango libraries are a "
            "common cause — install `tschoonj.GTKForWindows` and restart. "
            f"Details: {exc}"
        ) from exc

    if not pdf:
        raise ReportGenerationError("PDF generation returned empty output.")
    return pdf
