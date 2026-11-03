
from typing import Literal, Optional

from langgraph.graph import StateGraph, START, END

from app.graph.state import InvestmentState

from app.agents.query_analyzer import query_analyzer_node
from app.agents.customer_context import customer_context_node
from app.agents.knowledge_agent import knowledge_agent_node
from app.agents.financial_analysis import financial_analysis_node
from app.agents.compliance_agent import compliance_agent_node
from app.agents.response_agent import response_agent_node


def compliance_router(
    state: InvestmentState,
) -> Literal[
    "approved",
    "human_review",
    "blocked",
    "unknown",
]:
    """
    Route the workflow based on the Compliance Agent decision.

    Unknown or missing compliance status is treated as not approved.
    """

    status = state.get("compliance_status")

    if status == "approved":
        return "approved"

    if status == "human_review":
        return "human_review"

    if status == "blocked":
        return "blocked"

    return "unknown"

def customer_context_router(
    state: InvestmentState,
) -> Literal["continue", "stop"]:

    query_analysis = state.get("query_analysis", {})

    # Customer context is not required.
    if not query_analysis.get("requires_customer_context", False):
        return "continue"

    status = state.get("customer_context_status")

    if status == "found":
        return "continue"

    # Fail closed for customer-specific requests.
    return "stop"

def customer_context_error_node(state: InvestmentState) -> dict:

    status = state.get("customer_context_status", "unavailable")

    messages = {
        "access_denied": (
            "We could not verify your customer identity. "
            "Please authenticate before accessing customer-specific information."
        ),
        "not_found": (
            "No customer profile was found for the authenticated customer."
        ),
        "unavailable": (
            "Customer information is temporarily unavailable."
        ),
        "invalid_data": (
            "The customer profile requires validation before it can be used."
        ),
    }

    return {
        "final_response": messages.get(
            status,
            "Customer information could not be verified."
        ),
        "response_status": "customer_context_error",
        "audit_events": [
            f"Workflow stopped because customer context status was {status}."
        ],
    }

def approved_response_node(state: InvestmentState) -> dict:
    """Generate a grounded response for an approved request."""

    return response_agent_node(state)


def human_review_response_node(state: InvestmentState) -> dict:
    """Return a deterministic response without calling the LLM."""

    return {
        "final_response": (
            "Your request requires additional review before we can "
            "provide a response. It has not been treated as an "
            "approved recommendation."
        ),
        "response_status": "human_review",
        "audit_events": [
            "Workflow routed request to human-review response."
        ],
    }


def blocked_response_node(state: InvestmentState) -> dict:
    """Return a deterministic response for a blocked request."""

    return {
        "final_response": (
            "We cannot process this request through the current "
            "service. Please contact the appropriate support team "
            "if you need further assistance."
        ),
        "response_status": "blocked",
        "audit_events": [
            "Workflow routed request to blocked response."
        ],
    }


def unknown_compliance_response_node(
    state: InvestmentState,
) -> dict:
    """Fail closed when the compliance result is missing or unknown."""

    return {
        "final_response": (
            "We are unable to generate a response because the "
            "required approval status could not be confirmed."
        ),
        "response_status": "not_authorised",
        "audit_events": [
            "Workflow stopped response generation because "
            "compliance status was missing or unknown."
        ],
    }


def build_workflow(checkpointer: Optional[object] = None):
    """
    Build and compile the investment guidance workflow.

    Pass a LangGraph-compatible checkpointer when persistent
    conversation state is required.
    """

    graph = StateGraph(InvestmentState)

    # Register agent nodes.
    graph.add_node("query_analyzer", query_analyzer_node)
    graph.add_node("customer_context", customer_context_node)
    graph.add_node("knowledge_agent", knowledge_agent_node)
    graph.add_node("financial_analysis", financial_analysis_node)
    graph.add_node("compliance_agent", compliance_agent_node)
    graph.add_node("customer_context_error", customer_context_error_node)

    # Register response nodes.
    graph.add_node("approved_response", approved_response_node)
    graph.add_node("human_review_response", human_review_response_node)
    graph.add_node("blocked_response", blocked_response_node)
    graph.add_node(
        "unknown_compliance_response",
        unknown_compliance_response_node,
    )

    # Start with query understanding.
    graph.add_edge(START, "query_analyzer")

    # Independent tasks run in parallel.
    graph.add_edge("query_analyzer", "customer_context")
    graph.add_edge("query_analyzer", "knowledge_agent")

    # Wait for both branches before financial analysis.
    graph.add_conditional_edges(
        "customer_context",
        customer_context_router,
        {
            "continue": "financial_analysis",
            "stop": "customer_context_error",
        },
    )

    graph.add_edge(
        "customer_context_error",
        END,
    )

    graph.add_edge(
        "knowledge_agent",
        "financial_analysis",
    )

    # Run compliance after all relevant results are available.
    graph.add_edge("financial_analysis", "compliance_agent")

    # Route according to the compliance decision.
    graph.add_conditional_edges(
        "compliance_agent",
        compliance_router,
        {
            "approved": "approved_response",
            "human_review": "human_review_response",
            "blocked": "blocked_response",
            "unknown": "unknown_compliance_response",
        },
    )

    # Every response path ends the workflow.
    graph.add_edge("approved_response", END)
    graph.add_edge("human_review_response", END)
    graph.add_edge("blocked_response", END)
    graph.add_edge("unknown_compliance_response", END)

    return graph.compile(checkpointer=checkpointer)


# Build the graph without a persistent checkpointer.
# Persistent PostgreSQL checkpointing will be configured separately.
workflow = build_workflow()
