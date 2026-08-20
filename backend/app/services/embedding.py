"""
services/embedding.py

本地 ONNX Embedding 服务（基于 Xenova/bge-small-zh-v1.5 或兼容 BERT 模型）。
提供同步/异步文本编码接口，输出已归一化的向量。
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from ..config import SETTINGS


class EmbeddingError(Exception):
    """Embedding 服务异常。"""


class OnnxBgeEmbedder:
    """基于 ONNX Runtime 的 BGE Embedding 编码器。"""

    def __init__(
        self,
        model_path: str | Path | None = None,
        tokenizer_path: str | Path | None = None,
        max_length: int = 512,
        normalize: bool = True,
        use_fp16: bool = False,
    ):
        self.model_path = self._resolve_path(
            model_path, SETTINGS.EMBEDDING_MODEL_PATH, "onnx/model.onnx"
        )
        self.tokenizer_path = self._resolve_path(
            tokenizer_path, SETTINGS.EMBEDDING_TOKENIZER_PATH, "tokenizer.json"
        )
        self.max_length = max_length
        self.normalize = normalize
        self.use_fp16 = use_fp16
        self._tokenizer: Any | None = None
        self._session: Any | None = None

    @staticmethod
    def _resolve_path(
        explicit: str | Path | None,
        settings_path: str,
        default_suffix: str,
    ) -> Path:
        if explicit:
            return Path(explicit)
        if settings_path:
            base = Path(settings_path)
            if base.is_dir():
                return base / default_suffix
            return base
        raise EmbeddingError(
            "Missing embedding model path. Set EMBEDDING_MODEL_PATH "
            f"or pass model_path. Expected suffix: {default_suffix}"
        )

    def _load_tokenizer(self) -> Any:
        if self._tokenizer is None:
            try:
                from tokenizers import Tokenizer
            except ImportError as exc:
                raise EmbeddingError(
                    "tokenizers package is required for local ONNX embedding"
                ) from exc
            self._tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
            self._tokenizer.enable_truncation(max_length=self.max_length)
            self._tokenizer.enable_padding(length=self.max_length)
        return self._tokenizer

    def _load_session(self) -> Any:
        if self._session is None:
            try:
                import onnxruntime as ort
            except ImportError as exc:
                raise EmbeddingError(
                    "onnxruntime package is required for local ONNX embedding"
                ) from exc

            model_file = self.model_path
            if not model_file.exists():
                # 自动回退到目录中的第一个 .onnx 文件
                if model_file.suffix.lower() != ".onnx" and model_file.is_dir():
                    candidates = sorted(model_file.glob("*.onnx"))
                    if candidates:
                        model_file = candidates[0]
            if not model_file.exists():
                raise EmbeddingError(f"ONNX model not found: {self.model_path}")

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            available = ort.get_available_providers()
            providers = [p for p in providers if p in available] or [
                "CPUExecutionProvider"
            ]
            self._session = ort.InferenceSession(
                str(model_file),
                sess_options,
                providers=providers,
            )
        return self._session

    def _encode_sync(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)

        tokenizer = self._load_tokenizer()
        session = self._load_session()

        encoded = tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.array([e.type_ids for e in encoded], dtype=np.int64)

        # 部分模型可能不需要 token_type_ids；动态获取输入名
        input_names = {inp.name for inp in session.get_inputs()}
        inputs: dict[str, np.ndarray] = {}
        if "input_ids" in input_names:
            inputs["input_ids"] = input_ids
        if "attention_mask" in input_names:
            inputs["attention_mask"] = attention_mask
        if "token_type_ids" in input_names:
            inputs["token_type_ids"] = token_type_ids

        outputs = session.run(None, inputs)
        last_hidden_state = outputs[0]  # (batch, seq_len, hidden_size)

        mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
        sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
        counts = np.clip(
            np.sum(attention_mask, axis=1, keepdims=True), a_min=1e-9, a_max=None
        )
        embeddings = sum_embeddings / counts.astype(np.float32)

        if self.normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, a_min=1e-12, a_max=None)

        return embeddings.astype(np.float32)

    async def encode(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, self._encode_sync, texts)
        return embeddings.tolist()

    @property
    def vector_size(self) -> int:
        session = self._load_session()
        return session.get_outputs()[0].shape[-1]


class MockEmbedder:
    """测试/无模型环境下的伪 Embedding 编码器，返回固定维度的随机向量。"""

    def __init__(self, vector_size: int = 512):
        self.vector_size = vector_size

    async def encode(self, texts: list[str]) -> list[list[float]]:
        rng = np.random.default_rng(seed=42)
        return (
            rng.normal(size=(len(texts), self.vector_size)).astype(np.float32).tolist()
        )


@lru_cache()
def get_embedder() -> OnnxBgeEmbedder | MockEmbedder:
    if SETTINGS.EMBEDDING_MOCK:
        return MockEmbedder(vector_size=SETTINGS.EMBEDDING_VECTOR_SIZE or 512)
    return OnnxBgeEmbedder()
