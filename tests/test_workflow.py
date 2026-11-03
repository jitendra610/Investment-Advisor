
from app.graph.workflow import (
    build_workflow,
    compliance_router,
    human_review_response_node,
    blocked_response_node,
    unknown_compliance_response_node,
)


def test_workflow_compiles():
    graph = build_workflow()


    assert graph is not None


def test_compliance_router_approved():
    state = {"compliance_status": "approved"}

    assert compliance_router(state) == "approved"


def test_compliance_router_human_review():
    state = {"compliance_status": "human_review"}

    assert compliance_router(state) == "human_review"


def test_compliance_router_blocked():
    state = {"compliance_status": "blocked"}

    assert compliance_router(state) == "blocked"


def test_compliance_router_missing_status_fails_closed():
    state = {}

    assert compliance_router(state) == "unknown"


def test_human_review_response_is_deterministic():
    result = human_review_response_node({})

    assert result["response_status"] == "human_review"
    assert "additional review" in result["final_response"]


def test_blocked_response_is_deterministic():
    result = blocked_response_node({})

    assert result["response_status"] == "blocked"


def test_unknown_status_returns_safe_response():
    result = unknown_compliance_response_node({})

    assert result["response_status"] == "not_authorised"
