from .embedder import Embedder
from .log_chunker import LogChunker
from .indexer import InMemoryIndexer, PersistentFaissIndexer

from typing_extensions import Union, Optional, Any
import os

class VectorPipeline:
    """
    A class to chunk, embed and index the log files
    """
    def __init__(self, indexer : Union[type[InMemoryIndexer], type[PersistentFaissIndexer]]) -> None:
        self._chunker = LogChunker()
        self._embedder = Embedder()
        self._indexer: Optional[Union[InMemoryIndexer, PersistentFaissIndexer]] = None
        self._indexer = self._init_indexer(indexer)

    def _init_indexer(self, indexer : Union[type[InMemoryIndexer], type[PersistentFaissIndexer]]):
        if isinstance(indexer, type):
            return indexer()
        else:
            return indexer

    def create_db(self, file_path : str):
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found on path : {file_path}")
        
        for chunk in self._chunker.invoke(file_path=file_path, window_size=200):
            emb = self._embedder.embed(chunk['text'])
            self._indexer.add(emb, chunk['text'], metadata=chunk['metadata'])

    def query(self, text: str, k=3) -> list[Any]:
        """
        Query the the vector Database
        Args:
            text : the query text to perform search
        Returns:
            A list of similar documents
        """
        q_emb = self._embedder.embed(text)
        return self._indexer.search(q_emb, k)

    def save(self, faiss_path="faiss.index", store_path="store.pkl"):
        """
        Save to local faiss db
        Args:
            faiss_path : path to faiss index
            store_path : path to faiss store pkl file
        """
        if not hasattr(self._indexer, 'save'):
            raise AttributeError('Indexer does not have save method')
        self._indexer.save(faiss_path, store_path)

    def load(self, faiss_path="faiss.index", store_path="store.pkl"):
        """
        load the local faiss db
        Args:
            faiss_path : path to faiss index
            store_path : path to faiss store pkl file
        """
        if not hasattr(self._indexer, 'load'):
            raise AttributeError('Indexer does not have load method')
        self._indexer.load(faiss_path, store_path)

if __name__ == "__main__":
    pipeline = VectorPipeline(PersistentFaissIndexer)
    pipeline.create_db(file_path='data/python.log')
    pipeline.save('data/faiss.index', 'data/store.pkl')