from ingest import chunk_document, load_documents
from models import DocumentChunks

documents = load_documents()
all_chunks: list[DocumentChunks] = []

for doc in documents:
    all_chunks.extend(chunk_document(doc))
