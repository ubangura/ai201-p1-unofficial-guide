import json
from collections import Counter, defaultdict
from datetime import datetime

import planetterp
from config import settings
from models import Chunk, ChunkMetadata, DocumentChunks
from transformers import AutoTokenizer

_professors = [
    "Aaron Kyei-Asare",
    "Anwar Mamat",
    "Aravind Srinivasan",
    "Anna Evtushenko",
    "Christopher Kauffman",
    "Cliff Bakalian",
    "Clyde Kruskal",
    "Daniel Abadi",
    "Dave Levin",
    "David Van Horn",
    "Elias Gonzalez",
    "Evan Golub",
    "Herve Franceschi",
    "Ilchul Yoon",
    "James Purtilo",
    "Jennifer Manly",
    "John Aloimonos",
    "Justin Wyss-Gallifent",
    "Larry Herman",
    "Laxman Dhulipala",
    "Leonidas Lampropoulos",
    "Marine Carpuat",
    "Michael Marsh",
    "Michelle Mazurek",
    "Mihai Pop",
    "Mohammad Hajiaghayi",
    "Mohammad Nayeem Teli",
    "Nelson Padua-Perez",
    "Pedram Sadeghian",
    "Robert Patro",
    "Samrat Bhattacharjee",
    "Stevens Miller",
    "Sujeong Kim",
    "Thomas Goldstein",
    "William Regli",
    "Zhicheng Liu",
]

_tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
)

_CHUNK_SIZE = 200
_CHUNK_OVERLAP = 50

_grade_keys = [
    "A+",
    "A",
    "A-",
    "B+",
    "B",
    "B-",
    "C+",
    "C",
    "C-",
    "D+",
    "D",
    "D-",
    "F",
    "W",
    "Other",
]

_metadata_keys = {"course", "professor", "semester", "section"}


def fetch_professor_reviews() -> None:
    for professor in _professors:
        name_prefix = professor.replace(" ", "_").lower()

        with open(f"{settings.DOCS_PATH}/{name_prefix}_reviews.json", "w") as f:
            professor_data = planetterp.professor(name=professor, reviews=True)
            json.dump(obj=professor_data, fp=f, indent=2)


def fetch_professor_grades() -> None:
    for professor in _professors:
        name_prefix = professor.replace(" ", "_").lower()

        professor_data = planetterp.professor(name=professor)
        courses: set[str] = set(professor_data["courses"])

        grades: list[dict] = [
            grade
            for course in courses
            if course.startswith("CMSC")
            for grade in planetterp.grades(course=course, professor=professor)
            if isinstance(grade, dict)
        ]

        with open(f"{settings.DOCS_PATH}/{name_prefix}_grades.json", "w") as f:
            json.dump(obj=grades, fp=f, indent=2)


def load_documents() -> list[dict]:
    documents: list[dict] = []

    for path in settings.DOCS_PATH.glob("*.json"):
        with open(path) as f:
            data = json.load(fp=f)

        if path.stem.endswith("_reviews"):
            documents.append({"type": "reviews", "reviews": data["reviews"]})
        else:
            documents.append({"type": "grades", "grades": data})

    return documents


def chunk_document(document: dict) -> DocumentChunks:
    if document["type"] == "reviews":
        return _chunk_reviews(document)
    return _chunk_grades(document)


def _chunk_reviews(document: dict) -> DocumentChunks:
    reviews: list[dict] = document["reviews"]

    chunks: list[Chunk] = []

    for review in reviews:
        metadata = ChunkMetadata(
            professor=review["professor"],
            course=review["course"] or "",
            created=_normalize_date(review["created"]),
            type="review",
        )

        text = review["review"].strip()
        if not text:
            continue

        if _token_count(text) <= _CHUNK_SIZE:
            chunks.append(Chunk(text=text, metadata=metadata))
            continue

        paragraphs = [
            paragraph.strip()
            for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n\n")
            if paragraph.strip()
        ]
        for paragraph in paragraphs:
            if _token_count(paragraph) <= _CHUNK_SIZE:
                chunks.append(Chunk(text=paragraph, metadata=metadata))
            else:
                tokens = _tokenizer.tokenize(paragraph)

                start = 0
                while start < len(tokens):
                    chunk_text = _tokenizer.convert_tokens_to_string(
                        tokens[start : start + _CHUNK_SIZE]
                    )
                    chunks.append(Chunk(text=chunk_text, metadata=metadata))
                    start = start + _CHUNK_SIZE - _CHUNK_OVERLAP

    return chunks


def _chunk_grades(document: dict) -> DocumentChunks:
    grades: list[dict] = document["grades"]
    grade_distributions: dict[ChunkMetadata, Counter] = defaultdict(Counter)

    for grade in grades:
        key = ChunkMetadata(
            professor=grade["professor"],
            course=grade["course"] or "",
            created=_normalize_date(grade["semester"]),
            type="grade_distribution",
        )

        grade_counts = {k: v for k, v in grade.items() if k not in _metadata_keys}
        grade_distributions[key].update(grade_counts)

    chunks: list[Chunk] = []
    for metadata, counter in grade_distributions.items():
        distribution = ", ".join(f"{counter[grade]} {grade}" for grade in _grade_keys)

        chunks.append(
            Chunk(
                text=f"{metadata.course} taught by {metadata.professor} in {metadata.created}: {distribution}",
                metadata=metadata,
            )
        )

    return chunks


def _token_count(text: str) -> int:
    return len(_tokenizer.tokenize(text))


def _normalize_date(date_str: str) -> str:
    if len(date_str) == 6:  # semester format e.g. "202008"
        return datetime.strptime(date_str, "%Y%m").strftime("%Y-%m")

    # ISO 8601 e.g. "2013-05-12T03:56:00Z"
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
