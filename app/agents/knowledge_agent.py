
from typing import Any, Optional, Protocol

from langchain_core.documents import Document

from app.graph.state import InvestmentState


# ---------------------------------------------------------
# 1. Vector store interface
# ---------------------------------------------------------

class KnowledgeVectorStore(Protocol):
    """
    Contract expected from the vector store.

    The actual PostgreSQL + pgvector implementation
    will be created in app/services/vector_store.py.
    """

    def similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None
    ) -> list[tuple[Document, float]]:
        ...


# ---------------------------------------------------------
# 2. Knowledge Agent
# ---------------------------------------------------------

class KnowledgeAgent:
    """
    Retrieves relevant information from approved documents.

    This agent retrieves evidence only. It does not generate
    financial advice or make suitability decisions.
    """

    def __init__(
        self,
        vector_store: KnowledgeVectorStore,
        top_k: int = 5,
        minimum_relevance_score: float = 0.30
    ):

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        if not 0.0 <= minimum_relevance_score <= 1.0:
            raise ValueError(
                "minimum_relevance_score must be between 0 and 1."
            )

        self.vector_store = vector_store
        self.top_k = top_k
        self.minimum_relevance_score = minimum_relevance_score

    # -----------------------------------------------------
    # 3. Retrieve relevant knowledge
    # -----------------------------------------------------

    def retrieve(self, state: InvestmentState) -> dict:

        query = state.get("query", "").strip()

        if not query:
            raise ValueError("Customer query cannot be empty.")

        market = state.get("market", "UK")

        # Only approved documents for the requested market
        # should be returned by the vector-store implementation.
        metadata_filter = {
            "status": "approved",
            "market": market
        }

        try:

            search_results = (
                self.vector_store
                .similarity_search_with_relevance_scores(
                    query=query,
                    k=self.top_k,
                    filter=metadata_filter
                )
            )

        except Exception:
            # Avoid putting database or provider error details
            # into customer-visible state.
            return {
                "retrieved_documents": [],
                "citations": [],
                "knowledge_status": "unavailable",
                "audit_events": [
                    "Knowledge retrieval failed."
                ]
            }

        # -------------------------------------------------
        # 4. Process and validate search results
        # -------------------------------------------------

        retrieved_documents = []
        citations = []

        for document, relevance_score in search_results:

            if not isinstance(document, Document):
                continue

            if relevance_score < self.minimum_relevance_score:
                continue

            metadata = document.metadata or {}

            # Defensive validation. The vector-store filter
            # must also enforce these conditions at query time.
            if metadata.get("status") != "approved":
                continue

            if metadata.get("market") != market:
                continue

            content = document.page_content.strip()

            if not content:
                continue

            document_id = metadata.get("document_id")
            source = metadata.get("source")

            # Do not invent document IDs or source references.
            if not document_id or not source:
                continue

            retrieved_documents.append({
                "document_id": str(document_id),
                "content": content,
                "source": str(source),
                "relevance_score": float(relevance_score)
            })

            citation = f"{source}#{document_id}"

            if citation not in citations:
                citations.append(citation)

        # -------------------------------------------------
        # 5. Return results to LangGraph state
        # -------------------------------------------------

        if not retrieved_documents:

            return {
                "retrieved_documents": [],
                "citations": [],
                "knowledge_status": "no_relevant_documents",
                "audit_events": [
                    "Knowledge retrieval completed: no relevant "
                    "approved documents found."
                ]
            }

        return {
            "retrieved_documents": retrieved_documents,
            "citations": citations,
            "knowledge_status": "found",
            "audit_events": [
                f"Knowledge retrieval completed: "
                f"{len(retrieved_documents)} documents retrieved."
            ]
        }


# ---------------------------------------------------------
# 6. LangGraph node
# ---------------------------------------------------------

_knowledge_agent: Optional[KnowledgeAgent] = None


def knowledge_agent_node(state: InvestmentState) -> dict:
    """
    LangGraph entry point.

    The vector store is injected when the graph is built.
    This prevents hidden database initialisation inside
    the agent node.
    """

    if _knowledge_agent is None:
        raise RuntimeError(
            "KnowledgeAgent has not been configured. "
            "Inject a KnowledgeAgent before running this node."
        )

    return _knowledge_agent.retrieve(state)


def configure_knowledge_agent(agent: KnowledgeAgent) -> None:
    """
    Configure the Knowledge Agent once during application startup.
    """

    global _knowledge_agent
    _knowledge_agent = agent
