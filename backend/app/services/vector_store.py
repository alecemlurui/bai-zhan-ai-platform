"""
services/vector_store.py

向量库存储抽象层（默认 Chroma）。
提供集合级 upsert、query、delete 与集合管理接口。
"""

from __future__ import annotations

from typing import Any

from ..config import SETTINGS


class VectorStoreError(Exception):
    """向量库操作异常。"""


class ChromaVectorStore:
    """Chroma 向量库存储实现。"""

    def __init__(self, path: str | None = None):
        self.path = path or SETTINGS.VECTOR_DB_PATH
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from chromadb import PersistentClient
            except ImportError as exc:
                raise VectorStoreError(
                    "chromadb package is required for vector store"
                ) from exc
            self._client = PersistentClient(path=self.path)
        return self._client

    def get_or_create_collection(self, name: str) -> Any:
        client = self._get_client()
        return client.get_or_create_collection(name)

    def upsert(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        if len(ids) != len(documents) or len(ids) != len(embeddings):
            raise VectorStoreError("ids/documents/embeddings length mismatch")
        coll = self.get_or_create_collection(collection_name)
        coll.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in ids],
        )

    def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]] | None = None,
        query_texts: list[str] | None = None,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        coll = self.get_or_create_collection(collection_name)
        kwargs: dict[str, Any] = {
            "n_results": n_results,
            "include": ["metadatas", "documents", "distances"],
        }
        if where:
            kwargs["where"] = where
        if query_embeddings:
            kwargs["query_embeddings"] = query_embeddings
        elif query_texts:
            kwargs["query_texts"] = query_texts
        else:
            raise VectorStoreError(
                "Either query_embeddings or query_texts must be provided"
            )
        return coll.query(**kwargs)

    def delete(self, collection_name: str, ids: list[str]) -> None:
        coll = self.get_or_create_collection(collection_name)
        coll.delete(ids=ids)

    def list_collections(self) -> list[str]:
        client = self._get_client()
        return [c.name for c in client.list_collections()]


class MockVectorStore:
    """测试/无模型环境下的伪向量库。"""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict[str, Any]]] = {}

    def get_or_create_collection(self, name: str) -> "MockVectorStoreCollection":
        return MockVectorStoreCollection(self, name)

    def upsert(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        self._data.setdefault(collection_name, {})
        for i, doc_id in enumerate(ids):
            self._data[collection_name][doc_id] = {
                "document": documents[i],
                "embedding": embeddings[i],
                "metadata": (metadatas or [{} for _ in ids])[i],
            }

    def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]] | None = None,
        query_texts: list[str] | None = None,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        collection = self._data.get(collection_name, {})
        if not collection:
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        import random

        items = list(collection.items())
        if where:
            items = [
                (k, v)
                for k, v in items
                if all(v["metadata"].get(key) == value for key, value in where.items())
            ]
        selected = items[:n_results]
        return {
            "ids": [[k for k, _ in selected]],
            "documents": [[v["document"] for _, v in selected]],
            "metadatas": [[v["metadata"] for _, v in selected]],
            "distances": [[random.random() for _ in selected]],
        }

    def delete(self, collection_name: str, ids: list[str]) -> None:
        collection = self._data.get(collection_name, {})
        for doc_id in ids:
            collection.pop(doc_id, None)

    def list_collections(self) -> list[str]:
        return list(self._data.keys())


class MockVectorStoreCollection:
    def __init__(self, store: MockVectorStore, name: str):
        self.store = store
        self.name = name


def get_vector_store() -> ChromaVectorStore | MockVectorStore:
    if SETTINGS.VECTOR_DB_TYPE == "mock":
        return MockVectorStore()
    return ChromaVectorStore()
