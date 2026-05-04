import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os 

def get_connection():
    load_dotenv(override=True)
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password=os.getenv('db_pass'),#"Poer@#1499",
        port="5432"
    )


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_documents (
        id SERIAL PRIMARY KEY,
        patient_id VARCHAR(100) NOT NULL,
        file_name TEXT NOT NULL,
        file_hash VARCHAR(64) NOT NULL,
        file_path TEXT NOT NULL,
        file_size BIGINT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (patient_id, file_hash)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()