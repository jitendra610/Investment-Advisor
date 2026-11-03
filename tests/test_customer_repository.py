
from app.agents.customer_context import (
    PostgresCustomerContextRepository
)


repository = PostgresCustomerContextRepository()

customer = repository.get_customer("C1001")

if customer:
    print("Customer found!")
    print(customer)
else:
    print("Customer not found.")
