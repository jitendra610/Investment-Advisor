
import requests


class InvestmentAPIClient:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health_check(self):
        """Check whether the FastAPI backend is running."""

        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10,
            )

            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            return {
                "status": "unavailable",
                "error": str(exc),
            }

    def submit_query(
        self,
        customer_id: str,
        query: str,
        market: str = "UK",
        request_type: str = "general_information",
    ):
        """Send a customer query to FastAPI."""

        payload = {
            "customer_id": customer_id,
            "query": query,
            "market": market,
            "request_type": request_type,
        }

        headers = {
            "X-Dev-Customer-ID": customer_id,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/investment/query",
                json=payload,
                headers=headers,
                timeout=120,
            )

            response.raise_for_status()
            return response.json()

        except requests.HTTPError:
            try:
                error_details = response.json()
            except ValueError:
                error_details = response.text

            return {
                "error": error_details,
                "status_code": response.status_code,
            }

        except requests.RequestException as exc:
            return {
                "error": str(exc),
                "status_code": None,
            }
