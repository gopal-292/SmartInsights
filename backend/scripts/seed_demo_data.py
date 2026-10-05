"""Load demo CSVs into the database for end-to-end UI testing.

Creates (or reuses) a demo account, business profile, and uploads every file
from backend/sample_data/ so dashboard, ML, and RAG pages work immediately.

Run from the backend directory:
    .venv\\Scripts\\python.exe scripts\\seed_demo_data.py
    .venv\\Scripts\\python.exe scripts\\seed_demo_data.py --regenerate
    .venv\\Scripts\\python.exe scripts\\seed_demo_data.py --email you@example.com
"""

from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.entities import BusinessProfile, Dataset, User
from app.services.data_store import process_and_persist_upload

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"

TABULAR = {
    "sales.csv": "sales",
    "expenses.csv": "expenses",
    "inventory.csv": "inventory",
    "customers.csv": "customers",
    "reviews.csv": "reviews",
}

DEFAULT_EMAIL = "demo@test.com"
DEFAULT_PASSWORD = "demo12345"
DEFAULT_NAME = "Demo User"


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def get_or_create_user(db: Session, email: str, password: str, full_name: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        return user
    user = User(
        email=email.lower(),
        full_name=full_name,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_business_profile(db: Session, user: User) -> None:
    if db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first():
        return
    profile = BusinessProfile(
        user_id=user.id,
        business_name="SmartInsights Demo Store",
        business_type="Retail",
        industry="Grocery & FMCG",
        location="Pune, Maharashtra",
        currency="INR",
        business_size="SME",
    )
    db.add(profile)
    db.commit()


def clear_user_datasets(db: Session, user_id: int) -> None:
    rows = db.query(Dataset).filter(Dataset.user_id == user_id).all()
    for row in rows:
        path = Path(row.file_path)
        if path.exists():
            path.unlink(missing_ok=True)
        raw = path.with_suffix(path.suffix.replace(".processed", ""))
        if raw.exists() and raw != path:
            raw.unlink(missing_ok=True)
        db.delete(row)
    db.commit()

    user_dir = Path(settings.upload_dir) / str(user_id)
    if user_dir.exists():
        shutil.rmtree(user_dir, ignore_errors=True)


def seed_tabular(db: Session, user_id: int, filename: str, forced_type: str) -> Dataset:
    src = SAMPLE_DIR / filename
    if not src.exists():
        raise FileNotFoundError(f"Missing sample file: {src}")

    user_dir = Path(settings.upload_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = user_dir / f"{uuid.uuid4().hex}.csv"
    shutil.copy2(src, dest)

    return process_and_persist_upload(
        db=db,
        user_id=user_id,
        raw_path=dest,
        original_name=filename,
        forced_type=forced_type,
    )


def seed_document(db: Session, user_id: int, filename: str) -> Dataset:
    src = SAMPLE_DIR / filename
    if not src.exists():
        raise FileNotFoundError(f"Missing sample file: {src}")

    docs_dir = Path(settings.upload_dir) / str(user_id) / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_dir / f"{uuid.uuid4().hex}.txt"
    shutil.copy2(src, dest)

    dataset = Dataset(
        user_id=user_id,
        filename=filename,
        data_type="document",
        file_path=str(dest),
        row_count=0,
        columns_json="[]",
        status="stored",
        notes="Seeded demo policy document for RAG assistant",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SmartInsights demo data")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="Demo account email")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Demo account password")
    parser.add_argument("--name", default=DEFAULT_NAME, help="Demo account display name")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate CSVs in sample_data/ before seeding",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Remove existing uploads for this user before seeding",
    )
    args = parser.parse_args()

    if args.regenerate:
        from scripts.generate_sample_data import main as regenerate

        regenerate()

    if not SAMPLE_DIR.exists() or not any(SAMPLE_DIR.glob("*.csv")):
        print("No sample CSVs found — run with --regenerate first.")
        sys.exit(1)

    ensure_schema()
    db = SessionLocal()
    try:
        user = get_or_create_user(db, args.email, args.password, args.name)
        ensure_business_profile(db, user)

        if args.fresh:
            clear_user_datasets(db, user.id)
            print(f"Cleared previous uploads for {user.email}")

        loaded: list[str] = []
        for filename, data_type in TABULAR.items():
            ds = seed_tabular(db, user.id, filename, data_type)
            loaded.append(f"{ds.data_type}: {ds.row_count:,} rows")

        doc = seed_document(db, user.id, "business_policy.txt")
        loaded.append(f"{doc.data_type}: {doc.filename}")

        print("\nDemo data ready.")
        print(f"  Login: {args.email}")
        print(f"  Password: {args.password}")
        print(f"  Files in: {SAMPLE_DIR}")
        print("\nLoaded:")
        for line in loaded:
            print(f"  - {line}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
