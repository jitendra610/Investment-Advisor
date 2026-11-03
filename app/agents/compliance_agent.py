
from dataclasses import dataclass
from typing import Literal, Optional

from app.graph.state import InvestmentState


ComplianceStatus = Literal[
    "approved",
    "human_review",
    "blocked"
]


# ---------------------------------------------------------
# 1. Compliance decision model
# ---------------------------------------------------------

@dataclass
class ComplianceDecision:
    status: ComplianceStatus
    reasons: list[str]
    rule_ids: list[str]
    requires_human_review: bool


# ---------------------------------------------------------
# 2. Deterministic Compliance Policy Engine
# ---------------------------------------------------------

class CompliancePolicyEngine:
    """
    Evaluates workflow state against configured policy rules.

    This is a prototype policy engine, not a complete
    regulatory compliance or suitability assessment system.
    """

    PERSONALIZED_ADVICE_INTENTS = {
        "personalised_investment_advice",
        "personalized_investment_advice",
        "investment_recommendation",
        "product_recommendation",
        "portfolio_recommendation",
        "suitability_assessment",
    }

    PERSONALIZED_ADVICE_REQUEST_TYPES = {
        "personalised_advice",
        "personalized_advice",
        "investment_recommendation",
        "product_recommendation",
        "suitability_assessment",
    }

    def evaluate(
        self,
        state: InvestmentState
    ) -> ComplianceDecision:

        blocked_rules = []
        review_rules = []

        reasons = []
        rule_ids = []

        query_analysis = state.get("query_analysis", {})
        request_type = (
            state.get("request_type") or ""
        ).strip().lower()

        intent = (
            query_analysis.get("intent") or ""
        ).strip().lower()

        # -------------------------------------------------
        # Rule C001: Customer identity mismatch
        # -------------------------------------------------

        requested_customer_id = state.get("customer_id")
        authenticated_customer_id = state.get(
            "authenticated_customer_id"
        )

        if (
            authenticated_customer_id
            and requested_customer_id != authenticated_customer_id
        ):
            blocked_rules.append("C001")
            reasons.append(
                "Requested customer identity does not match "
                "the authenticated identity."
            )

        # -------------------------------------------------
        # Rule C002: Customer data access denied
        # -------------------------------------------------

        customer_status = state.get(
            "customer_context_status"
        )

        if customer_status == "access_denied":
            blocked_rules.append("C002")
            reasons.append(
                "Customer context access was denied."
            )

        # -------------------------------------------------
        # Rule C003: Personalised financial advice
        # -------------------------------------------------

        if (
            intent in self.PERSONALIZED_ADVICE_INTENTS
            or request_type in self.PERSONALIZED_ADVICE_REQUEST_TYPES
        ):
            review_rules.append("C003")
            reasons.append(
                "The request may involve personalised investment "
                "advice or product suitability assessment."
            )

        # -------------------------------------------------
        # Rule C004: Invalid financial calculation inputs
        # -------------------------------------------------

        financial_analysis = state.get(
            "financial_analysis", {}
        )

        financial_status = financial_analysis.get("status")

        if financial_status == "invalid_inputs":
            review_rules.append("C004")
            reasons.append(
                "Financial calculation inputs failed validation."
            )

        # -------------------------------------------------
        # Rule C005: Calculation inputs are incomplete
        # -------------------------------------------------

        if financial_status == "awaiting_inputs":
            review_rules.append("C005")
            reasons.append(
                "Required financial calculation inputs are missing."
            )

        # -------------------------------------------------
        # Rule C006: Knowledge service unavailable
        # -------------------------------------------------

        knowledge_status = state.get("knowledge_status")

        if knowledge_status == "unavailable":
            review_rules.append("C006")
            reasons.append(
                "Approved knowledge sources could not be retrieved."
            )

        # -------------------------------------------------
        # Rule C007: No relevant knowledge documents
        # -------------------------------------------------

        if knowledge_status == "no_relevant_documents":
            review_rules.append("C007")
            reasons.append(
                "No relevant approved knowledge documents were found."
            )

        # -------------------------------------------------
        # Rule C008: Required customer context unavailable
        # -------------------------------------------------

        requires_customer_context = query_analysis.get(
            "requires_customer_context", False
        )

        if requires_customer_context and customer_status in {
            "not_found",
            "unavailable",
            "invalid_data"
        }:
            review_rules.append("C008")
            reasons.append(
                "Required customer information is unavailable "
                "or could not be validated."
            )

        # -------------------------------------------------
        # Rule C009: Missing query analysis
        # -------------------------------------------------

        if not query_analysis:
            review_rules.append("C009")
            reasons.append(
                "Query analysis is missing; the request cannot "
                "be reliably classified."
            )

        # -------------------------------------------------
        # Rule C010: Unexpected customer context status
        # -------------------------------------------------

        if requires_customer_context and customer_status not in {
            "found",
            "not_found",
            "unavailable",
            "invalid_data",
            "access_denied"
        }:
            review_rules.append("C010")
            reasons.append(
                "Customer context retrieval status is missing "
                "or unrecognised."
            )

        # -------------------------------------------------
        # 3. Determine final compliance outcome
        # -------------------------------------------------

        rule_ids = blocked_rules + review_rules

        if blocked_rules:

            return ComplianceDecision(
                status="blocked",
                reasons=reasons,
                rule_ids=rule_ids,
                requires_human_review=False
            )

        if review_rules:

            return ComplianceDecision(
                status="human_review",
                reasons=reasons,
                rule_ids=rule_ids,
                requires_human_review=True
            )

        return ComplianceDecision(
            status="approved",
            reasons=[
                "All configured prototype policy checks passed."
            ],
            rule_ids=["C000"],
            requires_human_review=False
        )


# ---------------------------------------------------------
# 4. Compliance Agent
# ---------------------------------------------------------

class ComplianceAgent:

    def __init__(
        self,
        policy_engine: Optional[CompliancePolicyEngine] = None
    ):

        self.policy_engine = (
            policy_engine
            if policy_engine is not None
            else CompliancePolicyEngine()
        )

    def evaluate(self, state: InvestmentState) -> dict:

        decision = self.policy_engine.evaluate(state)

        audit_message = (
            f"Compliance evaluation completed: "
            f"{decision.status}; "
            f"rules={','.join(decision.rule_ids)}"
        )

        return {
            "compliance_status": decision.status,
            "compliance_reasons": decision.reasons,
            "compliance_rule_ids": decision.rule_ids,
            "requires_human_review": (
                decision.requires_human_review
            ),
            "audit_events": [audit_message]
        }


# ---------------------------------------------------------
# 5. LangGraph node
# ---------------------------------------------------------

_compliance_agent: Optional[ComplianceAgent] = None


def configure_compliance_agent(
    agent: ComplianceAgent
) -> None:

    global _compliance_agent
    _compliance_agent = agent


def compliance_agent_node(
    state: InvestmentState
) -> dict:
    """
    LangGraph entry point for compliance evaluation.
    """

    if _compliance_agent is None:
        raise RuntimeError(
            "ComplianceAgent is not configured."
        )

    return _compliance_agent.evaluate(state)
