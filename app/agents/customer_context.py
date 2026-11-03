from typing import Optional, Protocol

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.graph.state import InvestmentState
from app.services.database import SessionLocal
from app.services.models import CustomerProfile

# ---------------------------------------------------------
# 1. Repository interface
# ---------------------------------------------------------

class CustomerContextRepository(Protocol):
    """Contract for retrieving customer context."""

    def get_customer(self, customer_id: str) -> Optional[dict]:
        ...


# ---------------------------------------------------------
# 2. PostgreSQL repository
# ---------------------------------------------------------

class PostgresCustomerContextRepository:

    def get_customer(self, customer_id: str):

        try:
            with SessionLocal() as session:

                statement = select(CustomerProfile).where(
                    CustomerProfile.customer_id == customer_id
                )

                customer = session.execute(
                    statement
                ).scalar_one_or_none()

                if customer is None:
                    return None

                return {
                    "customer_id": customer.customer_id,
                    "age_band": customer.age_band,
                    "pension_type": customer.pension_type,
                    "monthly_contribution": (
                        customer.monthly_contribution
                    ),
                    "currency": customer.currency,
                    "data_source": "customer_profiles",
                    "data_timestamp": (
                        customer.updated_at.isoformat()
                        if customer.updated_at else None
                    )
                }

        except SQLAlchemyError:
            raise
# ---------------------------------------------------------
# 3. Customer Context Agent
# ---------------------------------------------------------

class CustomerContextAgent:

    def __init__(
        self,
        repository: Optional[CustomerContextRepository] = None
    ):

        self.repository = (
            repository
            if repository is not None
            else PostgresCustomerContextRepository()
        )

    def retrieve(self, state: InvestmentState) -> dict:
        """
        Retrieve customer context only when:
        1. The query requires customer-specific information.
        2. An authenticated customer identity is available.
        3. The requested customer matches the authenticated identity.
        """

        query_analysis = state.get("query_analysis", {})

        # -------------------------------------------------
        # Step A: Check whether context is required
        # -------------------------------------------------

        if not query_analysis.get("requires_customer_context", False):
            return {
                "customer_context": {},
                "customer_context_status": "not_required",
                "audit_events": [
                    "Customer context retrieval skipped."
                ]
            }

        # -------------------------------------------------
        # Step B: Verify authenticated customer identity
        # -------------------------------------------------

        requested_customer_id = state.get("customer_id")
        authenticated_customer_id = state.get(
            "authenticated_customer_id"
        )

        if not authenticated_customer_id:
            return {
                "customer_context": {},
                "customer_context_status": "access_denied",
                "requires_human_review": True,
                "audit_events": [
                    "Customer context access denied: "
                    "authenticated identity missing."
                ]
            }

        if requested_customer_id != authenticated_customer_id:
            return {
                "customer_context": {},
                "customer_context_status": "access_denied",
                "requires_human_review": True,
                "audit_events": [
                    "Customer context access denied: "
                    "customer identity mismatch."
                ]
            }

        # -------------------------------------------------
        # Step C: Retrieve customer record
        # -------------------------------------------------

        try:
            customer = self.repository.get_customer(
                authenticated_customer_id
            )

        except SQLAlchemyError:
            return {
                "customer_context": {},
                "customer_context_status": "unavailable",
                "error": "Customer data service is temporarily unavailable.",
                "audit_events": [
                    "Customer context retrieval failed: database error."
                ]
            }

        # -------------------------------------------------
        # Step D: Handle missing customer
        # -------------------------------------------------

        if customer is None:
            return {
                "customer_context": {},
                "customer_context_status": "not_found",
                "audit_events": [
                    "No customer profile found for authenticated customer."
                ]
            }

        # -------------------------------------------------
        # Step E: Validate and normalise customer data
        # -------------------------------------------------

        monthly_contribution = customer.get(
            "monthly_contribution"
        )

        if monthly_contribution is not None:
            monthly_contribution = float(monthly_contribution)

            if monthly_contribution < 0:
                return {
                    "customer_context": {},
                    "customer_context_status": "invalid_data",
                    "requires_human_review": True,
                    "audit_events": [
                        "Customer context validation failed."
                    ]
                }

        data_timestamp = customer.get("data_timestamp") or ""

        context = {
            "customer_id": customer["customer_id"],
            "age_band": customer.get("age_band") or "",
            "pension_type": customer.get("pension_type") or "",
            "monthly_contribution": monthly_contribution,
            "currency": customer.get("currency") or "GBP",
            "data_source": "customer_profiles",
            "data_timestamp": data_timestamp
        }

        # -------------------------------------------------
        # Step F: Return context to LangGraph
        # -------------------------------------------------

        return {
            "customer_context": context,
            "customer_context_status": "found",
            "audit_events": [
                "Customer context retrieved and validated."
            ]
        }


# ---------------------------------------------------------
# 4. LangGraph node
# ---------------------------------------------------------

_customer_context_agent: Optional[CustomerContextAgent] = None


def customer_context_node(state: InvestmentState) -> dict:
    """
    LangGraph entry point for Customer Context Agent.
    """

    global _customer_context_agent

    if _customer_context_agent is None:
        _customer_context_agent = CustomerContextAgent()

    return _customer_context_agent.retrieve(state)
