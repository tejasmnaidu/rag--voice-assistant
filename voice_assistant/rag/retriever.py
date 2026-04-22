from .embedder import get_embedding
from .vector_store import VectorStore

_default_vector_store = None

def init_retriever(vector_store_instance: VectorStore):
    """
    Initialize the retriever with a pre-configured VectorStore instance.
    This allows reuse of the same loaded index.
    """
    global _default_vector_store
    _default_vector_store = vector_store_instance

def init_retriever_from_path(path: str):
    """
    Convenience function to initialize the retriever by loading an index from a path.
    """
    global _default_vector_store
    store = VectorStore()
    store.load_index(path)
    _default_vector_store = store

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Convert the query to an embedding, fetch top-k relevant chunks from FAISS+BM25,
    and return the list of relevant text chunks with their indices.
    """
    if _default_vector_store is None:
        raise ValueError("Retriever has not been initialized. Call init_retriever or init_retriever_from_path first.")
        
    query_embedding = get_embedding(query)
    return _default_vector_store.similarity_search(query_embedding, query_text=query, top_k=top_k)
