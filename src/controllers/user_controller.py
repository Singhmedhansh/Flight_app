from ..models.account import Account
from ..config.database_config import get_db_connection  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash

class UserController:
    def __init__(self):
        self.current_user = None

    def signup(self, username, password, email):
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Account (username, password, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email)
        )
        conn.commit()
        cursor.close()
        conn.close()

    def login(self, username, password):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Account WHERE username=%s", (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and check_password_hash(row['password'], password):
            self.current_user = Account(**row)
            return self.current_user
        return None