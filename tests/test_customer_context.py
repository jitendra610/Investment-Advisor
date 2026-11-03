
from app.agents.customer_context import CustomerContextAgent


def test_customer_context_agent():

    agent = CustomerContextAgent()

    state = {
        "customer_id": "C1001",
        "authenticated_customer_id": "C1001",
        "query_analysis": {
            "requires_customer_context": True
        },
        "audit_events": []
    }

    result = agent.retrieve(state)

    print("\nCustomer Context Result:")
    print(result)

    assert result["customer_context_status"] == "found"
    assert result["customer_context"]["customer_id"] == "C1001"

    print("\nCustomer Context Agent test passed!")


if __name__ == "__main__":
    test_customer_context_agent()
