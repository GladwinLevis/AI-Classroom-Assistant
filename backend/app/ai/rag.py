import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from app.core.config import settings
from app.ai.config import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class VectorIndexManager:
    """
    VectorIndexManager handles sentence embedding creation and local FAISS vector store indexes.
    Implements standard vector calculations for AI search and RAG contexts.
    """
    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        index_dir: str = settings.FAISS_INDEX_PATH
    ):
        self.model_name = model_name
        self.index_dir = index_dir
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Load embedding model lazily to speed up initial load
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazily load SentenceTransformer model."""
        if self._model is None:
            logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Encodes standard list of text strings into vector arrays."""
        return self.model.encode(texts, convert_to_numpy=True)

    def create_and_save_index(self, index_name: str, texts: List[str], metadatas: List[Dict[str, Any]]) -> str:
        """
        Creates a new FAISS flat index, embeds the texts, and stores the index to disk.
        """
        embeddings = self.get_embeddings(texts)
        dimension = embeddings.shape[1]
        
        # Create standard L2 similarity flat index
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype("float32"))
        
        index_path = os.path.join(self.index_dir, f"{index_name}.faiss")
        faiss.write_index(index, index_path)
        
        # Placeholder: metadata mapping configuration could be saved to json alongside the index
        logger.info(f"Successfully wrote FAISS index of size {index.ntotal} to: {index_path}")
        return index_path

    def search_index(self, index_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Loads local index and runs standard L2 proximity query vectors.
        """
        index_path = os.path.join(self.index_dir, f"{index_name}.faiss")
        if not os.path.exists(index_path):
            logger.warning(f"Requested vector index {index_path} not found.")
            return []

        index = faiss.read_index(index_path)
        query_vector = self.get_embeddings([query]).astype("float32")
        
        distances, indices = index.search(query_vector, top_k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            results.append({
                "index_ref": int(idx),
                "distance": float(dist)
            })
        return results
