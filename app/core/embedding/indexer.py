import faiss
import numpy as np
from typing import List, Dict, Optional
import pickle

class InMemoryIndexer:
    def __init__(self, dim: Optional[int] = None) -> None:
        """
        dim: embedding dimension (pass from model or infer on first insert)
        """
        self.dim = dim
        self._index: Optional[faiss.IndexFlatL2] = None
        self._documents: List[str] = []
        self._metadata: List[Dict] = []

    def _init_index(self, dim: int):
        self.dim = dim
        self._index = faiss.IndexFlatL2(dim)

    def add(self, embedding: np.ndarray, document: str, metadata: Dict):
        """
        Add single vector and store doc + metadata
        """
        embedding = embedding.astype('float32')

        if self._index is None:
            self._init_index(len(embedding))

        self._index.add(np.array([embedding]))
        self._documents.append(document)
        self._metadata.append(metadata)

    def search(self, query_embedding: np.ndarray, k: int = 3):
        """
        Returns top-k results with doc + metadata + distance
        """
        query_embedding = query_embedding.astype('float32')
        distances, ids = self._index.search(np.array([query_embedding]), k)

        results = []
        for rank, idx in enumerate(ids[0]):
            results.append({
                "document": self._documents[idx],
                "metadata": self._metadata[idx],
                "distance": float(distances[0][rank])
            })
        return results

class PersistentFaissIndexer:
    def __init__(self, dim: Optional[int] = None):
        self._index: Optional[faiss.IndexFlatL2] = None
        self.dim = dim
        self._documents: List[str] = []
        self._metadata: List[Dict] = []

    def _init_index(self, dim: int):
        self.dim = dim
        self._index = faiss.IndexFlatL2(dim)

    def add(self, embedding: np.ndarray, document: str, metadata: Dict):
        embedding = embedding.astype("float32")

        if self._index is None:
            self._init_index(len(embedding))

        self._index.add(np.array([embedding]))
        self._documents.append(document)
        self._metadata.append(metadata)

    def search(self, embedding: np.ndarray, k: int = 3):
        embedding = embedding.astype("float32")
        distances, ids = self._index.search(np.array([embedding]), k)
        results = []
        for rank, idx in enumerate(ids[0]):
            results.append({
                "document": self._documents[idx],
                "metadata": self._metadata[idx],
                "distance": float(distances[0][rank])
            })
        return results

    def save(self, faiss_path="faiss.index", store_path="store.pkl"):
        faiss.write_index(self._index, faiss_path)
        with open(store_path, "wb") as f:
            pickle.dump({
                "documents": self._documents,
                "metadata": self._metadata,
                "dim": self.dim
            }, f)

    def load(self, faiss_path="faiss.index", store_path="store.pkl"):
        self._index = faiss.read_index(faiss_path)
        with open(store_path, "rb") as f:
            store = pickle.load(f)
        self._documents = store["documents"]
        self._metadata = store["metadata"]
        self.dim = store["dim"]

__all__ = ['InMemoryIndexer', 'PersistentFaissIndexer']