from fastapi import APIRouter

from app.core.container import embedding_model, llm_client, vector_store
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest) -> QueryResponse:
    service = QueryService(
        vector_store=vector_store,
        embedding_model=embedding_model,
        llm_client=llm_client,
    )
    return service.answer(question=request.question, top_k=request.top_k)