class Account:
    def __init__(self, id, username, password, email, role='user', status='active'):
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.status = status