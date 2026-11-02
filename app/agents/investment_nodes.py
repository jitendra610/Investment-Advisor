import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from langgraph.types import interrupt

from investment_schemas import QueryClassification


# -----------------------------------------
# Agent 1: Query Analyzer
# -----------------------------------------

async def query_analyzer(state):

    query = state["query"]

    if os.getenv("OPENAI_API_KEY"):

        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0
        )

        structured_llm = llm.with_structured_output(
            QueryClassification
        )

        result = await structured_llm.ainvoke([
            SystemMessage(content="""
                Classify investment questions.

                Distinguish general financial education
                from requests for personalised investment advice.

                Do not recommend investments or contribution changes.
                Return only the requested structured classification.
            """),
            HumanMessage(content=query)
        ])

    else:
        # Development-only mock classifier.
        # Replace with a validated model in production.

        lower_query = query.lower()

        if any(word in lower_query for word in [
            "should i",
            "my investment",
            "increase my",
            "buy",
            "sell",
            "recommend"
        ]):
            result = QueryClassification(
                intent="personalized_advice",
                requires_customer_context=True,
                entities=["investment"],
                timeframe="unknown",
                reasoning_summary="Personalised financial decision requested."
            )

        elif any(word in lower_query for word in [
            "explain",
            "what is",
            "difference",
            "how does"
        ]):
            result = QueryClassification(
                intent="general_education",
                requires_customer_context=False,
                entities=["financial education"],
                timeframe="unknown",
                reasoning_summary="General educational question."
            )

        else:
            result = QueryClassification(
                intent="unclear",
                requires_customer_context=False,
                entities=[],
                timeframe="unknown",
                reasoning_summary="Intent needs clarification."
            )

    return {
        "intent": result.intent,
        "requires_customer_context":
            result.requires_customer_context,
        "audit_events": ["Query analyzed"]
    }


# -----------------------------------------
# Agent 2: Customer Context Agent
# -----------------------------------------

async def customer_context_agent(state):

    # Synthetic demonstration only.
    # Real customer data requires appropriate
    # authorisation, consent/legal basis and access controls.

    context = {
        "accessed": False,
        "source": "synthetic_demo",
        "reason": "No customer profile accessed in this exercise"
    }

    return {
        "customer_context": context,
        "audit_events": ["Customer context access checked"]
    }


# -----------------------------------------
# Agent 3: Knowledge Retrieval Agent
# -----------------------------------------

async def knowledge_agent(state):

    # Temporary mock knowledge base.
    # We will replace this with PostgreSQL + pgvector RAG.

    documents = [
        {
            "document_id": "DEMO-PENSION-001",
            "topic": "Pension contributions",
            "content": (
                "Pension contribution arrangements can depend "
                "on scheme rules, employer contributions, "
                "fees, tax treatment and individual circumstances. "
                "This is synthetic demonstration content."
            ),
            "source": "Synthetic demonstration document"
        }
    ]

    return {
        "retrieved_documents": documents,
        "audit_events": ["Knowledge retrieval completed"]
    }


# -----------------------------------------
# Agent 4: Compliance Agent
# -----------------------------------------

async def compliance_agent(state):

    intent = state["intent"]

    # Deterministic policy routing.
    # This is a demonstration policy, not a complete FCA rules engine.

    if intent == "general_education":

        status = "approved"

    elif intent == "personalized_advice":

        status = "human_review"

    else:

        status = "blocked"

    return {
        "compliance_status": status,
        "audit_events": [
            f"Compliance routing: {status}"
        ]
    }


# -----------------------------------------
# Agent 5: Response Agent
# -----------------------------------------

async def response_agent(state):

    documents = state.get(
        "retrieved_documents", []
    )

    citations = [
        doc["document_id"]
        for doc in documents
    ]

    response = """
    I can provide general educational information.

    Pension contribution arrangements can depend on
    scheme rules, employer contributions, fees,
    tax treatment and personal circumstances.

    This demonstration cannot determine whether you
    should change your own contributions.

    For a personal decision, consult your pension
    provider or an appropriately authorised adviser.
    """

    return {
        "final_response": response.strip(),
        "citations": citations,
        "audit_events": ["Educational response generated"]
    }


# -----------------------------------------
# Agent 6: Human Review Agent
# -----------------------------------------

async def human_review_agent(state):

    # Pause graph execution until an authorised
    # reviewer provides a decision.

    decision = interrupt({
        "request_id": state["request_id"],
        "intent": state["intent"],
        "reason": "Personalised advice requires authorised review",
        "action": "Review and provide a decision"
    })

    if decision.get("decision") == "approved":

        result = "approved"

    else:

        result = "rejected"

    return {
        "review_decision": result,
        "audit_events": ["Human review completed"]
    }


# -----------------------------------------
# Agent 7: Blocked Response Agent
# -----------------------------------------

async def blocked_response_agent(state):

    return {
        "final_response": (
            "This request cannot be processed through "
            "the current educational service. "
            "Please contact the appropriate support team."
        ),
        "audit_events": ["Request blocked"]
    }