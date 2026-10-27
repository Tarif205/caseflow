"""Load settings without displaying credentials or modifying the user's .env."""

import math
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(
    os.getenv("CASEFLOW_PROJECT_ROOT")
    or os.getenv("COPILOT_PROJECT_ROOT")  # Compatibility with existing deployment environments.
    or Path(__file__).resolve().parents[2]
)
LOCAL_DATABASE_URL = "postgresql://copilot:copilot-local-only@127.0.0.1:5432/copilot"


@dataclass(frozen=True)
class Settings:
    # Do not include database credentials in dataclass repr/logging.
    database_url: str = field(default=LOCAL_DATABASE_URL, repr=False)
    embed_provider: str = "fastembed"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_cache: Path = Path(".cache/fastembed")
    embed_dimension: int = 384
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:4b"
    llm_api_key: str = field(default="", repr=False)
    llm_timeout: float = 120.0
    min_similarity: float = 0.691243
    chunk_size: int = 800
    chunk_overlap: int = 120

    def __post_init__(self):
        if not math.isfinite(self.min_similarity) or not -1 <= self.min_similarity <= 1:
            raise ValueError("MIN_SIMILARITY must be between -1 and 1")
        if not math.isfinite(self.llm_timeout) or not 0 < self.llm_timeout <= 300:
            raise ValueError("LLM timeout must be positive and at most 300 seconds")
        if type(self.chunk_size) is not int or self.chunk_size < 1:
            raise ValueError("Chunk size must be a positive integer")
        if type(self.chunk_overlap) is not int or not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("Chunk overlap must be smaller than the chunk size")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        default_cache = (
            Path("G:/fastembed-cache") if os.name == "nt" else PROJECT_ROOT / ".cache/fastembed"
        )
        return cls(
            database_url=os.getenv("DATABASE_URL", "").strip() or LOCAL_DATABASE_URL,
            embed_provider=os.getenv("EMBED_PROVIDER", "fastembed"),
            embed_model=os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
            embed_cache=Path(os.getenv("FASTEMBED_CACHE_PATH", "").strip() or str(default_cache)),
            llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
            llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434").rstrip("/"),
            llm_model=os.getenv("LLM_MODEL", "qwen3:4b"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
            min_similarity=float(os.getenv("MIN_SIMILARITY", "0.691243")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
        )
