
import psycopg


def get_connection():
    return psycopg.connect(
        host="localhost",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="postgres"
    )


def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    customer_id VARCHAR(50) PRIMARY KEY,
                    age_band VARCHAR(20) NOT NULL,
                    pension_type VARCHAR(50) NOT NULL,
                    monthly_contribution FLOAT NOT NULL,
                    currency VARCHAR(3) NOT NULL DEFAULT 'GBP',
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    print("Customer profiles table is ready.")


def insert_customer(
    customer_id,
    age_band,
    pension_type,
    monthly_contribution,
    currency="GBP"
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO customer_profiles (
                    customer_id,
                    age_band,
                    pension_type,
                    monthly_contribution,
                    currency
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id)
                DO UPDATE SET
                    age_band = EXCLUDED.age_band,
                    pension_type = EXCLUDED.pension_type,
                    monthly_contribution = EXCLUDED.monthly_contribution,
                    currency = EXCLUDED.currency,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING customer_id;
            """, (
                customer_id,
                age_band,
                pension_type,
                monthly_contribution,
                currency
            ))

            print("Inserted/Updated Customer:", cur.fetchone()[0])


def get_all_customers():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    customer_id,
                    age_band,
                    pension_type,
                    monthly_contribution,
                    currency,
                    updated_at
                FROM customer_profiles
                ORDER BY customer_id;
            """)

            customers = cur.fetchall()

            for customer in customers:
                print(customer)

            return customers


if __name__ == "__main__":

    # 1. Create customer table
    create_table()

    # 2. Insert sample customers
    insert_customer(
        "C1001", "30-40", "Workplace Pension", 500
    )

    insert_customer(
        "C1002", "40-50", "Personal Pension", 750
    )

    insert_customer(
        "C1003", "50-60", "Workplace Pension", 600
    )

    # 3. Display all customers
    print("\nAll Customers:")
    get_all_customers()
