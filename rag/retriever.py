# Import the local vector database client and the same embedding model used by the loader.
import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_PATH
from rag.loader import EMBEDDING_MODEL_NAME, POLICY_COLLECTION_NAME


# Retrieve the policy sections that are most relevant to a trust-check query.
def retrieve_policy_context(query, result_count=3):
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = embedding_model.encode(query).tolist()

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(
        name=POLICY_COLLECTION_NAME,
        embedding_function=None,
    )
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_count,
    )

    return results["documents"][0]
