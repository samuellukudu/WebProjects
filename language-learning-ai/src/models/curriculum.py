class Curriculum:
    def __init__(self, id: int, title: str, content: str):
        self.id = id
        self.title = title
        self.content = content

    def __repr__(self):
        return f"<Curriculum(id={self.id}, title='{self.title}')>"