import asyncio
import uuid

from langgraph.types import Command

from investment_graph import investment_app


async def run_investment_system():

    request_id = str(uuid.uuid4())

    initial_state = {
        "request_id": request_id,
        "customer_id": "DEMO_CUSTOMER",
        "query": (
            "Explain how pension contributions work."
        ),
        "audit_events": []
    }

    config = {
        "configurable": {
            "thread_id": request_id
        }
    }

    result = await investment_app.ainvoke(
        initial_state,
        config=config
    )

    print("\n========== FINAL RESULT ==========")

    print("Response:")
    print(result.get("final_response"))

    print("\nIntent:")
    print(result.get("intent"))

    print("\nCompliance:")
    print(result.get("compliance_status"))

    print("\nCitations:")
    print(result.get("citations"))

    print("\nAudit Events:")
    print(result.get("audit_events"))


if __name__ == "__main__":

    asyncio.run(run_investment_system())