class Assessment:
    def __init__(self, id: int, title: str, questions: list):
        self.id = id
        self.title = title
        self.questions = questions

    def add_question(self, question: str):
        self.questions.append(question)

    def remove_question(self, question: str):
        self.questions.remove(question)

    def get_questions(self):
        return self.questions