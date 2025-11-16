# Minimal stub of mysql.connector.connect to allow running the app for UI testing without installing MySQL client.
# This intentionally raises an informative error when connect() is called.

def connect(*args, **kwargs):
    raise RuntimeError("mysql.connector is not installed. For full DB functionality, install mysql-connector-python.")

# Provide a simple Cursor placeholder if code inspects attributes (optional)
class Error(Exception):
    pass
