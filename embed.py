from dataclasses import asdict

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
from config import settings
from models import DocumentChunks

_embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL
)
_chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_PATH))
_collection: Collection = _chroma_client.get_or_create_collection(
    name=settings.CHROMA_COLLECTION,
    embedding_function=_embedding_func,
    metadata={"hnsw:space": "cosine"},
)


def get_collection() -> Collection:
    return _collection


def embed_and_store(chunks: DocumentChunks) -> None:
    if not chunks:
        return
    _collection.add(
        documents=[chunk.text for chunk in chunks],
        metadatas=[asdict(chunk.metadata) for chunk in chunks],
        ids=[chunk.id for chunk in chunks],
    )
