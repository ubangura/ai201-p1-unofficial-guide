import uuid
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ChunkMetadata:
    professor: str
    course: str
    created: str
    type: Literal["review", "grade_distribution"]


def generate_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: ChunkMetadata
    id: str = field(init=False, default_factory=generate_id)


DocumentChunks = list[Chunk]
