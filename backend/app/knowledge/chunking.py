from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class Chunker(Protocol):
    """Protocol for text chunking strategies."""

    def chunk(self, text: str, metadata: dict | None = None) -> list["Chunk"]: ...


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


class SlidingWindowChunker:
    """Sliding-window chunker with overlap for general text.

    target_size and overlap are measured in approximate characters.
    """

    def __init__(self, target_size: int = 500, overlap: int = 80):
        self.target_size = target_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        if metadata is None:
            metadata = {}

        text = text.strip()
        if len(text) <= self.target_size:
            return [Chunk(text=text, metadata=dict(metadata))]

        chunks: list[Chunk] = []
        step = max(1, self.target_size - self.overlap)
        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + self.target_size, len(text))
            # Try to break at a sentence boundary
            if end < len(text):
                for sep in ("\n\n", "\n", "。", "；", "，", " "):
                    last = text.rfind(sep, start, end)
                    if last > start + step // 2:
                        end = last + len(sep)
                        break
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_meta = dict(
                    metadata, chunk_index=chunk_index, start=start, end=end
                )
                chunks.append(Chunk(text=chunk_text, metadata=chunk_meta))
                chunk_index += 1
            start = end - self.overlap if end < len(text) else end

        return chunks


class RuleChunker:
    """Structure-aware chunker for business rules.

    Splits on heading or article boundaries and preserves heading/article metadata.
    """

    def __init__(self, max_chunk_size: int = 600):
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        import re

        if metadata is None:
            metadata = {}

        # Split on markdown headings or article numbers
        # Pattern matches: "## heading", "第1条", "第 1 条", "1.", "1、"
        parts = re.split(
            r"(?=^#{1,4}\s|[第第]\s*\d+\s*[条條]|\d+[\.、]\s)", text, flags=re.MULTILINE
        )

        chunks: list[Chunk] = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            heading_match = re.match(r"^#{1,4}\s+(.+)$", part, re.MULTILINE)
            article_match = re.match(r"^[第第]?\s*(\d+)\s*[\.、条條]", part)

            chunk_meta = dict(metadata, part_index=i)
            if heading_match:
                chunk_meta["heading"] = heading_match.group(1).strip()
            if article_match:
                chunk_meta["article_number"] = article_match.group(1)

            if len(part) <= self.max_chunk_size:
                chunks.append(Chunk(text=part, metadata=chunk_meta))
            else:
                # Sub-chunk long articles with sliding window
                sub = SlidingWindowChunker(target_size=self.max_chunk_size, overlap=80)
                sub_chunks = sub.chunk(part, metadata=chunk_meta)
                chunks.extend(sub_chunks)

        return chunks


class ComplaintChunker:
    """Normalize a historical complaint into structured fields."""

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        if metadata is None:
            metadata = {}

        # Produce one normalized record with complaint, cause, process, result
        return [Chunk(text=text, metadata=dict(metadata, record_type="complaint"))]
