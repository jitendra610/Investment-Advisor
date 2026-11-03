
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator
)


# ------------------------------------------------
# 1. Supported markets
# ------------------------------------------------

class Market(str, Enum):

    UK = "UK"


# ------------------------------------------------
# 2. Request categories
# ------------------------------------------------

class RequestType(str, Enum):

    INVESTMENT_GUIDANCE = "investment_guidance"

    FINANCIAL_EDUCATION = "financial_education"

    PENSION_QUERY = "pension_query"

    PORTFOLIO_QUERY = "portfolio_query"


# ------------------------------------------------
# 3. Main customer request schema
# ------------------------------------------------

class InvestmentRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )

    # Unique request identifier
    request_id: UUID = Field(
        default_factory=uuid4
    )

    # Customer identifier
    customer_id: str = Field(
        min_length=3,
        max_length=50,
        description="Unique bank customer identifier"
    )

    # Customer query
    query: str = Field(
        min_length=5,
        max_length=3000,
        description="Customer investment-related query"
    )

    # Market
    market: Market = Field(
        default=Market.UK
    )

    # Request category
    request_type: RequestType = Field(
        default=RequestType.INVESTMENT_GUIDANCE
    )

    # Request timestamp
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Optional conversation identifier
    conversation_id: UUID | None = None

    # Validate customer ID
    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, value):

        if not value.replace("-", "").isalnum():
            raise ValueError(
                "Customer ID must contain only "
                "letters, numbers and hyphens"
            )

        return value

    # Validate customer query
    @field_validator("query")
    @classmethod
    def validate_query(cls, value):

        if not value.strip():
            raise ValueError(
                "Query cannot be empty"
            )

        if "\x00" in value:
            raise ValueError(
                "Query contains invalid characters"
            )

        return value


# ------------------------------------------------
# 4. Standard API response schema
# ------------------------------------------------

class InvestmentResponse(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    request_id: UUID

    status: str

    response: str | None = None

    requires_human_review: bool = False

    citations: list[str] = Field(
        default_factory=list
    )
