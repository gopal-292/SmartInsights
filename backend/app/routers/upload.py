import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import Dataset, User
from app.models.schemas import DatasetOut
from app.services.data_store import process_and_persist_upload

router = APIRouter(prefix="/upload", tags=["Data Upload"])

ALLOWED = {".csv", ".xlsx", ".xls", ".txt", ".md", ".pdf"}


@router.post("", response_model=DatasetOut)
async def upload_dataset(
    file: UploadFile = File(...),
    data_type: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=400, detail="Supported formats: CSV, Excel, TXT, MD, PDF")

    user_dir = Path(settings.upload_dir) / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Documents go to docs for RAG; tabular data is processed into analytics store
    if suffix in {".txt", ".md", ".pdf"}:
        docs_dir = user_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        dest = docs_dir / f"{uuid.uuid4().hex}{suffix}"
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        if suffix in {".txt", ".md"}:
            text_path = dest
        else:
            text_path = dest.with_suffix(".txt")
            text_path.write_text(
                f"Uploaded document: {file.filename}\n"
                "PDF text extraction can be enhanced in the full model. "
                "Add a .txt sidecar for RAG in the prototype.",
                encoding="utf-8",
            )
        dataset = Dataset(
            user_id=current_user.id,
            filename=file.filename,
            data_type="document",
            file_path=str(text_path if suffix == ".pdf" else dest),
            row_count=0,
            columns_json="[]",
            status="stored",
            notes="Stored for RAG assistant",
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        # LangChain + OpenAI embeddings → pgVector (PPT RAG stack)
        from app.services.langchain_rag import index_path_for_user

        index_meta = index_path_for_user(
            current_user.id,
            Path(dataset.file_path),
            file.filename,
        )
        if index_meta.get("indexed"):
            dataset.notes = (
                f"Indexed into pgVector via LangChain "
                f"({index_meta.get('chunks', 0)} chunks)"
            )
            dataset.status = "indexed"
            db.commit()
            db.refresh(dataset)
        elif index_meta.get("message"):
            dataset.notes = f"Stored for RAG · {index_meta['message']}"
            db.commit()
            db.refresh(dataset)
        return DatasetOut.model_validate(dataset)

    dest = user_dir / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        dataset = process_and_persist_upload(
            db=db,
            user_id=current_user.id,
            raw_path=dest,
            original_name=file.filename,
            forced_type=data_type if data_type and data_type != "auto" else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DatasetOut.model_validate(dataset)


@router.get("/datasets", response_model=list[DatasetOut])
def list_datasets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Dataset)
        .filter(Dataset.user_id == current_user.id)
        .order_by(Dataset.uploaded_at.desc())
        .all()
    )
    return [DatasetOut.model_validate(r) for r in rows]


@router.delete("/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    path = Path(row.file_path)
    if path.exists():
        path.unlink(missing_ok=True)
    db.delete(row)
    db.commit()
    return {"message": "Dataset deleted"}
