from pydantic import ValidationError

from app.schemas.request import (
    InvestmentRequest,
    RequestType,
    Market
)


# ---------------------------------
# Test 1: Valid request
# ---------------------------------

request = InvestmentRequest(
    customer_id="C1001",
    query="Explain pension contributions",
    market=Market.UK,
    request_type=RequestType.PENSION_QUERY
)

print("VALID REQUEST")
print(request.model_dump())


# ---------------------------------
# Test 2: Invalid customer ID
# ---------------------------------

try:

    InvestmentRequest(
        customer_id="@@@",
        query="Explain pension contributions"
    )

except ValidationError as error:

    print("\nINVALID CUSTOMER ID")
    print(error)


# ---------------------------------
# Test 3: Invalid market
# ---------------------------------

try:

    InvestmentRequest(
        customer_id="C1001",
        query="Explain pension contributions",
        market="USA"
    )

except ValidationError as error:

    print("\nINVALID MARKET")
    print(error)


# ---------------------------------
# Test 4: Empty query
# ---------------------------------

try:

    InvestmentRequest(
        customer_id="C1001",
        query="     "
    )

except ValidationError as error:

    print("\nINVALID QUERY")
    print(error)