from investment_graph import (
    route_after_compliance,
    route_after_human_review
)


def test_approved_route():

    state = {
        "compliance_status": "approved"
    }

    assert route_after_compliance(state) == "response"


def test_human_review_route():

    state = {
        "compliance_status": "human_review"
    }

    assert route_after_compliance(state) == "human_review"


def test_blocked_route():

    state = {
        "compliance_status": "blocked"
    }

    assert route_after_compliance(state) == "blocked"


def test_rejected_review():

    state = {
        "review_decision": "rejected"
    }

    assert route_after_human_review(state) == "blocked"