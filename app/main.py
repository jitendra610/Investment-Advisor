
from contextlib import asynccontextmanager
import logging
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.request import InvestmentRequest
from app.graph.workflow import workflow

logger = logging.getLogger(__name__)

from app.services.database import (
    initialize_database,
    check_database_connection,
    close_database_connections,
)


def configure_agents() -> None:
    """
    Configure all agent dependencies before serving requests.

    Add the exact repository/vector-store constructors from your
    existing implementation here.

    Required configuration:
    - Customer Context Agent: PostgreSQL customer repository
    - Knowledge Agent: PostgreSQL/pgvector vector store
    - Financial Analysis Agent: financial calculator
    - Compliance Agent: policy engine
    - Response Agent: ChatOpenAI model

    Do not accept requests until all required agents are configured.
    """

    from app.agents.response_agent import configure_response_agent
    from app.agents.compliance_agent import configure_compliance_agent

    # These two agents do not require an external repository in
    # the implementations described so far.
    from app.agents.compliance_agent import (
    ComplianceAgent,
    CompliancePolicyEngine,
    configure_compliance_agent,
)

    compliance_engine = CompliancePolicyEngine()
    compliance_agent = ComplianceAgent(compliance_engine)

    configure_compliance_agent(compliance_agent)
    configure_response_agent()

    # TODO: Configure Customer Context Agent using its PostgreSQL repository.
    # TODO: Configure Knowledge Agent using PostgresVectorStore.
    # TODO: Configure Financial Analysis Agent using FinancialCalculator.

    logger.info("Basic agent configuration completed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""

    logger.info("Starting %s", settings.app_name)

    # Configure agent dependencies before accepting requests.
    # Complete the TODOs in configure_agents() before running
    # the full workflow.
    configure_agents()

    app.state.workflow = workflow

    logger.info("Application startup completed.")

    yield

    logger.info("Application shutdown completed.")


app = FastAPI(
    title="Investment AI API",
    description=(
        "Educational prototype for investment information, "
        "pension explanations, and illustrative calculations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    """Basic application information."""

    return {
        "application": settings.app_name,
        "status": "running",
        "message": "Investment AI API is running.",
    }


@app.get("/health")
def health_check():
    """Application health endpoint."""

    return {
        "status": "healthy",
        "application": settings.app_name,
    }


@app.post("/api/v1/investment/query")
def submit_investment_query(
    request: InvestmentRequest,
    x_dev_customer_id: Optional[str] = Header(
        default=None,
        alias="X-Dev-Customer-ID",
    ),
):
    """
    Submit an investment information request to LangGraph.

    X-Dev-Customer-ID is a development-only identity placeholder.
    Replace it with a verified authenticated principal in production.
    """

    # Development-only identity consistency check.
    if (
        x_dev_customer_id is not None
        and x_dev_customer_id != request.customer_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer identity does not match the authenticated identity.",
        )

    # Convert the validated Pydantic request into workflow state.
    state = request.model_dump(mode="json")

    # Identity comes from the trusted authentication layer.
    # This header is only a local development placeholder.
    state["authenticated_customer_id"] = x_dev_customer_id

    # Add workflow-specific fields that are not currently part
    # of the public API request schema.
    state["financial_inputs"] = {}
    state["audit_events"] = []

    try:
        result = app.state.workflow.invoke(state)

        return {
            "request_id": result.get("request_id"),
            "compliance_status": result.get("compliance_status"),
            "response_status": result.get("response_status"),
            "final_response": result.get("final_response"),
            "citations": result.get("citations", []),
            "requires_human_review": result.get(
                "requires_human_review",
                False,
            ),
        }

    except Exception:
        # Log technical details internally, not in the customer response.
        logger.exception(
            "Investment workflow failed. Request ID: %s",
            state.get("request_id"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The request could not be processed. Please try again later.",
        )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request, exc):
    """Prevent unexpected internal exception details leaking to clients."""

    logger.exception("Unexpected API error")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred."
        },
    )
