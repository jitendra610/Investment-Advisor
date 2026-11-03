
from typing import (
    TypedDict,
    Annotated,
    Optional,
    Literal
)

import operator


# ==========================================
# 1. Query Analysis State
# ==========================================

class QueryAnalysis(TypedDict, total=False):

    intent: str

    entities: list[str]

    timeframe: str

    requires_customer_context: bool

    requires_calculation: bool

    reasoning_summary: str


# ==========================================
# 2. Customer Context State
# ==========================================

class CustomerContext(TypedDict, total=False):

    customer_id: str

    age_band: str

    pension_type: str

    monthly_contribution: float

    currency: str

    data_source: str

    data_timestamp: str


# ==========================================
# 3. Retrieved Document State
# ==========================================

class RetrievedDocument(TypedDict):

    document_id: str

    content: str

    source: str

    relevance_score: float


# ==========================================
# 4. Financial Analysis State
# ==========================================

class FinancialAnalysis(TypedDict, total=False):

    calculation_type: str

    input_values: dict

    output_values: dict

    assumptions: list[str]


# ==========================================
# 5. Main Investment Workflow State
# ==========================================

class InvestmentState(TypedDict, total=False):

    # Request information
    request_id: str

    customer_id: str

    authenticated_customer_id: str

    query: str

    market: str

    request_type: str

    # Query analysis
    query_analysis: QueryAnalysis

    # Customer information
    customer_context: CustomerContext

    customer_context_status: Optional[
    Literal[
        "not_required",
        "access_denied",
        "unavailable",
        "not_found",
        "invalid_data",
        "found"
    ]
]

    # Knowledge retrieval
    retrieved_documents: list[RetrievedDocument]

    knowledge_status: str

    citations: list[str]

    # Financial calculations
    financial_inputs: dict

    financial_analysis: FinancialAnalysis

    # Compliance
    compliance_status: Literal[
        "approved",
        "human_review",
        "blocked"
    ]

    compliance_reasons: list[str]

    compliance_rule_ids: list[str]

    # Human review
    requires_human_review: bool

    human_review_status: str

    # Final response
    final_response: str

    response_status: str

    # Error handling
    error: Optional[str]

    # Audit events
    audit_events: Annotated[
        list[str],
        operator.add
    ]
