"""
services/rag.py

RAG 管道：文本分块 -> Embedding -> 向量库存储 / 检索 -> 上下文拼接。
"""

from __future__ import annotations

from typing import Any

from ..config import SETTINGS
from .embedding import get_embedder
from .vector_store import get_vector_store

DEFAULT_COLLECTION = "materials"


def split_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """按字符窗口切分文本，保留重叠。"""
    if not text or chunk_size <= 0:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start += step
    return chunks


async def ingest_material(
    material_id: int,
    text: str,
    metadata: dict[str, Any] | None = None,
    collection: str = DEFAULT_COLLECTION,
) -> dict[str, Any]:
    """将素材文本分块、嵌入并写入向量库。"""
    if not text.strip():
        return {"chunks": 0, "ids": []}

    embedder = get_embedder()
    vector_store = get_vector_store()

    chunks = split_text(
        text,
        chunk_size=SETTINGS.RAG_CHUNK_SIZE,
        overlap=SETTINGS.RAG_CHUNK_OVERLAP,
    )
    embeddings = await embedder.encode(chunks)

    ids = [f"{collection}:{material_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "material_id": material_id,
            "chunk_index": i,
            "collection": collection,
            **(metadata or {}),
        }
        for i in range(len(chunks))
    ]

    vector_store.upsert(
        collection_name=collection,
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {"chunks": len(chunks), "ids": ids}


async def retrieve_context(
    query: str,
    collection: str = DEFAULT_COLLECTION,
    top_k: int | None = None,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """根据查询检索最相关的文本块，返回带分数的上下文列表。"""
    top_k = top_k or SETTINGS.RAG_TOP_K
    embedder = get_embedder()
    vector_store = get_vector_store()

    query_embeddings = await embedder.encode([query])
    results = vector_store.query(
        collection_name=collection,
        query_embeddings=query_embeddings,
        n_results=top_k,
        where=where,
    )

    contexts = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        contexts.append(
            {
                "id": doc_id,
                "content": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": distances[i] if i < len(distances) else 0.0,
            }
        )
    return contexts


async def build_rag_prompt_context(
    query: str,
    collection: str = DEFAULT_COLLECTION,
    top_k: int | None = None,
    where: dict[str, Any] | None = None,
    max_chars: int = 2000,
) -> str:
    """检索上下文并拼接成 prompt 可用的字符串。"""
    contexts = await retrieve_context(query, collection, top_k, where)
    if not contexts:
        return ""

    lines = []
    total = 0
    for ctx in contexts:
        line = f"[参考 {len(lines) + 1}]\n{ctx['content']}\n"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


async def delete_material_chunks(
    material_id: int,
    collection: str = DEFAULT_COLLECTION,
) -> None:
    """删除素材在向量库中的所有 chunk。"""
    vector_store = get_vector_store()
    # 通过 metadata 过滤查询出 ids 后删除
    results = vector_store.query(
        collection_name=collection,
        query_texts=[""],
        n_results=10000,
        where={"material_id": material_id},
    )
    ids = results.get("ids", [[]])[0]
    if ids:
        vector_store.delete(collection_name=collection, ids=ids)
