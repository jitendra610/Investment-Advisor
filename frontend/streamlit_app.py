
import streamlit as st

from api_client import InvestmentAPIClient


# --------------------------------------------------
# 1. Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Investment AI Assistant",
    page_icon="📈",
    layout="wide",
)


# --------------------------------------------------
# 2. Backend Configuration
# --------------------------------------------------

st.sidebar.title("Backend Configuration")

api_url = st.sidebar.text_input(
    "FastAPI URL",
    value="http://127.0.0.1:8000",
)

client = InvestmentAPIClient(api_url)

if st.sidebar.button("Check Backend Connection"):
    health = client.health_check()

    if health.get("status") == "healthy":
        st.sidebar.success("FastAPI Connected")
    else:
        st.sidebar.error("Backend unavailable")
        st.sidebar.caption(health.get("error", ""))


# --------------------------------------------------
# 3. Application Header
# --------------------------------------------------

st.title("📈 Investment AI Assistant")

st.markdown(
    """
    Welcome to the Investment AI Assistant.

    Ask questions about pensions, investment concepts,
    financial information, and illustrative calculations.

    This educational prototype does not provide regulated
    personalised investment advice.
    """
)

st.divider()


# --------------------------------------------------
# 4. Customer Input
# --------------------------------------------------

st.subheader("Customer Information")

customer_id = st.text_input(
    "Customer ID",
    value="C1001",
    help="Use a synthetic customer ID configured in your local database.",
)


# --------------------------------------------------
# 5. Query Input
# --------------------------------------------------

st.subheader("Ask Your Question")

query = st.text_area(
    "Enter your investment-related question",
    placeholder=(
        "Example: Explain how pension contributions work."
    ),
    height=120,
)

st.caption(
    "Current request type: General information"
)


# --------------------------------------------------
# 6. Submit Query
# --------------------------------------------------

if st.button(
    "Submit Query",
    type="primary",
    use_container_width=True,
):

    if not customer_id.strip():
        st.error("Please enter a customer ID.")

    elif not query.strip():
        st.warning("Please enter your question.")

    else:
        with st.spinner(
            "Investment AI is analysing your question..."
        ):

            result = client.submit_query(
                customer_id=customer_id.strip(),
                query=query.strip(),
            )

        # ------------------------------------------
        # 7. Display API Errors
        # ------------------------------------------

        if "error" in result:

            st.error("Unable to process your request.")

            st.json(result["error"])

        else:

            st.success("Request processing completed.")

            # --------------------------------------
            # 8. Display Compliance Status
            # --------------------------------------

            compliance_status = result.get(
                "compliance_status",
                "unknown",
            )

            response_status = result.get(
                "response_status",
                "unknown",
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Compliance Status",
                    compliance_status.upper(),
                )

            with col2:
                st.metric(
                    "Response Status",
                    response_status.upper(),
                )

            st.divider()

            # --------------------------------------
            # 9. Display AI Response
            # --------------------------------------

            st.subheader("AI Response")

            final_response = result.get(
                "final_response",
                "No response was returned.",
            )

            st.markdown(final_response)

            # --------------------------------------
            # 10. Display Citations
            # --------------------------------------

            citations = result.get("citations", [])

            if citations:
                with st.expander("View Sources"):
                    for citation in citations:
                        st.write(f"- {citation}")

            # --------------------------------------
            # 11. Display Review Status
            # --------------------------------------

            if result.get("requires_human_review"):
                st.warning(
                    "This request requires additional human review."
                )

            # --------------------------------------
            # 12. Debug Information
            # --------------------------------------

            with st.expander("Technical Response (Debug)"):
                st.json(result)


# --------------------------------------------------
# 13. Footer
# --------------------------------------------------

st.divider()

st.caption(
    "Investment AI | Local Development Prototype | "
    "For educational purposes only."
)
