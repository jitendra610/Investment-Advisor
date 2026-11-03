import psycopg

def check_pgvector():

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="postgres"
        ) as conn:

            with conn.cursor() as cur:

                cur.execute("SELECT version();")
                print("PostgreSQL version:")
                print(cur.fetchone()[0])

                cur.execute("""
                    SELECT extname
                    FROM pg_extension
                    WHERE extname = 'vector';
                """)

                result = cur.fetchone()

                if result:
                    print("\nSUCCESS: pgvector extension is available.")
                else:
                    print("\npgvector extension is NOT enabled.")

    except Exception as e:
        print("Database connection failed:", e)


if __name__ == "__main__":
    check_pgvector()