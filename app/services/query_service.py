import re

from app.llm.client import LLMClient
from app.rag.embeddings import EmbeddingModel
from app.rag.prompts import DISCLAIMER, RAG_SYSTEM_PROMPT
from app.rag.vector_store import FaissVectorStore, SearchResult
from app.schemas.query import QueryResponse, SourceChunk


STOP_WORDS = {
    "a",
    "an",
    "and",
    "is",
    "of",
    "the",
    "to",
    "what",
}


def _query_terms(question: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if token not in STOP_WORDS and len(token) > 2
    }


def _keyword_overlap_score(result: SearchResult, terms: set[str]) -> int:
    if not terms:
        return 0
    chunk_terms = set(re.findall(r"[a-zA-Z0-9]+", result.chunk.text.lower()))
    return len(terms & chunk_terms)


def _compact_context(text: str) -> str:
    return " ".join(text.split())


class QueryService:
    def __init__(
        self,
        vector_store: FaissVectorStore,
        embedding_model: EmbeddingModel,
        llm_client: LLMClient,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm_client = llm_client

    def retrieve_sources(self, question: str, top_k: int) -> list[SourceChunk]:
        query_vector = self.embedding_model.embed_query(question)
        fetch_k = max(top_k * 4, top_k)
        results = self.vector_store.search(query_vector=query_vector, top_k=fetch_k)
        terms = _query_terms(question)
        results = sorted(
            results,
            key=lambda result: (_keyword_overlap_score(result, terms), result.score),
            reverse=True,
        )[:top_k]
        sources = [
            SourceChunk(
                document_id=result.chunk.document_id,
                source=result.chunk.source,
                chunk_index=result.chunk.chunk_index,
                score=result.score,
                text=result.chunk.text,
                citation_id=f"{result.chunk.source}#{result.chunk.chunk_index}",
                excerpt=result.chunk.text[:240],
                metadata={
                    "document_id": result.chunk.document_id,
                    "source": result.chunk.source,
                    "chunk_index": result.chunk.chunk_index,
                },
            )
            for result in results
        ]
        return sources

    def answer(self, question: str, top_k: int) -> QueryResponse:
        sources = self.retrieve_sources(question=question, top_k=top_k)
        context = "\n".join(
            f"[citation:{source.source}#{source.chunk_index}] {_compact_context(source.text)}"
            for source in sources
        )
        answer = self.llm_client.generate(
            system_prompt=RAG_SYSTEM_PROMPT,
            user_prompt=f"Question: {question}\n\nContext:\n{context}",
        )
        return QueryResponse(answer=answer, sources=sources, disclaimer=DISCLAIMER)
