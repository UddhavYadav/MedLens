from db import get_connection

def hash_exists(patient_id: str, file_hash: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM patient_documents WHERE patient_id = %s AND file_hash = %s",
        (patient_id, file_hash)
    )

    exists = cur.fetchone() is not None

    cur.close()
    conn.close()

    return exists


def save_document(patient_id: str, file_name: str, file_hash: str, file_path: str, file_size: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO patient_documents (patient_id, file_name, file_hash, file_path, file_size)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, file_name, file_hash, file_path, file_size))

    conn.commit()
    cur.close()
    conn.close()