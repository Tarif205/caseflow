"""Small embedding interface with lazy CPU inference and shape validation."""

from collections.abc import Callable, Sequence
from threading import Lock
from typing import Protocol

import numpy as np

from support_copilot.config import Settings


class Embeddings(Protocol):
    model_name: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def validate_vector(vector: Sequence[float], dimension: int = 384) -> list[float]:
    values = np.asarray(vector, dtype=np.float32)
    if values.shape != (dimension,):
        raise ValueError(f"Expected a vector with {dimension} dimensions")
    if not np.isfinite(values).all() or np.linalg.norm(values) == 0:
        raise ValueError("Embedding must contain finite values and have a nonzero norm")
    return values.tolist()


class FastEmbedAdapter:
    def __init__(self, settings: Settings, model_factory: Callable | None = None):
        if settings.embed_provider != "fastembed":
            raise ValueError("Only the fastembed embedding provider is supported")
        self.model_name = settings.embed_model
        self.dimension = settings.embed_dimension
        self.settings = settings
        self._model_factory = model_factory
        self._model = None
        self._init_lock = Lock()

    @property
    def model(self):
        with self._init_lock:
            return self._load_model()

    def _load_model(self):
        if self._model is None:
            # Avoid loading an ONNX model when importing modules or running fake-based tests.
            from fastembed import TextEmbedding

            factory = self._model_factory or TextEmbedding
            self._model = factory(
                model_name=self.model_name,
                cache_dir=str(self.settings.embed_cache),
                threads=2,
                providers=["CPUExecutionProvider"],
            )
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("Document text must not be empty")
        vectors = [
            validate_vector(v, self.dimension) for v in self.model.embed(list(texts), batch_size=16)
        ]
        if len(vectors) != len(texts):
            raise ValueError("The model returned an unexpected number of embeddings")
        return vectors

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Query must not be empty")
        # Use FastEmbed's query path so model-specific retrieval prefixes are applied.
        return validate_vector(next(iter(self.model.query_embed(text))), self.dimension)
