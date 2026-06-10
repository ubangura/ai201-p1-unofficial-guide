import json

from config import settings
from embed import get_collection
from groq import Groq
from ingest import _professors
from models import ChunkMetadata, QueryFilter, RetrievalResult

_groq = Groq(api_key=settings.GROQ_API_KEY.get_secret_value())


def _extract_filters(query: str) -> QueryFilter:
    content = f"""Extract metadata filters from this query for a RAG system about UMD CS professors.

Known professors — use the exact full name from this list, or null if none mentioned:
{json.dumps(_professors, indent=2)}

Query: {query}

Respond with JSON only — no explanation:
{{
  "professor": "<exact full name from the list above, or null>",
  "course": "<CMSC course code e.g. CMSC417, or null>",
  "type": "<'review' | 'grade_distribution' | null — use grade_distribution for grade/GPA/withdrawal/rate questions, review for student opinion questions>",
  "created": "<single specific semester as YYYY-MM, or null if a range or not mentioned — Spring=01, Summer=05, Fall=08>"
}}"""

    response = _groq.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    data = json.loads(response.choices[0].message.content)
    return QueryFilter(
        professor=data["professor"] or None,
        course=data["course"] or None,
        type=data["type"] or None,
        created=data["created"] or None,
    )


def _build_where(filters: QueryFilter) -> dict | None:
    conditions = [
        {field: {"$eq": value}}
        for field, value in [
            ("professor", filters.professor),
            ("course", filters.course),
            ("type", filters.type),
            ("created", filters.created),
        ]
        if value is not None
    ]
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def retrieve(query: str, n_results: int = settings.N_RESULTS) -> list[RetrievalResult]:
    collection = get_collection()

    if collection.count() == 0:
        return []

    filters = _extract_filters(query)
    where = _build_where(filters)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
        where=where,
    )

    documents = results["documents"] or [[]]
    metadatas = results["metadatas"] or [[]]
    distances = results["distances"] or [[]]

    if not documents[0] and where is not None:
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
