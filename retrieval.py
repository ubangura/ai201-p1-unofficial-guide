from config import settings
from embed import get_collection
from models import ChunkMetadata, RetrievalResult


def retrieve(query: str, n_results: int = settings.N_RESULTS) -> list[RetrievalResult]:
    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"] or [[]]
    metadatas = results["metadatas"] or [[]]
    distances = results["distances"] or [[]]

    return [
        RetrievalResult(text=doc, metadata=ChunkMetadata(**metadata), distance=distance)
        for doc, metadata, distance in zip(documents[0], metadatas[0], distances[0])
    ]
