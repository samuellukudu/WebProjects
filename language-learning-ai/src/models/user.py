class User:
    def __init__(self, id: int, username: str, password: str):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}')"