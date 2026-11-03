
import uuid
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings


# ---------------------------------------------------------
# 1. Vector Store Service
# ---------------------------------------------------------

class PostgresVectorStore:
    """
    PostgreSQL + pgvector implementation.

    Responsibilities:
    - Generate document embeddings.
    - Store document chunks and metadata.
    - Perform cosine similarity search.
    - Return LangChain Document objects and relevance scores.
    """

    def __init__(
        self,
        engine: Optional[Engine] = None,
        embeddings=None,
        embedding_dimensions: int = 1536
    ):

        if engine is None:
            engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )

        self.engine = engine
        self.embedding_dimensions = embedding_dimensions

        # Allow an embedding model to be injected during tests.
        if embeddings is None:

            api_key = settings.openai_api_key.get_secret_value()

            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is missing from .env."
                )

            embeddings = OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                api_key=api_key
            )

        self.embeddings = embeddings

    # -----------------------------------------------------
    # 2. Initialise PostgreSQL schema
    # -----------------------------------------------------

    def initialize_schema(self) -> None:
        """
        Create the pgvector extension and document table.

        The PostgreSQL user must have permission to create
        the extension if it does not already exist.
        """

        create_extension = text("""
            CREATE EXTENSION IF NOT EXISTS vector;
        """)

        create_table = text(f"""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id UUID PRIMARY KEY,
                document_id VARCHAR(150) NOT NULL,
                chunk_id VARCHAR(150) NOT NULL,
                content TEXT NOT NULL,
                source VARCHAR(500) NOT NULL,
                market VARCHAR(20) NOT NULL,
                status VARCHAR(30) NOT NULL,
                document_version VARCHAR(50),
                embedding VECTOR({self.embedding_dimensions}) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),

                CONSTRAINT uq_knowledge_document_chunk
                    UNIQUE (document_id, chunk_id)
            );
        """)

        create_index = text("""
            CREATE INDEX IF NOT EXISTS
            idx_knowledge_chunks_market_status
            ON knowledge_chunks (market, status);
        """)

        with self.engine.begin() as connection:
            connection.execute(create_extension)
            connection.execute(create_table)
            connection.execute(create_index)

    # -----------------------------------------------------
    # 3. Convert embedding list to pgvector format
    # -----------------------------------------------------

    def _to_vector_literal(self, vector: list[float]) -> str:

        if len(vector) != self.embedding_dimensions:
            raise ValueError(
                f"Expected {self.embedding_dimensions} dimensions, "
                f"received {len(vector)}."
            )

        return "[" + ",".join(
            f"{float(value):.10f}" for value in vector
        ) + "]"

    # -----------------------------------------------------
    # 4. Ingest document chunks
    # -----------------------------------------------------

    def add_documents(
        self,
        documents: list[Document]
    ) -> int:
        """
        Generate embeddings and store approved document chunks.

        Required metadata:
        - document_id
        - chunk_id
        - source
        - market
        - status

        Only approved documents are accepted.
        """

        if not documents:
            return 0

        contents = []
        records = []

        for document in documents:

            if not isinstance(document, Document):
                raise TypeError(
                    "Every input must be a LangChain Document."
                )

            content = document.page_content.strip()
            metadata = document.metadata or {}

            if not content:
                raise ValueError("Document content cannot be empty.")

            required_fields = [
                "document_id",
                "chunk_id",
                "source",
                "market",
                "status"
            ]

            missing_fields = [
                field for field in required_fields
                if not metadata.get(field)
            ]

            if missing_fields:
                raise ValueError(
                    f"Missing document metadata: {missing_fields}"
                )

            if metadata["status"] != "approved":
                raise ValueError(
                    "Only approved documents can be ingested."
                )

            contents.append(content)

            records.append({
                "id": str(uuid.uuid4()),
                "document_id": str(metadata["document_id"]),
                "chunk_id": str(metadata["chunk_id"]),
                "content": content,
                "source": str(metadata["source"]),
                "market": str(metadata["market"]),
                "status": str(metadata["status"]),
                "document_version": metadata.get(
                    "document_version"
                )
            })

        # Generate all embeddings in one batch.
        vectors = self.embeddings.embed_documents(contents)

        if len(vectors) != len(records):
            raise ValueError(
                "Embedding count does not match document count."
            )

        for record, vector in zip(records, vectors):
            record["embedding"] = self._to_vector_literal(vector)

        insert_query = text("""
            INSERT INTO knowledge_chunks (
                id,
                document_id,
                chunk_id,
                content,
                source,
                market,
                status,
                document_version,
                embedding
            )
            VALUES (
                :id,
                :document_id,
                :chunk_id,
                :content,
                :source,
                :market,
                :status,
                :document_version,
                CAST(:embedding AS vector)
            )
            ON CONFLICT (document_id, chunk_id)
            DO UPDATE SET
                content = EXCLUDED.content,
                source = EXCLUDED.source,
                market = EXCLUDED.market,
                status = EXCLUDED.status,
                document_version = EXCLUDED.document_version,
                embedding = EXCLUDED.embedding
        """)

        with self.engine.begin() as connection:
            connection.execute(insert_query, records)

        return len(records)

    # -----------------------------------------------------
    # 5. Semantic similarity search
    # -----------------------------------------------------

    def similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None
    ) -> list[tuple[Document, float]]:
        """
        Search approved document chunks using cosine distance.

        Returns:
            List of (LangChain Document, relevance_score)
        """

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if k < 1:
            raise ValueError("k must be at least 1.")

        filter = filter or {}

        # Only allow these metadata filters.
        allowed_filters = {"status", "market"}

        if not set(filter).issubset(allowed_filters):
            raise ValueError("Unsupported metadata filter.")

        # Default to approved documents only.
        status = filter.get("status", "approved")
        market = filter.get("market", "UK")

        if status != "approved":
            raise ValueError(
                "Knowledge search is restricted to approved documents."
            )

        # Convert customer query into an embedding.
        query_vector = self.embeddings.embed_query(query)

        query_vector_literal = self._to_vector_literal(
            query_vector
        )

        search_query = text("""
            SELECT
                document_id,
                chunk_id,
                content,
                source,
                market,
                status,
                document_version,
                1 - (
                    embedding <=> CAST(:query_vector AS vector)
                ) AS relevance_score

            FROM knowledge_chunks

            WHERE status = :status
              AND market = :market

            ORDER BY
                embedding <=> CAST(:query_vector AS vector)

            LIMIT :limit
        """)

        with self.engine.connect() as connection:

            rows = connection.execute(
                search_query,
                {
                    "query_vector": query_vector_literal,
                    "status": status,
                    "market": market,
                    "limit": k
                }
            ).mappings().all()

        results = []

        for row in rows:

            score = float(row["relevance_score"])

            # Keep scores in a predictable 0-to-1 range.
            score = max(0.0, min(1.0, score))

            document = Document(
                page_content=row["content"],
                metadata={
                    "document_id": row["document_id"],
                    "chunk_id": row["chunk_id"],
                    "source": row["source"],
                    "market": row["market"],
                    "status": row["status"],
                    "document_version": row["document_version"]
                }
            )

            results.append((document, score))

        return results
