from db import get_connection
import hashlib
import secrets

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_doctor(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO doctors (username, password_hash) VALUES (%s, %s)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def login_doctor(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM doctors WHERE username=%s AND password_hash=%s",
        (username, hash_password(password))
    )
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists