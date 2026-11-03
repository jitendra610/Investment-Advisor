
from math import isfinite
from typing import Optional

from app.graph.state import InvestmentState


# ---------------------------------------------------------
# 1. Financial Calculation Engine
# ---------------------------------------------------------

class FinancialCalculator:
    """
    Deterministic financial calculations.

    These calculations are educational illustrations,
    not investment forecasts or guarantees.
    """

    @staticmethod
    def _validate_number(
        name: str,
        value: float,
        minimum: float,
        maximum: float
    ) -> float:

        # Reject booleans as well as non-numeric values.
        if isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise ValueError(f"{name} must be a number.")

        value = float(value)

        if not isfinite(value):
            raise ValueError(f"{name} must be finite.")

        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name} must be between {minimum} and {maximum}."
            )

        return value

    @classmethod
    def calculate_pension_projection(
        cls,
        monthly_contribution: float,
        years: int,
        annual_return_percent: float,
        initial_balance: float = 0.0,
        currency: str = "GBP"
    ) -> dict:
        """
        Calculate an illustrative pension projection.

        Assumptions:
        - Contributions occur at the end of each month.
        - Annual return is converted to an effective monthly rate.
        - Return is constant for the illustration.
        - No fees, taxes or inflation are included.
        """

        monthly_contribution = cls._validate_number(
            "monthly_contribution",
            monthly_contribution,
            0,
            10_000_000
        )

        initial_balance = cls._validate_number(
            "initial_balance",
            initial_balance,
            0,
            1_000_000_000
        )

        annual_return_percent = cls._validate_number(
            "annual_return_percent",
            annual_return_percent,
            -99.9,
            100
        )

        years = cls._validate_number(
            "years",
            years,
            1,
            80
        )

        if not years.is_integer():
            raise ValueError("years must be a whole number.")

        years = int(years)

        if not isinstance(currency, str) or currency not in {
            "GBP", "EUR", "USD"
        }:
            raise ValueError(
                "Currency must be GBP, EUR, or USD."
            )

        # Convert annual percentage into decimal.
        annual_rate = annual_return_percent / 100

        # Effective monthly rate.
        monthly_rate = (
            (1 + annual_rate) ** (1 / 12)
        ) - 1

        number_of_months = years * 12

        # Future value of regular monthly contributions.
        if abs(monthly_rate) < 1e-12:

            contribution_future_value = (
                monthly_contribution * number_of_months
            )

        else:

            contribution_future_value = (
                monthly_contribution
                * (
                    (1 + monthly_rate) ** number_of_months - 1
                )
                / monthly_rate
            )

        # Future value of existing balance.
        initial_balance_future_value = (
            initial_balance
            * (1 + monthly_rate) ** number_of_months
        )

        # Combined projection.
        projected_value = (
            contribution_future_value
            + initial_balance_future_value
        )

        total_contributions = (
            monthly_contribution * number_of_months
        )

        total_invested = (
            initial_balance + total_contributions
        )

        illustrative_growth = (
            projected_value - total_invested
        )

        return {
            "currency": currency,
            "years": years,
            "number_of_months": number_of_months,
            "monthly_contribution": round(
                monthly_contribution, 2
            ),
            "initial_balance": round(initial_balance, 2),
            "annual_return_percent": annual_return_percent,
            "monthly_rate_percent": round(
                monthly_rate * 100, 6
            ),
            "total_contributions": round(
                total_contributions, 2
            ),
            "total_invested": round(
                total_invested, 2
            ),
            "contribution_future_value": round(
                contribution_future_value, 2
            ),
            "initial_balance_future_value": round(
                initial_balance_future_value, 2
            ),
            "projected_value": round(
                projected_value, 2
            ),
            "illustrative_growth": round(
                illustrative_growth, 2
            )
        }


# ---------------------------------------------------------
# 2. Financial Analysis Agent
# ---------------------------------------------------------

class FinancialAnalysisAgent:

    def __init__(
        self,
        calculator: Optional[FinancialCalculator] = None
    ):

        self.calculator = (
            calculator
            if calculator is not None
            else FinancialCalculator()
        )

    def analyze(self, state: InvestmentState) -> dict:
        """
        Execute a calculation using validated financial inputs.

        This agent does not extract numbers from free text.
        """

        query_analysis = state.get("query_analysis", {})

        # Check whether calculation is required.
        if not query_analysis.get("requires_calculation", False):

            return {
                "financial_analysis": {
                    "status": "not_required"
                },
                "audit_events": [
                    "Financial calculation skipped: not required."
                ]
            }

        financial_inputs = state.get("financial_inputs")

        if not financial_inputs:

            return {
                "financial_analysis": {
                    "status": "awaiting_inputs"
                },
                "audit_events": [
                    "Financial calculation requires validated inputs."
                ]
            }

        calculation_type = financial_inputs.get(
            "calculation_type"
        )

        # Supported calculation.
        if calculation_type != "pension_projection":

            return {
                "financial_analysis": {
                    "status": "unsupported_calculation"
                },
                "audit_events": [
                    "Unsupported financial calculation requested."
                ]
            }

        try:

            result = self.calculator.calculate_pension_projection(
                monthly_contribution=financial_inputs[
                    "monthly_contribution"
                ],
                initial_balance=financial_inputs.get(
                    "initial_balance", 0.0
                ),
                annual_return_percent=financial_inputs[
                    "annual_return_percent"
                ],
                years=financial_inputs["years"],
                currency=financial_inputs.get(
                    "currency", "GBP"
                )
            )

        except (ValueError, KeyError) as exc:

            return {
                "financial_analysis": {
                    "status": "invalid_inputs",
                    "error": str(exc)
                },
                "audit_events": [
                    "Financial calculation stopped: invalid inputs."
                ]
            }

        assumptions = [
            "Illustrative calculation using a constant assumed annual return.",
            "Monthly contributions are made at the end of each month.",
            "The annual return is converted to an effective monthly rate.",
            "Fees, taxes and inflation are excluded.",
            "Actual investment returns can be positive or negative.",
            "This result is not a forecast, guarantee or personal recommendation."
        ]

        return {
            "financial_analysis": {
                "status": "completed",
                "calculation_type": calculation_type,
                "input_values": financial_inputs,
                "output_values": result,
                "assumptions": assumptions
            },
            "audit_events": [
                "Illustrative pension projection calculated successfully."
            ]
        }


# ---------------------------------------------------------
# 3. LangGraph node
# ---------------------------------------------------------

_financial_analysis_agent: Optional[
    FinancialAnalysisAgent
] = None


def configure_financial_analysis_agent(
    agent: FinancialAnalysisAgent
) -> None:

    global _financial_analysis_agent
    _financial_analysis_agent = agent


def financial_analysis_node(
    state: InvestmentState
) -> dict:
    """
    LangGraph entry point.
    """

    if _financial_analysis_agent is None:
        raise RuntimeError(
            "FinancialAnalysisAgent is not configured."
        )

    return _financial_analysis_agent.analyze(state)
