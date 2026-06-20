from app.rag.embeddings import HashEmbeddingModel
from app.rag.vector_store import FaissVectorStore

vector_store = FaissVectorStore()
embedding_model = HashEmbeddingModel()
