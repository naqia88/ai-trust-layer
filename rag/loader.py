# Import the PDF reader, embedding model, and persistent vector database client.
from pathlib import Path

import chromadb
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

from config import CHROMA_PATH, POLICY_PDF_PATH


# Keep the stored policy chunks separate from any future vector collections.
POLICY_COLLECTION_NAME = "company_policy"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


# Read all text pages from the company policy PDF.
def read_policy_pdf():
    reader = PdfReader(POLICY_PDF_PATH)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


# Divide policy text into overlapping sections for more focused retrieval.
def split_text_into_chunks(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - chunk_overlap

    return chunks


# Load the policy into Chroma so later checks can retrieve relevant rules.
def load_policy_vector_store():
    policy_text = read_policy_pdf()
    if not policy_text:
        raise ValueError("The company policy PDF does not contain readable text")

    chunks = split_text_into_chunks(policy_text)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = embedding_model.encode(chunks).tolist()

    # Create the local database folder before Chroma stores policy vectors there.
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=POLICY_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Replace prior chunks from this source so the latest policy is retrieved.
    collection.delete(where={"source": POLICY_PDF_PATH})
    collection.add(
        ids=[f"policy-{index}" for index in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {"source": POLICY_PDF_PATH, "chunk_number": index + 1}
            for index in range(len(chunks))
        ],
    )

    return collection
