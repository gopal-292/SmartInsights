"""LangChain + OpenAI embeddings + pgVector RAG (PPT stack)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.rag import chunk_text, load_user_documents, simple_retrieve


def _pg_connection_string() -> str:
    from app.core.database import ACTIVE_DATABASE_URL

    return ACTIVE_DATABASE_URL


def _embeddings():
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
    )


def _collection_name(user_id: int) -> str:
    return f"{settings.rag_collection}_user_{user_id}"


def index_user_document(user_id: int, text: str, source: str) -> dict[str, Any]:
    """Embed and upsert document chunks into pgVector via LangChain."""
    if not settings.openai_enabled:
        return {
            "indexed": False,
            "mode": "local-fallback",
            "message": "OPENAI_API_KEY not set — document stored for keyword RAG only.",
        }

    chunks = chunk_text(text)
    if not chunks:
        return {"indexed": False, "mode": "langchain-pgvector", "chunks": 0}

    try:
        from langchain_core.documents import Document
        from langchain_community.vectorstores.pgvector import PGVector

        docs = [
            Document(
                page_content=chunk,
                metadata={"user_id": user_id, "source": source, "chunk": i},
            )
            for i, chunk in enumerate(chunks)
        ]
        PGVector.from_documents(
            documents=docs,
            embedding=_embeddings(),
            collection_name=_collection_name(user_id),
            connection_string=_pg_connection_string(),
            pre_delete_collection=False,
        )
        return {
            "indexed": True,
            "mode": "langchain-pgvector",
            "chunks": len(chunks),
            "collection": _collection_name(user_id),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "indexed": False,
            "mode": "langchain-pgvector",
            "error": str(exc),
            "message": "pgVector indexing failed; keyword RAG remains available.",
        }


def retrieve_context(user_id: int, question: str, k: int = 4) -> list[str]:
    """Retrieve relevant chunks from pgVector; fall back to keyword retrieval."""
    if settings.openai_enabled:
        try:
            from langchain_community.vectorstores.pgvector import PGVector

            store = PGVector(
                collection_name=_collection_name(user_id),
                connection_string=_pg_connection_string(),
                embedding_function=_embeddings(),
            )
            docs = store.similarity_search(question, k=k)
            hits = [d.page_content for d in docs if d.page_content.strip()]
            if hits:
                return hits
        except Exception:
            pass

    local_docs = load_user_documents(settings.upload_dir, user_id)
    return simple_retrieve(question, local_docs, top_k=k)


def answer_with_rag(user_id: int, question: str, analytics_fallback: str) -> dict[str, Any]:
    """Ground an answer with LangChain/OpenAI + pgVector (or analytics fallback)."""
    sources = retrieve_context(user_id, question)
    context = "\n---\n".join(sources[:4]) if sources else ""

    if settings.openai_enabled:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.2,
            )
            messages = [
                SystemMessage(
                    content=(
                        "You are SmartInsights, an AI business analyst. "
                        "Use the analytics summary and retrieved business-document context. "
                        "Explain root causes when possible and give actionable recommendations. "
                        "If context is insufficient, say what data is missing."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Business analytics summary:\n{analytics_fallback}\n\n"
                        f"Retrieved document context:\n{context or '(none)'}\n\n"
                        f"User question: {question}"
                    )
                ),
            ]
            result = llm.invoke(messages)
            answer = getattr(result, "content", None) or str(result)
            return {
                "answer": answer,
                "sources": sources[:3],
                "mode": "langchain-openai-pgvector" if sources else "langchain-openai",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "answer": f"{analytics_fallback}\n\n(OpenAI/LangChain unavailable: {exc})",
                "sources": sources[:3],
                "mode": "analytics-fallback",
            }

    if context:
        return {
            "answer": (
                f"{analytics_fallback}\n\nAdditional context from uploaded business documents "
                f"(keyword RAG — set OPENAI_API_KEY for LangChain + OpenAI):\n{context[:900]}"
            ),
            "sources": sources[:3],
            "mode": "keyword-rag",
        }

    return {
        "answer": analytics_fallback,
        "sources": [],
        "mode": "analytics-only",
    }


def index_path_for_user(user_id: int, path: Path, original_name: str) -> dict[str, Any]:
    if not path.exists():
        return {"indexed": False, "message": "File not found"}
    text = path.read_text(encoding="utf-8", errors="ignore")
    return index_user_document(user_id, text, original_name)
