"""
api/rag.py

RAG 检索 API。
"""

from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import get_current_active_user
from ..models import User
from ..services.rag import build_rag_prompt_context, ingest_material, retrieve_context

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/ingest/{material_id}")
async def ingest(
    material_id: int,
    text: str,
    metadata: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_active_user),
):
    result = await ingest_material(
        material_id=material_id,
        text=text,
        metadata=metadata,
    )
    return result


@router.get("/search")
async def search(
    q: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_active_user),
):
    contexts = await retrieve_context(query=q, top_k=top_k)
    return {"query": q, "top_k": top_k, "contexts": contexts}


@router.get("/context")
async def context(
    q: str,
    top_k: int = 5,
    max_chars: int = 2000,
    current_user: User = Depends(get_current_active_user),
):
    prompt_context = await build_rag_prompt_context(
        query=q,
        top_k=top_k,
        max_chars=max_chars,
    )
    return {"query": q, "context": prompt_context}
