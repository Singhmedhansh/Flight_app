import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

class Role:
    def __init__(self, name: str, permissions: list):
        """Role class to define user roles and their associated permissions."""
        self.name = name
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if the role has a specific permission."""
        return permission in self.permissions

    def __repr__(self):
        return f"Role(name='{self.name}', permissions={self.permissions})"

class Account:
    def __init__(self, username: str, password: str, roles: list = None, account_id: int = None, status: str = "active"):
        """Account class representing a user with basic credentials."""
        self.username = username
        self.password = password  # This should always be a hashed password!
        self.roles = roles if roles else []
        self.account_id = account_id
        self._status = status

    def authenticate(self, password: str) -> bool:
        """Check if the given password matches the stored (hashed) password."""
        return check_password_hash(self.password, password)

    def has_role(self, role: str) -> bool:
        """Check if the account has a specific role."""
        return role in self.roles

    def reset_password(self, new_password: str):
        """Reset the account password (hash before storing)."""
        self.password = generate_password_hash(new_password)
        print(f"Password for {self.username} has been reset.")

    def __repr__(self):
        return f"Account(username='{self.username}', roles={self.roles}, status='{self._status}')"

    def _is_admin(self):
        return "admin" in self.roles

class CLIAuthenticator:
    def __init__(self):
        """CLIAuthenticator for handling user login and registration."""
        self.conn = mysql.connector.connect(
            host="localhost",
            user="educative",
            password="BMWfav3$",
            database="flight"
        )
        self.cursor = self.conn.cursor()

    def register(self, account: Account) -> bool:
        """Register a new account and assign a role."""
        # Check if the username already exists in the database
        query = "SELECT username FROM account WHERE username = %s"
        self.cursor.execute(query, (account.username,))
        result = self.cursor.fetchone()

        if result:
            return False  # Username already exists

        # Insert new account into the Account table with hashed password
        hashed_password = generate_password_hash(account.password)
        insert_query = """
        INSERT INTO account (account_id, username, password, status)
        VALUES (null, %s, %s, %s)
        """
        self.cursor.execute(insert_query, (account.username, hashed_password, account._status))
        account_id = self.cursor.lastrowid

        # Dynamically fetch the role_id for 'user'
        self.cursor.execute("SELECT role_id FROM role WHERE name = %s", ('user',))
        role_row = self.cursor.fetchone()
        if role_row:
            role_id = role_row[0]
        else:
            # If 'user' role doesn't exist, create it
            self.cursor.execute("INSERT INTO role (name) VALUES (%s)", ('user',))
            role_id = self.cursor.lastrowid

        # Insert account-role relationship into the account_role table
        account_role_query = "INSERT INTO account_role (account_id, role_id) VALUES (%s, %s)"
        self.cursor.execute(account_role_query, (account_id, role_id))
        self.conn.commit()
        return True

    def authenticate(self, username: str, password: str) -> Account:
        """Attempt to authenticate a user by their username and password, and fetch roles."""
        # Query the database for the account
        query = "SELECT account_id, username, password, status FROM account WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()

        if result and check_password_hash(result[2], password):  # Secure password check
            account_id = result[0]
            # Fetch roles for the user
            role_query = """
            SELECT role.name FROM role
            JOIN account_role ON role.role_id = account_role.role_id
            WHERE account_role.account_id = %s
            """
            self.cursor.execute(role_query, (account_id,))
            roles = [role_row[0] for role_row in self.cursor.fetchall()]

            return Account(
                username=result[1],
                password=result[2],  # hashed password
                account_id=account_id,
                status=result[3],
                roles=roles
            )
        return None

    def close(self):
        """Close the database connection."""
        if self.conn.is_connected():
            self.conn.close()