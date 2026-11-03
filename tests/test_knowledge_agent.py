from app.agents.query_analyzer import QueryAnalyzer


def test_query_analyzer():

    agent = QueryAnalyzer()

    state = {
        "query": (
            "How will increasing my monthly pension "
            "contribution affect my retirement savings?"
        ),
        "request_type": "general_information",
        "market": "UK"
    }

    result = agent.analyze(state)

    print("\nQuery Analyzer Output:")
    print(result["query_analysis"])

    assert "intent" in result["query_analysis"]
    assert "requires_customer_context" in result["query_analysis"]
    assert "requires_calculation" in result["query_analysis"]

    print("\nGPT-4o-mini test passed!")


if __name__ == "__main__":
    test_query_analyzer()
