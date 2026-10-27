"""Deterministic character windows with overlap and original text offsets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    position: int
    text: str
    start: int
    end: int


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[Chunk]:
    """Preserve text exactly; size and overlap are characters, not tokens.

    Windows may split words. This simple baseline makes experiments reproducible.
    Whitespace-only windows are omitted, and stored positions remain consecutive.
    """
    if type(chunk_size) is not int or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")
    if type(overlap) is not int or not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be an integer between zero and chunk_size - 1")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        window = text[start:end]
        if window.strip():
            chunks.append(Chunk(position=len(chunks), text=window, start=start, end=end))
        if end == len(text):
            break
        start = end - overlap
    return chunks
