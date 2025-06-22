import psycopg2
import os

DB_NAME = os.getenv("POSTGRES_DB", "autonova_db")
DB_USER = os.getenv("POSTGRES_USER", "autonova_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "autonova_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database at {DB_HOST}:{DB_PORT}. Is the Docker container running?")
        print(f"Details: {e}")
        return None

def initialize_database():
    conn = get_db_connection()
    if conn is None:
        print("Database initialization failed because a connection could not be established.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    original_task TEXT NOT NULL,
                    sub_tasks JSONB,
                    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'EXECUTING', 'SUCCESS', 'FAILED'))
                );
            """)
            conn.commit()
            print("Database initialized successfully. The 'tasks' table is ready.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Attempting to initialize the database schema...")
    initialize_database()