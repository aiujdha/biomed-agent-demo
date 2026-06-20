from app.core.config import Settings, settings
from app.llm.client import FakeLLMClient, LLMClient, OpenAICompatibleClient
from app.rag.embeddings import HashEmbeddingModel
from app.rag.vector_store import FaissVectorStore


def create_llm_client(cfg: Settings) -> LLMClient:
    if cfg.llm_provider == "openai-compatible":
        if not cfg.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is required when LLM_PROVIDER=openai-compatible"
            )
        return OpenAICompatibleClient(
            api_key=cfg.llm_api_key,
            base_url=cfg.llm_base_url,
            model=cfg.llm_model,
        )
    return FakeLLMClient()


vector_store = FaissVectorStore()
embedding_model = HashEmbeddingModel()
llm_client = create_llm_client(settings)
