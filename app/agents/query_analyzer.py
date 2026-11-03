
from typing import Optional
from app.graph import state
from app.prompts.prompt_manager import prompt_manager
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.graph.state import InvestmentState
from app.services.llm import get_llm


# ---------------------------------------------------------
# 1. Define the structured output expected from the LLM
# ---------------------------------------------------------

class QueryAnalysisOutput(BaseModel):
    """Structured result produced by the Query Analyzer Agent."""

    intent: str = Field(
        description=(
            "The main purpose of the customer's query. "
            "Examples: general_education, pension_contribution_impact, "
            "retirement_projection, investment_information, "
            "portfolio_question, product_information, unclear."
        )
    )

    entities: list[str] = Field(
        description=(
            "Important financial concepts, products, amounts, "
            "or topics mentioned in the query."
        )
    )

    timeframe: str = Field(
        description=(
            "Time period mentioned in the query. "
            "Examples: 20 years, 5 years, short_term, long_term, "
            "not_specified."
        )
    )

    requires_customer_context: bool = Field(
        description=(
            "True when answering the query requires customer-specific "
            "information, such as pension details or existing holdings."
        )
    )

    requires_calculation: bool = Field(
        description=(
            "True when the query requires a numerical calculation, "
            "projection, estimate, or comparison."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "A short explanation of the classification. "
            "Do not provide financial advice."
        )
    )


# ---------------------------------------------------------
# 2. Define the Query Analyzer Agent
# ---------------------------------------------------------

class QueryAnalyzer:

    def __init__(self, llm=None):

        # Allow an LLM to be injected for unit testing.
        if llm is None:

            llm = get_llm()


        # Force the LLM to return the Pydantic schema.
        self.structured_llm = llm.with_structured_output(
            QueryAnalysisOutput
        )

    # -----------------------------------------------------
    # 3. Analyze customer query
    # -----------------------------------------------------

    def analyze(self, state: InvestmentState) -> dict:

        query = state.get("query", "").strip()

        if not query:
            raise ValueError("Customer query cannot be empty.")

        system_prompt = prompt_manager.render_prompt(
            agent_name="query_analyzer",
            prompt_type="system_prompt"
            )

        human_prompt = prompt_manager.render_prompt(
            agent_name="query_analyzer",
            prompt_type="human_prompt",
            query=state.get("query", ""),
            customer_id=state.get("customer_id", "Not provided"),
            market=state.get("market", "Not specified")
        )

        
        # Invoke the structured LLM.
        result = self.structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
            ])

        # Return only the fields that this node updates.
        return {
            "query_analysis": result.model_dump(),
            "audit_events": [
                "Query Analyzer completed successfully."
            ]
        }


# ---------------------------------------------------------
# 4. LangGraph node function
# ---------------------------------------------------------

_query_analyzer: Optional[QueryAnalyzer] = None


def query_analyzer_node(state: InvestmentState) -> dict:
    """
    LangGraph entry point for the Query Analyzer Agent.

    The analyzer is initialized lazily so importing this module
    does not require an API call or an API key.
    """

    global _query_analyzer

    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()

    return _query_analyzer.analyze(state)
