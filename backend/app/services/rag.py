from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks = []
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def simple_retrieve(question: str, documents: list[str], top_k: int = 3) -> list[str]:
    q_tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
    scored: list[tuple[int, str]] = []
    for doc in documents:
        tokens = set(re.findall(r"[a-z0-9]+", doc.lower()))
        score = len(q_tokens & tokens)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def load_user_documents(upload_dir: str | Path, user_id: int) -> list[str]:
    base = Path(upload_dir) / str(user_id) / "docs"
    if not base.exists():
        return []
    docs: list[str] = []
    for path in base.glob("*"):
        if path.suffix.lower() in {".txt", ".md"}:
            docs.extend(chunk_text(path.read_text(encoding="utf-8", errors="ignore")))
        elif path.suffix.lower() == ".pdf":
            # Prototype: store extracted text sidecar if present
            sidecar = path.with_suffix(".txt")
            if sidecar.exists():
                docs.extend(chunk_text(sidecar.read_text(encoding="utf-8", errors="ignore")))
    return docs


def rag_answer(question: str, documents: list[str], fallback_answer: str) -> dict[str, Any]:
    retrieved = simple_retrieve(question, documents)
    if not retrieved:
        return {
            "answer": fallback_answer,
            "sources": [],
            "mode": "analytics-only",
        }
    context = "\n---\n".join(retrieved)
    answer = (
        f"{fallback_answer}\n\nAdditional context from uploaded business documents:\n{context[:900]}"
    )
    return {"answer": answer, "sources": retrieved[:3], "mode": "rag"}
