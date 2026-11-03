from app.graph.state import InvestmentState


def test_investment_state():

    state: InvestmentState = {

        "request_id": "REQ1001",

        "customer_id": "C1001",

        "query": (
            "Explain pension contributions"
        ),

        "query_analysis": {

            "intent": "general_education",

            "entities": ["pension"],

            "timeframe": "long_term",

            "requires_customer_context": False
        },

        "compliance_status": "approved",

        "audit_events": [
            "Query analyzed"
        ]
    }

    assert state["customer_id"] == "C1001"

    assert (
        state["query_analysis"]["intent"]
        == "general_education"
    )

    assert state["compliance_status"] == "approved"

    print("Investment state test passed!")


if __name__ == "__main__":

    test_investment_state()