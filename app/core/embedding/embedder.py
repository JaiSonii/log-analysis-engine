from sentence_transformers import SentenceTransformer
import torch

DEFAULT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

class Embedder:
    """
    Embedder Class for generating embeddings
    Uses sentence transformers
    """
    def __init__(self, model : str = DEFAULT_MODEL) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._model : SentenceTransformer = SentenceTransformer(model, device=self.device)

    def embed(self, document : str):
        return self._model.encode(document, convert_to_numpy=True)