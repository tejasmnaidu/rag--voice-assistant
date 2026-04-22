import os
import pickle
import numpy as np
import faiss
from .embedder import get_embedding

class VectorStore:
    def __init__(self):
        """Initialize empty FAISS index properties, chunks, and BM25 index."""
        self.dimension = None
        self.index = None
        self.chunks = []
        self.bm25 = None

    def _build_bm25(self):
        if not self.chunks:
            self.bm25 = None
            return
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [
            doc.get("text", "").lower().split() if isinstance(doc, dict) else str(doc).lower().split() 
            for doc in self.chunks
        ]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def add_documents(self, list_of_documents: list[dict]):
        """Add text documents (with metadata), compute their embeddings, and store them."""
        if not list_of_documents:
            return
            
        embeddings_list = [get_embedding(doc["text"]) for doc in list_of_documents]
        
        # Dynamically initialize the index using the length of the first embedding if not initialized
        if self.index is None:
            self.dimension = len(embeddings_list[0])
            self.index = faiss.IndexFlatL2(self.dimension)
            
        embeddings_np = np.array(embeddings_list).astype('float32')
        self.index.add(embeddings_np)
        self.chunks.extend(list_of_documents)
        self._build_bm25()

    def save_index(self, path: str):
        """Save the FAISS index and corresponding chunks to disk."""
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}_chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    def load_index(self, path: str):
        """Load the FAISS index and corresponding chunks from disk."""
        faiss_path = f"{path}.faiss"
        pkl_path = f"{path}_chunks.pkl"
        
        if os.path.exists(faiss_path) and os.path.exists(pkl_path):
            self.index = faiss.read_index(faiss_path)
            self.dimension = self.index.d
            with open(pkl_path, "rb") as f:
                self.chunks = pickle.load(f)
            self._build_bm25()
        else:
            raise FileNotFoundError(f"Index files not found at {path}")

    def similarity_search(self, query_embedding: list[float], query_text: str = "", top_k: int = 5, distance_threshold: float = 1.25) -> list[dict]:
        """Search similar chunks using Hybrid FAISS+BM25 with Reciprocal Rank Fusion."""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # 1. FAISS Vector Search
        query_np = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_np, max(10, top_k * 2))
        
        faiss_ranks = {}
        for rank, (i, dist) in enumerate(zip(indices[0], distances[0])):
            if i != -1 and i < len(self.chunks) and dist <= distance_threshold:
                faiss_ranks[i] = rank
                
        # 2. BM25 Keyword Search
        bm25_ranks = {}
        if self.bm25 and query_text:
            tokenized_query = query_text.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
            top_bm25_indices = np.argsort(bm25_scores)[::-1][:max(10, top_k * 2)]
            for rank, i in enumerate(top_bm25_indices):
                if bm25_scores[i] > 0:
                    bm25_ranks[i] = rank
                    
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        rrf_scores = {}
        all_candidate_indices = set(faiss_ranks.keys()).union(set(bm25_ranks.keys()))
        
        for i in all_candidate_indices:
            score = 0.0
            if i in faiss_ranks:
                score += 1.0 / (rrf_k + faiss_ranks[i])
            if i in bm25_ranks:
                score += 1.0 / (rrf_k + bm25_ranks[i])
            rrf_scores[i] = score
            
        # 4. Sort and Extract Top K
        sorted_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]
        
        results = []
        for i in sorted_indices:
            doc = self.chunks[i]
            if isinstance(doc, dict):
                results.append({
                    "chunk": doc.get("text", ""), 
                    "metadata": doc.get("metadata", {}), 
                    "index": int(i),
                    "score": float(rrf_scores[i])
                })
            else:
                results.append({"chunk": doc, "metadata": {}, "index": int(i), "score": float(rrf_scores[i])})
                
        return results
