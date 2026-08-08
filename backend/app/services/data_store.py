from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.entities import Dataset
from app.services.preprocessing import detect_data_type, preprocess_dataframe, read_upload


def load_user_frames(db: Session, user_id: int) -> dict[str, pd.DataFrame]:
    datasets = (
        db.query(Dataset)
        .filter(Dataset.user_id == user_id, Dataset.status == "processed")
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )
    frames: dict[str, list[pd.DataFrame]] = {}
    for ds in datasets:
        path = Path(ds.file_path)
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        except Exception:
            continue
        frames.setdefault(ds.data_type, []).append(df)

    merged: dict[str, pd.DataFrame] = {}
    for dtype, parts in frames.items():
        merged[dtype] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    return merged


def process_and_persist_upload(
    db: Session,
    user_id: int,
    raw_path: Path,
    original_name: str,
    forced_type: str | None = None,
) -> Dataset:
    raw_df = read_upload(raw_path)
    data_type = forced_type or detect_data_type(raw_df, original_name)
    clean_df, meta = preprocess_dataframe(raw_df, data_type)

    processed_path = raw_path.with_suffix(".processed.csv")
    clean_df.to_csv(processed_path, index=False)

    dataset = Dataset(
        user_id=user_id,
        filename=original_name,
        data_type=data_type,
        file_path=str(processed_path),
        row_count=int(meta["processed_rows"]),
        columns_json=json.dumps(meta["columns"]),
        status="processed",
        notes="; ".join(meta["notes"]),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset
